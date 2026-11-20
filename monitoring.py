"""
monitorage.py : Service hybride de sécurité API (C20) et Monitorage MLOps (C11).
"""
import hashlib
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
    """
    Journalise les alertes de sécurité et les échecs.
    L'e-mail n'est jamais écrit en clair : on garde une empreinte de 8 caractères,
    qui permet de reconnaître un même utilisateur sans l'identifier.
    """
    utilisateur = hashlib.sha256(cible.encode()).hexdigest()[:8]
    message = f"ALERTE SÉCURITÉ | Utilisateur : {utilisateur} | Motif : {type_attaque}"
    logging.warning(message)
    print(f"attention {message}")


# --- 2. MONITORAGE DU MODÈLE IA - MLOps (C11) ---
# Configuration du dossier local pour générer le tableau de bord
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("Eco-Frigo-RAG")

# Compte les échecs de génération qui se suivent (pour l'alerte)
echecs_de_suite = 0

def monitorer_ia_mlflow(store_name: str, budget: float, temps_execution: float, succes: bool,
                        personnes: int, modele: str, erreur: str = "", essais: int = 0):
    """
    Enregistre une génération de menu dans MLflow : une ligne par demande.
    - paramètres : ce qui a été demandé (magasin, budget, personnes) et le modèle utilisé
    - métriques  : ce qui a été mesuré (temps de réponse, réussite 1 ou 0, nombre d'essais du RAG)
    - étiquette  : la raison de l'échec, pour retrouver vite les problèmes
    - alerte     : écrite dans le journal après 3 échecs de suite
    """
    global echecs_de_suite

    # On compte les échecs à la suite : une réussite remet le compteur à zéro
    echecs_de_suite = 0 if succes else echecs_de_suite + 1
    if echecs_de_suite >= 3:
        logging.warning(f"ALERTE IA | {echecs_de_suite} échecs de génération de suite")

    # Le titre de la ligne dans MLflow : magasin, budget et nombre de personnes
    with mlflow.start_run(run_name=f"{store_name} - {budget} € - {personnes} pers."):
        mlflow.log_param("magasin", store_name)
        mlflow.log_param("budget", budget)
        mlflow.log_param("personnes", personnes)
        mlflow.log_param("modele", modele)

        mlflow.log_metric("temps_reponse_secondes", temps_execution)
        mlflow.log_metric("statut_reussite", 1 if succes else 0)

        if succes:
            mlflow.log_metric("nombre_essais", essais)

        if erreur:
            mlflow.set_tag("erreur", erreur)

        # Pour voir le tableau de bord : mlflow ui --backend-store-uri sqlite:///mlflow.db