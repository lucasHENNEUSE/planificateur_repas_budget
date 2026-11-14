"""
test_routes.py : tests des routes de l'API (carte #15, C12).

Principe : on appelle chaque route comme le ferait le navigateur,
mais la base de données et Gemini sont remplacés par de fausses réponses
(@patch). Les tests sont donc rapides, gratuits et sans internet.
"""
from datetime import timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from api.auth_service import create_access_token, get_password_hash, verify_password

client = TestClient(app)


def entetes(duree=timedelta(hours=2)):
    # Fabrique l'en-tête d'un utilisateur connecté (jeton valable 2 h par défaut)
    jeton = create_access_token({"sub": "test@ecofrigo.fr"}, duree)
    return {"Authorization": f"Bearer {jeton}"}


# ---------- Mots de passe et jetons ----------

def test_mot_de_passe_hache():
    # Le mot de passe est transformé en empreinte, et seule la bonne valeur la valide
    empreinte = get_password_hash("secret123")
    assert empreinte != "secret123"
    assert verify_password("secret123", empreinte)
    assert not verify_password("autre", empreinte)


def test_jeton_invalide_refuse():
    # Un faux jeton est refusé (erreur 401)
    reponse = client.post("/api/get-stores", json={"city": "Brest"},
                          headers={"Authorization": "Bearer faux"})
    assert reponse.status_code == 401


def test_jeton_expire_refuse():
    # Un jeton déjà expiré est refusé avec un message pour se reconnecter
    reponse = client.post("/api/get-stores", json={"city": "Brest"},
                          headers=entetes(timedelta(seconds=-1)))
    assert reponse.status_code == 401
    assert "expiré" in reponse.json()["detail"]


# ---------- Inscription ----------

@patch("api.api_routes.users_collection")
def test_inscription_reussie(base):
    # Nouveau compte : l'email est nettoyé et le mot de passe n'est jamais stocké en clair
    base.find_one.return_value = None
    reponse = client.post("/api/register", json={"email": " Test@Ecofrigo.fr ", "password": "secret123"})
    compte = base.insert_one.call_args[0][0]
    assert reponse.json()["status"] == "success"
    assert compte["email"] == "test@ecofrigo.fr"
    assert compte["password"] != "secret123"


@patch("api.api_routes.users_collection")
def test_inscription_mot_de_passe_trop_court(base):
    # Moins de 6 caractères : refusé, rien n'est enregistré
    reponse = client.post("/api/register", json={"email": "a@b.fr", "password": "123"})
    assert reponse.json()["status"] == "error"
    base.insert_one.assert_not_called()


@patch("api.api_routes.users_collection")
def test_inscription_compte_existant(base):
    # Email déjà utilisé : refusé, rien n'est enregistré
    base.find_one.return_value = {"email": "a@b.fr"}
    reponse = client.post("/api/register", json={"email": "a@b.fr", "password": "secret123"})
    assert reponse.json()["status"] == "error"
    base.insert_one.assert_not_called()


# ---------- Connexion ----------

@patch("api.api_routes.users_collection")
def test_connexion_reussie(base):
    # Bon mot de passe : on reçoit un jeton
    base.find_one.return_value = {"email": "a@b.fr", "password": get_password_hash("secret123")}
    reponse = client.post("/api/login", json={"email": "a@b.fr", "password": "secret123"})
    assert reponse.json()["status"] == "success"
    assert reponse.json()["token"]


@patch("api.api_routes.users_collection")
def test_connexion_mauvais_mot_de_passe(base):
    # Mauvais mot de passe : erreur et aucun jeton
    base.find_one.return_value = {"email": "a@b.fr", "password": get_password_hash("secret123")}
    reponse = client.post("/api/login", json={"email": "a@b.fr", "password": "faux"})
    assert reponse.json()["status"] == "error"
    assert "token" not in reponse.json()


# ---------- Magasins ----------

def test_magasins_ville_vide():
    # Ville vide : erreur et liste vide
    reponse = client.post("/api/get-stores", json={"city": "  "}, headers=entetes())
    assert reponse.json() == {"status": "error", "stores": []}


@patch("api.api_routes.obtenir_magasins_depuis_llm")
@patch("api.api_routes.menus_collection")
def test_magasins_depuis_le_cache(base, ia):
    # Ville déjà recherchée : on répond depuis la base, sans appeler Gemini
    base.find_one.return_value = {"stores": [{"nom": "E.Leclerc", "adresse": "Brest"}]}
    reponse = client.post("/api/get-stores", json={"city": "Brest"}, headers=entetes())
    assert reponse.json()["stores"][0]["nom"] == "E.Leclerc"
    ia.assert_not_called()


