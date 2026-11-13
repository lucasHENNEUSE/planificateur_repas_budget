"""
test_rag.py : tests du moteur de menus (RAG) avec un faux Gemini et une fausse base (Mocks, C12).
On vérifie que le code contrôle bien la réponse de l'IA : produits réels, budget, prix recalculé.
"""
import pytest
from unittest.mock import patch
from IA.rag_service import verifier_menu, generer_menu_rag, JOURS

PRODUITS = [
    {"nom": "Filet de poulet", "prix": 2.0},
    {"nom": "Riz", "prix": 1.0},
]
CATALOGUE = {p["nom"].lower(): p for p in PRODUITS}


def reponse_ia(produits):
    """Fabrique une réponse d'IA : 2 plats par jour avec les produits donnés."""
    plat = {"nom": "Poulet et riz", "produits": produits}
    return {jour: [plat, plat] for jour in JOURS}


def test_prix_recalcule_par_le_code():
    menu, problemes = verifier_menu(reponse_ia(["Filet de poulet", "Riz"]), CATALOGUE, budget_max=4.0)
    assert problemes == []
    assert menu["Lundi"][0]["prix_par_personne"] == 3.0  # 2.0 + 1.0


def test_produit_invente_refuse():
    _, problemes = verifier_menu(reponse_ia(["Filet de poulet", "Caviar"]), CATALOGUE, budget_max=4.0)
    assert any("Caviar" in p for p in problemes)


def test_plat_hors_budget_refuse():
    _, problemes = verifier_menu(reponse_ia(["Filet de poulet", "Riz"]), CATALOGUE, budget_max=2.5)
    assert any("au-dessus du budget" in p for p in problemes)


@patch("IA.rag_service.get_store_products", return_value=PRODUITS)
@patch("IA.rag_service.menus_collection")
@patch("IA.rag_service.appeler_gemini_json")
def test_generation_reussie(mock_gemini, mock_coll, mock_produits):
    mock_coll.find_one.return_value = None  # pas de cache
    mock_gemini.return_value = reponse_ia(["Filet de poulet", "Riz"])

    menu = generer_menu_rag("E.Leclerc", "4.0", 3)

    assert len(menu) == 7
    mock_coll.update_one.assert_called_once()  # le menu est enregistré en cache


@patch("IA.rag_service.get_store_products", return_value=PRODUITS)
@patch("IA.rag_service.menus_collection")
@patch("IA.rag_service.appeler_gemini_json")
def test_correction_demandee_a_l_ia(mock_gemini, mock_coll, mock_produits):
    mock_coll.find_one.return_value = None
    mock_gemini.side_effect = [reponse_ia(["Filet de poulet", "Caviar"]), reponse_ia(["Filet de poulet", "Riz"])]

    generer_menu_rag("E.Leclerc", "4.0", 3)

    assert mock_gemini.call_count == 2
    assert "Caviar" in mock_gemini.call_args_list[1].args[0]  # l'erreur est renvoyée à l'IA


@patch("IA.rag_service.get_store_products", return_value=PRODUITS)
@patch("IA.rag_service.menus_collection")
def test_budget_trop_bas_refuse(mock_coll, mock_produits):
    mock_coll.find_one.return_value = None
    with pytest.raises(ValueError):
        generer_menu_rag("E.Leclerc", "1.0", 3)  # aucun produit à moins de 0,50 €


@patch("IA.rag_service.get_store_products", return_value=PRODUITS)
@patch("IA.rag_service.menus_collection")
@patch("IA.rag_service.appeler_gemini_json", return_value=None)
def test_echec_si_gemini_ne_repond_pas(mock_gemini, mock_coll, mock_produits):
    mock_coll.find_one.return_value = None
    with pytest.raises(RuntimeError):
        generer_menu_rag("E.Leclerc", "4.0", 3)
    mock_coll.update_one.assert_not_called()  # rien n'est mis en cache