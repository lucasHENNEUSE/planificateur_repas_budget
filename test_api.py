"""
test_api.py : tests automatisés (Pytest) avec injection de dépendances (Mocks).
Objectif : Valider les règles de sécurité (OWASP) et la logique métier sans solliciter les services externes.
Correspondance Référentiel : Blocs C12 (Mocks/Fixtures) et C18 (Automatisation des tests).
"""
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app
from api.auth_service import create_access_token

client = TestClient(app)

def test_securite_bloquee():
    """Test 1 (OWASP) : Vérifier qu'un pirate est bloqué (Erreur 401/403)."""
    reponse = client.post("/api/generate-menus", json={
        "store_name": "E.Leclerc", "budget": 5, "adults": 2, "children": 0
    })
    assert reponse.status_code in [401, 403]

def test_get_stores_sans_jeton_bloque():
    """Test 2a (OWASP) : get-stores doit refuser une requête sans jeton."""
    reponse = client.post("/api/get-stores", json={"city": "Brest"})
    assert reponse.status_code in [401, 403]

def test_get_recipe_sans_jeton_bloque():
    """Test 2b (OWASP) : get-recipe doit refuser une requête sans jeton."""
    reponse = client.post("/api/get-recipe", json={
        "meal_name": "Poulet", "prix_par_personne": 2.5, "adults": 2, "children": 0
    })
    assert reponse.status_code in [401, 403]

def test_modify_recipe_sans_jeton_bloque():
    """Test 2c (OWASP) : modify-recipe doit refuser une requête sans jeton."""
    reponse = client.post("/api/modify-recipe", json={
        "meal_name": "Poulet", "feedback": "sans sel",
        "prix_par_personne": 2.5, "adults": 2, "children": 0
    })
    assert reponse.status_code in [401, 403]

# On intercepte l'appel à l'IA pour la recherche de magasins
@patch("api.api_routes.menus_collection")
@patch("api.api_routes.obtenir_magasins_depuis_llm")
def test_recherche_magasin(mock_llm, mock_coll):
    """
    Test 3 (C12) : recherche de magasins avec un jeton valide.
    L'IA et la base de données sont simulées pour isoler le test.
    """
    mock_coll.find_one.return_value = None  # pas de cache en base
    mock_llm.return_value = [{"nom": "E.Leclerc", "adresse": "Brest"}]

    token = create_access_token({"sub": "test@ecofrigo.fr"})
    reponse = client.post(
        "/api/get-stores",
        json={"city": "Brest"},
        headers={"Authorization": f"Bearer {token}"}
    )
    donnees = reponse.json()

    assert donnees["status"] == "success"
    assert len(donnees["stores"]) > 0

# On intercepte l'appel à l'IA pour la génération de menus
@patch("api.api_routes.generer_menu_rag")
def test_generation_menu_avec_mock(mock_rag):
    """
    Test 4 (C12) : Simule l'IA pour tester le moteur RAG sans dépendance externe.
    """
    mock_rag.return_value = {
        "Lundi": [{"nom": "Plat de test simulé", "prix_par_personne": 2.5}]
    }
    
    faux_token = create_access_token({"sub": "test@ecofrigo.fr"})
    reponse = client.post(
        "/api/generate-menus", 
        json={"store_name": "Carrefour", "budget": 4, "adults": 2, "children": 0},
        headers={"Authorization": f"Bearer {faux_token}"}
    )
    
    donnees = reponse.json()
    assert donnees["status"] == "success"
    assert "Lundi" in donnees["menus"]
    assert donnees["menus"]["Lundi"][0]["nom"] == "Plat de test simulé"
    mock_rag.assert_called_once()