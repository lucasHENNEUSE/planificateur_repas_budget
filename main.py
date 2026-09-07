# main.py

import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
import google.generativeai as genai
import ollama

# Importation de l'interface de base de données séparée pour maintenir l'architecture n-tiers
from database import menus_collection

# Initialisation de l'application FastAPI et configuration du répertoire contenant les vues HTML
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# CONFIGURATION DES API ET MODÈLES

# Configuration de l'API Google Gemini pour la recherche géographique de magasins via les variables d'environnement
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# Définition du modèle d'intelligence artificielle local utilisé pour la génération culinaire
LOCAL_AI_MODEL = 'llama3'

# ROUTES DE L'APPLICATION

# Route interceptant la requête automatique du navigateur pour l'icône afin d'éviter les erreurs 404 dans les journaux
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# Route principale exposant l'interface utilisateur
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# Route permettant de rechercher les supermarchés existants dans une zone géographique ciblée
@app.post("/api/get-stores")
async def get_stores(data: dict):
    # Extraction et nettoyage du nom de la ville transmis dans la requête
    city = data.get("city", "").strip()
    if not city:
        return {"status": "error", "stores": []}
    
    # Consigne stricte définissant le comportement attendu de l'IA pour la recherche de magasins
    prompt = f"""
    Trouve 5 véritables grands supermarchés ou hypermarchés existant réellement dans la ville de {city}, France.
    Renvoie STRICTEMENT un tableau JSON contenant des objets avec les clés 'nom' et 'adresse'. N'ajoute aucun autre champ.
    """
    
    try:
        # Appel à l'API Gemini en forçant nativement le format de réponse en JSON pour garantir l'intégrité de la structure
        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        
        # Désérialisation directe de la réponse JSON garantie par la configuration de l'API
        stores = json.loads(response.text)
        return {"status": "success", "stores": stores}
        
    except Exception as e:
        # Traçabilité des erreurs d'API dans la console du serveur
        print(f"Erreur API Gemini : {str(e)}")
        return {"status": "error", "stores": [], "details": f"Erreur de traitement Gemini : {str(e)}"}

# Route générant l'ossature du menu hebdomadaire via le modèle local
@app.post("/api/generate-menus")
async def generate_menus(data: dict):
    # Récupération des paramètres de configuration du repas
    budget = data.get("budget")
    adults = int(data.get("adults", 2))
    children = int(data.get("children", 0))
    store_name = data.get("store_name")
    
    # Calcul de la jauge totale de convives pour calibrer les futures portions
    total_people = adults + children
    
    prompt = f"""Tu es un planificateur de repas expert et strict. Génère un menu varié pour 7 jours pour {total_people} personnes. 
Budget maximum strict : {budget} euros par personne. Magasin de référence : {store_name}.
Propose de vrais plats traditionnels. Donne uniquement le nom exact du plat et le prix estimé par personne.
Ne mets aucun texte avant ou après le JSON.

Réponds STRICTEMENT sous format JSON valide avec cette structure exacte :
{{
  "Lundi": [
    {{"option": 1, "nom": "Poulet rôti aux pommes de terre", "prix_par_personne": 3.5}},
    {{"option": 2, "nom": "Gratin de courgettes", "prix_par_personne": 2.5}}
  ],
  "Mardi": [
    {{"option": 1, "nom": "Spaghettis à la bolognaise", "prix_par_personne": 2.0}},
    {{"option": 2, "nom": "Filet de poisson et riz", "prix_par_personne": 3.8}}
  ]
}}"""

    # Mécanisme de tolérance aux pannes : 3 tentatives pour pallier aux erreurs de formatage JSON de l'IA locale
    for _ in range(3):
        try:
            response = ollama.chat(model=LOCAL_AI_MODEL, messages=[{'role': 'user', 'content': prompt}])
            content = response['message']['content'].strip()
            
            if content.startswith("```json"): 
                content = content[7:-3].strip()
            elif content.startswith("```"): 
                content = content[3:-3].strip()
                
            return {"status": "success", "menus": json.loads(content)}
        except json.JSONDecodeError:
            continue
            
    return {"status": "error", "details": "Erreur de sérialisation JSON générée par le modèle d'intelligence artificielle."}