@patch("api.api_routes.obtenir_magasins_depuis_llm", return_value=None)
@patch("api.api_routes.menus_collection")
def test_magasins_solution_de_secours(base, ia):
    # Gemini ne répond pas : on propose quand même Leclerc et Carrefour
    base.find_one.return_value = None
    reponse = client.post("/api/get-stores", json={"city": "Brest"}, headers=entetes())
    noms = [magasin["nom"] for magasin in reponse.json()["stores"]]
    assert noms == ["E.Leclerc", "Carrefour"]


# ---------- Génération des menus ----------

DEMANDE_MENUS = {"store_name": "Carrefour", "budget": 20, "adults": 2, "children": 0}


@patch("api.api_routes.enregistrer_alerte_securite")
@patch("api.api_routes.monitorer_ia_mlflow")
@patch("api.api_routes.generer_menu_rag", side_effect=RuntimeError("Gemini n'a pas répondu"))
@patch("api.api_routes.count_products", return_value=100)
def test_generation_echec(produits, rag, mlflow, alerte):
    # Le moteur échoue : message d'erreur, échec suivi dans MLflow, alerte écrite dans le journal
    reponse = client.post("/api/generate-menus", headers=entetes(), json=DEMANDE_MENUS)
    assert reponse.json()["status"] == "error"
    assert "Gemini n'a pas répondu" in reponse.json()["message"]
    assert mlflow.call_args.kwargs["succes"] is False


@patch("api.api_routes.monitorer_ia_mlflow")
@patch("api.api_routes.enregistrer_alerte_securite")
@patch("api.api_routes.generer_menu_rag", return_value={"Lundi": []})
@patch("api.api_routes.charger_catalogue")
@patch("api.api_routes.count_products", return_value=10)
def test_generation_charge_le_catalogue(produits, charger, rag, alerte, mlflow):
    # Moins de 50 produits en base : on charge le catalogue avant de générer
    client.post("/api/generate-menus", headers=entetes(), json=DEMANDE_MENUS)
    charger.assert_called_once()


# ---------- Recettes ----------

DEMANDE_RECETTE = {"meal_name": "Poulet riz", "prix_par_personne": 2.5, "adults": 2, "children": 1}


@patch("api.api_routes.rediger_recette_depuis_llm", return_value={"nom": "Poulet riz", "etapes": ["Cuire"]})
@patch("api.api_routes.menus_collection")
def test_recette_nouvelle(base, ia):
    # Recette inconnue : Gemini la rédige, le code calcule le prix total et la met en cache
    base.find_one.return_value = None
    reponse = client.post("/api/get-recipe", json=DEMANDE_RECETTE, headers=entetes())
    assert reponse.json()["status"] == "success"
    assert reponse.json()["recipe"]["prix_total"] == 7.5       # 2,50 € x 3 personnes
    base.update_one.assert_called_once()


@patch("api.api_routes.rediger_recette_depuis_llm")
@patch("api.api_routes.menus_collection")
def test_recette_depuis_le_cache(base, ia):
    # Recette déjà en cache : Gemini n'est pas appelé
    base.find_one.return_value = {"recipe": {"nom": "Poulet riz", "etapes": ["Cuire"]}}
    reponse = client.post("/api/get-recipe", json=DEMANDE_RECETTE, headers=entetes())
    assert reponse.json()["status"] == "success"
    ia.assert_not_called()


@patch("api.api_routes.rediger_recette_depuis_llm", return_value=None)
@patch("api.api_routes.menus_collection")
def test_recette_echec_ia(base, ia):
    # Gemini échoue : message d'erreur, et surtout rien n'est mis en cache
    base.find_one.return_value = None
    reponse = client.post("/api/get-recipe", json=DEMANDE_RECETTE, headers=entetes())
    assert reponse.json()["status"] == "error"
    base.update_one.assert_not_called()


def test_modification_recette():
    # Route actuellement simplifiée : elle renvoie la recette marquée « Modifié »
    reponse = client.post("/api/modify-recipe", headers=entetes(), json={**DEMANDE_RECETTE, "feedback": "sans sel"})
    assert reponse.json()["recipe"]["nom"] == "Poulet riz (Modifié)"

    # pytest -m pytest -v