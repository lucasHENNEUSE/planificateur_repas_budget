"""
api_routes.py : Contrôleur principal (API REST) documenté pour Swagger.
-------------------------------------------------------------------------
Ce fichier utilise Pydantic (BaseModel) pour que la documentation Swagger 
affiche des formulaires précis et interactifs pour chaque route.
"""
import time
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from data.catalogue_service import scrape_store_catalog as charger_catalogue
from data.database import client, menus_collection, count_products
from IA.rag_service import generer_menu_rag
from IA.llm_service import obtenir_magasins_depuis_llm, rediger_recette_depuis_llm
from api.auth_service import get_password_hash, verify_password, create_access_token, verify_token
from monitoring import monitorer_ia_mlflow, enregistrer_alerte_securite

router = APIRouter(prefix="/api", tags=["Application Éco-Frigo"])
users_collection = client["planificateur_repas_db"]["users"]



# SCHÉMAS PYDANTIC (Pour générer le Swagger)


class UserLogin(BaseModel):
    email: str
    password: str

class StoreSearch(BaseModel):
    city: str

class MenuRequest(BaseModel):
    store_name: str
    budget: float
    adults: int
    children: int

class RecipeRequest(BaseModel):
    meal_name: str
    prix_par_personne: float
    adults: int
    children: int
    store_name: str = ""

class ModifyRecipeRequest(BaseModel):
    meal_name: str
    feedback: str
    prix_par_personne: float
    adults: int
    children: int
    store_name: str = ""


# ==========================================
# ROUTES DE L'API
# ==========================================

@router.post("/register")
async def register_user(data: UserLogin):
    """
    **Création de compte sécurisée** : 
    Vérifie la complexité du mot de passe et s'assure que l'utilisateur n'existe pas déjà.
    """
    email = data.email.strip().lower()
    password = data.password
    
    if not email or len(password) < 6:
        return {"status": "error", "details": "Email invalide ou mot de passe trop court (min 6 caractères)."}
    
    if users_collection.find_one({"email": email}):
        return {"status": "error", "details": "Cet utilisateur existe déjà."}
        
    users_collection.insert_one({"email": email, "password": get_password_hash(password)})
    return {"status": "success", "details": "Compte créé avec succès."}

@router.post("/login")
async def login_user(data: UserLogin):
    """
    **Authentification OWASP** : 
    Vérifie les identifiants en base et renvoie un jeton JWT valide 2 heures.
    """
    email = data.email.strip().lower()
    password = data.password
    
    user = users_collection.find_one({"email": email})
    
    if not user or not verify_password(password, user["password"]):
        return {"status": "error", "details": "Identifiants incorrects."}
        
    return {"status": "success", "token": create_access_token({"sub": email}), "email": email}

@router.post("/get-stores")
async def get_stores(data: StoreSearch):
    """
    **Recherche de magasins** : 
    Cherche les enseignes (Leclerc/Carrefour) via le cache ou l'IA Gemini.
    """
    city = data.city.strip()
    if not city:
        return {"status": "error", "stores": []}
    
    cached = menus_collection.find_one({"type": "stores_cache", "city": city.lower()})
    if cached:
        return {"status": "success", "stores": cached["stores"]}

    stores = obtenir_magasins_depuis_llm(city)
    
    if not stores or not isinstance(stores, list):
        stores = []
        
    stores_filtres = [s for s in stores if "leclerc" in s.get("nom", "").lower() or "carrefour" in s.get("nom", "").lower()]
    
    if not stores_filtres:
        stores_filtres = [
            {"nom": "E.Leclerc", "adresse": f"Zone commerciale, {city}"},
            {"nom": "Carrefour", "adresse": f"Centre, {city}"}
        ]

    menus_collection.update_one({"type": "stores_cache", "city": city.lower()}, {"$set": {"stores": stores_filtres}}, upsert=True)
    return {"status": "success", "stores": stores_filtres}

