"""
monitorage.py : Service hybride de sécurité API (C20) et Monitorage MLOps (C11).
"""
import logging
import os
import mlflow

# --- 1. SÉCURITÉ DE L'APPLICATION (C20) ---
DOSSIER_LOGS = "logs"
os.makedirs(DOSSIER_LOGS, exist_ok=True)

logging.basicConfig(
    filename=f"{DOSSIER_LOGS}/api_eco_frigo.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

def enregistrer_alerte_securite(cible: str, type_attaque: str):
    """Journalise les tentatives de piratage ou les erreurs de mot de passe."""
    message = f"ALERTE SÉCURITÉ | Cible : {cible} | Motif : {type_attaque}"
    logging.warning(message)
    print(f"attention {message}")


# --- 2. MONITORAGE DU MODÈLE IA - MLOps (C11) ---
# Configuration du dossier local pour générer le tableau de bord
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("Eco-Frigo-RAG")

def monitorer_ia_mlflow(store_name: str, budget: float, temps_execution: float, succes: bool):
    """
    Enregistre les performances de l'IA (Features et Métriques) dans MLflow.
    """
    # start_run() crée une nouvelle ligne dans le tableau de bord MLflow
    with mlflow.start_run():
        # Enregistrement des paramètres d'entrée (Features)
        mlflow.log_param("magasin", store_name)
        mlflow.log_param("budget", budget)
        
        # Enregistrement des métriques de performance
        mlflow.log_metric("temps_reponse_secondes", temps_execution)
        mlflow.log_metric("statut_reussite", 1 if succes else 0)

        # mlflow ui --backend-store-uri sqlite:///mlflow.db