# Route détaillant les instructions de préparation et verrouillant le coût du plat
@app.post("/api/get-recipe")
async def get_recipe(data: dict):
    meal_name = data.get("meal_name")
    adults = int(data.get("adults", 2))
    children = int(data.get("children", 0))
    total_people = adults + children
    
    # Récupération du prix préalablement validé lors de la génération du menu pour assurer la cohérence des données
    prix_unitaire_verrouille = float(data.get("prix_par_personne", 0))
    
    prompt = f"""Tu es un grand chef cuisinier français, expert en gastronomie traditionnelle.
Rédige la vraie recette pour ce plat : "{meal_name}".
La recette doit nourrir exactement {total_people} personnes.

Règles impératives :
1. Liste uniquement les vrais ingrédients nécessaires pour ce plat. 
2. Donne les quantités exactes pour {total_people} personnes.
3. Rédige des étapes de préparation claires, logiques et professionnelles.
4. Ne génère aucun prix, aucune introduction, aucune conclusion.

Réponds STRICTEMENT sous format JSON valide :
{{
  "ingredients": ["1 kg de poulet", "800g de pommes de terre", "Huile d'olive", "Sel et poivre"],
  "etapes": ["Préchauffer le four à 200 degrés.", "Placer le poulet dans un plat et enfourner 1h.", "Couper les pommes de terre et les ajouter à mi-cuisson."]
}}"""

    for _ in range(3):
        try:
            response = ollama.chat(model=LOCAL_AI_MODEL, messages=[{'role': 'user', 'content': prompt}])
            content = response['message']['content'].strip()
            
            if content.startswith("```json"): 
                content = content[7:-3].strip()
            elif content.startswith("```"): 
                content = content[3:-3].strip()
                
            recipe_data = json.loads(content)
            
            # Injection des données tarifaires sécurisées et exécution du calcul de coût total côté serveur
            recipe_data["prix_par_personne"] = round(prix_unitaire_verrouille, 2)
            recipe_data["prix_total"] = round(prix_unitaire_verrouille * total_people, 2)
            
            return {"status": "success", "recipe": recipe_data}
        except json.JSONDecodeError:
            continue
            
    return {"status": "error", "details": "Échec de l'élaboration de la recette par le modèle."}

# Route permettant la modification contextuelle d'une recette selon les instructions de l'utilisateur
@app.post("/api/modify-recipe")
async def modify_recipe(data: dict):
    meal_name = data.get("meal_name")
    feedback = data.get("feedback")
    adults = int(data.get("adults", 2))
    children = int(data.get("children", 0))
    total_people = adults + children
    
    # Récupération du prix actuel pour définir la base de calcul de la modification
    prix_unitaire_actuel = float(data.get("prix_par_personne", 0))
    
    prompt = f"""Le plat actuel est : "{meal_name}".
L'utilisateur demande cette modification : "{feedback}".
Adapte la recette pour {total_people} personnes.
Le prix actuel était de {prix_unitaire_actuel} euros par personne. Ajuste légèrement ce prix par personne à la hausse ou à la baisse selon le coût des nouveaux ingrédients ajoutés ou retirés.

Réponds STRICTEMENT sous format JSON valide :
{{
  "nom": "Nouveau nom du plat",
  "ingredients": ["Ingrédient adapté 1", "Ingrédient 2"],
  "etapes": ["Etape de préparation adaptée 1"],
  "nouveau_prix_par_personne": 2.5
}}"""

    for _ in range(3):
        try:
            response = ollama.chat(model=LOCAL_AI_MODEL, messages=[{'role': 'user', 'content': prompt}])
            content = response['message']['content'].strip()
            
            if content.startswith("```json"): 
                content = content[7:-3].strip()
            elif content.startswith("```"): 
                content = content[3:-3].strip()
                
            recipe_data = json.loads(content)
            
            # Extraction du nouveau prix unitaire estimé et recalcul du coût global par le backend
            nouveau_prix_pp = float(recipe_data.get("nouveau_prix_par_personne", prix_unitaire_actuel))
            recipe_data["prix_par_personne"] = round(nouveau_prix_pp, 2)
            recipe_data["prix_total"] = round(nouveau_prix_pp * total_people, 2)
            
            return {"status": "success", "recipe": recipe_data}
        except json.JSONDecodeError:
            continue
            
    return {"status": "error", "details": "Erreur lors de l'altération de la recette existante."}

# Point d'entrée pour l'exécution du serveur ASGI
if __name__ == "__main__":
    import uvicorn
    # Lancement du serveur uvicorn avec rechargement à chaud pour le développement
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)