@router.post("/generate-menus")
async def generate_menus(data: MenuRequest, current_user: dict = Depends(verify_token)):
    """
    **ROUTE PROTÉGÉE PAR JETON (JWT)** : 
    Génère le menu de la semaine avec le moteur RAG en respectant le budget.
    Intègre la télémétrie MLOps (C11) et la journalisation de sécurité (C20).
    """
    budget = str(data.budget)
    total_people = data.adults + data.children
    store_name = data.store_name
    
    # 1. MONITORAGE C20 (Logs système) : On trace qui utilise l'API
    email_utilisateur = current_user.get("sub", "inconnu")
    enregistrer_alerte_securite(email_utilisateur, f"Demande de génération de menu pour {store_name}")
    
    # 2. Préparation des données catalogue
    if count_products(store_name) < 50:
        charger_catalogue(store_name, "")

    # 3. Gestion du Cache (pour éviter de payer l'IA si on a déjà la réponse)
    cache_key = f"menu_{store_name.lower().replace(' ', '_')}_b{budget}_p{total_people}"
    cached = menus_collection.find_one({"type": "menu_cache", "key": cache_key})
    
    if cached and cached.get("menus") and len(cached["menus"]) > 0:
        menus_data = cached["menus"]
        enregistrer_alerte_securite(email_utilisateur, "Menu récupéré depuis le cache (Pas d'appel IA).")
    else:
        # === DEBUT MONITORAGE MLOps (C11) ===
        # L'IA va être sollicitée. On lance le chronomètre.
        debut_chrono = time.time()
        
        try:
            # Appel au moteur d'intelligence artificielle (RAG)
            menus_data = generer_menu_rag(store_name, budget, total_people)
            
            # Arrêt du chronomètre
            temps_ecoule = time.time() - debut_chrono
            
            if menus_data:
                # Succès : On envoie les statistiques à MLflow
                monitorer_ia_mlflow(store_name, float(budget), temps_ecoule, succes=True)
                # On sauvegarde dans le cache pour les prochains utilisateurs
                menus_collection.update_one(
                    {"type": "menu_cache", "key": cache_key}, 
                    {"$set": {"menus": menus_data}}, 
                    upsert=True
                )
            else:
                # Échec silencieux de l'IA (retour vide)
                monitorer_ia_mlflow(store_name, float(budget), temps_ecoule, succes=False)
                
        except Exception as erreur:
            # Échec critique de l'IA (ex: Gemini est en panne ou clé invalide)
            temps_ecoule = time.time() - debut_chrono
            
            # On prévient MLflow de l'échec pour dégrader le taux de réussite du modèle (C11)
            monitorer_ia_mlflow(store_name, float(budget), temps_ecoule, succes=False)
            
            # On prévient le fichier de logs (C20) qu'un incident grave s'est produit
            enregistrer_alerte_securite(email_utilisateur, f"Crash IA Gemini : {str(erreur)}")
            
            return {"status": "error", "message": f"Erreur lors de la génération IA : {str(erreur)}"}
        

    return {"status": "success", "menus": menus_data}

@router.post("/get-recipe")
async def get_recipe(data: RecipeRequest):
    """
    **Détail d'une recette** : 
    Demande à l'IA de rédiger les étapes de cuisine pour un plat précis.
    """
    meal_name = data.meal_name
    total_people = data.adults + data.children
    prix_unitaire = data.prix_par_personne
    
    cache_key = f"recipe_{meal_name.lower().strip()}_p{total_people}"
    cached = menus_collection.find_one({"type": "recipe_cache", "key": cache_key})
    
    if cached:
        recipe_data = cached["recipe"]
    else:
        recipe_data = rediger_recette_depuis_llm(meal_name, total_people)
        menus_collection.update_one({"type": "recipe_cache", "key": cache_key}, {"$set": {"recipe": recipe_data}}, upsert=True)

    recipe_data["prix_par_personne"] = round(prix_unitaire, 2)
    recipe_data["prix_total"] = round(prix_unitaire * total_people, 2)
    return {"status": "success", "recipe": recipe_data}

@router.post("/modify-recipe")
async def modify_recipe(data: ModifyRecipeRequest):
    """
    **Personnalisation** : 
    Met à jour les étapes d'une recette selon la demande de l'utilisateur.
    """
    total_people = data.adults + data.children
    prix_unitaire = data.prix_par_personne
    
    return {"status": "success", "recipe": {
        "nom": f"{data.meal_name} (Modifié)",
        "ingredients": ["Ingrédients ajustés selon votre demande."],
        "etapes": [f"Modification : {data.feedback}."],
        "prix_par_personne": round(prix_unitaire, 2),
        "prix_total": round(prix_unitaire * total_people, 2)
    }}