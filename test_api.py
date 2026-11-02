"""
test_api.py : tests automatisés (Pytest) avec injection de dépendances (Mocks).
Objectif : Valider les règles de sécurité (OWASP) et la logique métier sans solliciter les services externes.
Correspondance Référentiel : Blocs C12 (Mocks/Fixtures) et C18 (Automatisation des tests).
"""
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app
from api.auth_service import create_access_token

# Initialisation du client de test natif de FastAPI.
# Permet de simuler des requêtes HTTP entrantes vers l'application sans nécessiter le démarrage d'un serveur uvicorn réel.
client = TestClient(app)

def test_securite_bloquee():
    """
    Test d'intégration : Vérification du middleware d'authentification.
    S'assure qu'une requête POST dépourvue d'en-tête d'autorisation (Token JWT) 
    est formellement rejetée par la route protégée.
    """
    reponse = client.post("/api/generate-menus", json={
        "store_name": "E.Leclerc", "budget": 5, "adults": 2, "children": 0
    })
    
    # L'assertion valide que le code statut HTTP retourné est 401 (Unauthorized) ou 403 (Forbidden).
    assert reponse.status_code in [401, 403]

def test_recherche_magasin():
    """
    Test d'intégration : Vérification de l'accès aux ressources non protégées.
    Valide que le point de terminaison public répond correctement et interagit 
    avec le système de cache ou la logique de base de données.
    """
    reponse = client.post("/api/get-stores", json={"city": "Brest"})
    donnees = reponse.json()
    
    # Validation du contrat de données (contrôle du statut et de la présence d'au moins un élément).
    assert donnees["status"] == "success"
    assert len(donnees["stores"]) > 0

# Le décorateur @patch cible le chemin d'importation exact de la fonction à intercepter au sein du contrôleur cible (api_routes.py).
@patch("api.api_routes.generer_menu_rag")
def test_generation_menu_avec_mock(mock_rag):
    """
    Test unitaire isolé : Validation du contrôleur avec Mock du service LLM (C12).
    Simule le comportement du moteur d'intelligence artificielle pour tester la capacité 
    de l'API à formater et renvoyer une réponse complexe, sans dépendance externe.
    """
    # 1. Configuration du Mock (Fixture statique) : Définit la réponse simulée que la fonction interceptée doit renvoyer.
    mock_rag.return_value = {
        "Lundi": [{"nom": "Plat de test simulé", "prix_par_personne": 2.5}]
    }

    # 2. Injection de contexte de sécurité : Génération d'un JWT valide signé avec le secret local 
    # pour passer le middleware d'authentification durant le test.
    faux_token = create_access_token({"sub": "systeme_de_test@interne.fr"})
    
    # 3. Exécution de la requête avec injection du token dans l'en-tête HTTP standard 'Authorization'.
    reponse = client.post(
        "/api/generate-menus", 
        json={"store_name": "Carrefour", "budget": 4, "adults": 2, "children": 0},
        headers={"Authorization": f"Bearer {faux_token}"}
    )
    
    donnees = reponse.json()
    
    # 4. Assertions métier : Vérification que l'API a correctement reçu, traité et encapsulé 
    # les données statiques fournies par le Mock sans altération.
    assert donnees["status"] == "success"
    assert "Lundi" in donnees["menus"]
    assert donnees["menus"]["Lundi"][0]["nom"] == "Plat de test simulé"
    
    # 5. Validation comportementale : S'assure que la fonction externe ciblée a bien été invoquée 
    # exactement une fois par le contrôleur lors de la requête.
    mock_rag.assert_called_once()