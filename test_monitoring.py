"""
test_monitoring.py : tests du suivi MLflow et du journal de sécurité (carte #17, C11).
MLflow est remplacé par un faux (@patch) : on regarde seulement ce que le code lui envoie.
"""
from unittest.mock import patch
from monitoring import monitorer_ia_mlflow, enregistrer_alerte_securite


def valeurs(appels):
    # Transforme les appels (nom, valeur) de MLflow en dictionnaire facile à lire
    return {appel.args[0]: appel.args[1] for appel in appels}


@patch("monitoring.mlflow")
def test_generation_reussie_enregistre_parametres_et_metriques(mlflow):
    # Une génération réussie : on garde ce qui a été demandé, le modèle, le temps et le statut 1
    monitorer_ia_mlflow("E.Leclerc", 20.0, 3.5, succes=True, personnes=2, modele="gemini-test")
    assert valeurs(mlflow.log_param.call_args_list) == {
        "magasin": "E.Leclerc", "budget": 20.0, "personnes": 2, "modele": "gemini-test"}
    assert valeurs(mlflow.log_metric.call_args_list) == {
        "temps_reponse_secondes": 3.5, "statut_reussite": 1}
    mlflow.set_tag.assert_not_called()            # pas d'erreur à noter


@patch("monitoring.mlflow")
def test_generation_en_echec_enregistre_statut_0_et_erreur(mlflow):
    # Un échec : statut 0 et la raison est notée pour la retrouver dans le tableau de bord
    monitorer_ia_mlflow("Carrefour", 15.0, 1.0, succes=False, personnes=2, modele="gemini-test", erreur="Gemini n'a pas répondu")
    assert valeurs(mlflow.log_metric.call_args_list)["statut_reussite"] == 0
    mlflow.set_tag.assert_called_once_with("erreur", "Gemini n'a pas répondu")


@patch("monitoring.logging")
def test_alerte_securite_ecrite_dans_le_journal(journal):
    # Une alerte est écrite en niveau « warning » avec la cible et le motif
    enregistrer_alerte_securite("a@b.fr", "Échec de la génération")
    message = journal.warning.call_args.args[0]
    assert "a@b.fr" in message and "Échec de la génération" in message