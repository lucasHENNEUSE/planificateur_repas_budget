"""
test_donnees.py : tests des données (carte #16, C12).

On vérifie la qualité des données à chaque étape :
1. les produits choisis pour l'IA,
2. les menus générés (structure, produits réels, budget),
3. l'enregistrement dans la base,
4. le chargement du catalogue.
La base, Gemini et Open Food Facts sont remplacés par de fausses réponses (@patch).
"""
from unittest.mock import patch, MagicMock
from IA.rag_service import recuperer_produits, generer_menu_rag, JOURS
from data.database import get_store_collection, save_products, get_store_products, count_products
from data.catalogue_service import scrape_store_catalog

# ---------- 1. Produits choisis pour l'IA ----------

PRODUITS_BASE = [
    {"nom": "Filet de poulet", "prix": 2.0},   # plat principal : gardé
    {"nom": "Riz", "prix": 1.0},               # accompagnement : gardé
    {"nom": "Yaourt nature", "prix": 0.8},     # dessert : exclu
    {"nom": "Huile d'olive", "prix": 3.0},     # condiment : exclu
    {"nom": "Steak haché", "prix": 5.0},       # trop cher pour le budget : exclu
]


@patch("IA.rag_service.get_store_products", return_value=PRODUITS_BASE)
def test_produits_exclus_ou_trop_chers_ecartes(base):
    # Budget 6 € : un produit seul ne doit pas dépasser 3 € (la moitié du budget)
    plats, accompagnements = recuperer_produits("E.Leclerc", 6.0)
    assert [p["nom"] for p in plats] == ["Filet de poulet"]
    assert [p["nom"] for p in accompagnements] == ["Riz"]


# ---------- 2. Menus générés ----------

PRODUITS_MENU = [{"nom": "Filet de poulet", "prix": 2.0}, {"nom": "Riz", "prix": 1.0}]
PLAT = {"nom": "Poulet et riz", "produits": ["Filet de poulet", "Riz"]}
BUDGET = 4.0


@patch("IA.rag_service.get_store_products", return_value=PRODUITS_MENU)
@patch("IA.rag_service.menus_collection")
@patch("IA.rag_service.appeler_gemini_json", return_value={jour: [PLAT, PLAT] for jour in JOURS})
def menu_genere(gemini, cache, base):
    # Génère un menu avec un faux Gemini (utilisé par les 3 tests ci-dessous)
    cache.find_one.return_value = None
    return generer_menu_rag("E.Leclerc", str(BUDGET), 2)


def test_menu_sept_jours_deux_plats():
    # Chaque jour de la semaine a exactement 2 plats au choix
    menu = menu_genere()
    assert list(menu.keys()) == JOURS
    assert all(len(plats) == 2 for plats in menu.values())


def test_menu_champs_obligatoires():
    # Chaque plat a un numéro d'option, un nom, un prix et la liste des ingrédients
    for plats in menu_genere().values():
        for plat in plats:
            assert set(plat.keys()) == {"option", "nom", "prix_par_personne", "ingredients"}


def test_menu_budget_et_produits_reels():
    # Chaque plat respecte le budget et n'utilise que des produits de la base
    noms_reels = [p["nom"] for p in PRODUITS_MENU]
    for plats in menu_genere().values():
        for plat in plats:
            assert 0 < plat["prix_par_personne"] <= BUDGET
            assert all(ingredient in noms_reels for ingredient in plat["ingredients"])


# ---------- 3. Enregistrement dans la base ----------

@patch("data.database.db", {"produits_carrefour": "tiroir Carrefour", "produits_leclerc": "tiroir Leclerc"})
def test_produits_ranges_dans_le_bon_tiroir():
    # Carrefour a sa collection, tout le reste va dans celle de Leclerc
    assert get_store_collection("Carrefour Brest") == "tiroir Carrefour"
    assert get_store_collection("E.Leclerc Brest") == "tiroir Leclerc"
    assert get_store_collection("Autre magasin") == "tiroir Leclerc"


@patch("data.database.get_store_collection")
def test_enregistrement_sans_doublon(tiroir):
    # Un produit est identifié par son nom ET son magasin, et enregistré en « upsert »
    # (mis à jour s'il existe déjà, créé sinon) : pas de doublon.
    save_products("E.Leclerc Brest", [{"nom": "Riz", "prix": 1.0, "enseigne": "E.Leclerc Brest"}])
    filtre, _ = tiroir.return_value.update_one.call_args.args
    assert filtre == {"nom": "Riz", "enseigne": "E.Leclerc Brest"}
    assert tiroir.return_value.update_one.call_args.kwargs["upsert"] is True


@patch("data.database.get_store_collection")
def test_lecture_limitee_au_magasin(tiroir):
    # On ne lit et on ne compte que les produits du magasin demandé
    count_products("E.Leclerc Brest")
    get_store_products("E.Leclerc Brest")
    tiroir.return_value.count_documents.assert_called_once_with({"enseigne": "E.Leclerc Brest"})
    assert tiroir.return_value.find.call_args.args[0] == {"enseigne": "E.Leclerc Brest"}


# ---------- 4. Chargement du catalogue (Open Food Facts) ----------

def fausse_reponse():
    # Fausse réponse d'Open Food Facts : 1 bon produit, 1 sans nom, 1 nom trop court
    reponse = MagicMock(status_code=200)
    reponse.json.return_value = {"products": [
        {"product_name_fr": "Poulet rôti", "categories": "Viandes, Plats"},
        {"product_name": ""},
        {"product_name": "ab"},
    ]}
    return reponse


@patch("data.catalogue_service.get_store_products", return_value=[])
@patch("data.catalogue_service.save_products")
@patch("data.catalogue_service.count_products", return_value=0)
@patch("data.catalogue_service.requests.get", return_value=fausse_reponse())
def test_catalogue_produits_valides_seulement(web, compte, sauvegarde, lecture):
    # Les produits sans nom ou au nom trop court sont ignorés ; les autres ont un prix, un rayon, une enseigne
    scrape_store_catalog("E.Leclerc Brest")
    produits = sauvegarde.call_args.args[1]
    assert produits[0] == {"nom": "Poulet rôti", "prix": 3.0, "rayon": "Viandes", "enseigne": "E.Leclerc Brest"}
    assert all(len(p["nom"]) > 2 for p in produits)


@patch("data.catalogue_service.get_store_products", return_value=[])
@patch("data.catalogue_service.save_products")
@patch("data.catalogue_service.count_products", return_value=0)
@patch("data.catalogue_service.requests.get", return_value=fausse_reponse())
def test_catalogue_prix_dans_la_fourchette(web, compte, sauvegarde, lecture):
    # Open Food Facts ne donne pas de prix : le code en attribue un entre 1,50 € et 3,00 €
    scrape_store_catalog("E.Leclerc Brest")
    assert all(1.5 <= p["prix"] <= 3.0 for p in sauvegarde.call_args.args[1])


@patch("data.catalogue_service.get_store_products", return_value=[])
@patch("data.catalogue_service.save_products")
@patch("data.catalogue_service.count_products", return_value=0)
@patch("data.catalogue_service.requests.get", return_value=fausse_reponse())
def test_catalogue_plan_b_si_peu_de_produits(web, compte, sauvegarde, lecture):
    # Moins de 50 produits trouvés : 3 pages du plan A puis 4 recherches de secours (plan B)
    scrape_store_catalog("E.Leclerc Brest")
    assert web.call_count == 3 + 4


@patch("data.catalogue_service.get_store_products", return_value=[])
@patch("data.catalogue_service.count_products", return_value=400)
@patch("data.catalogue_service.requests.get")
def test_catalogue_deja_rempli_aucun_appel(web, compte, lecture):
    # Déjà 400 produits en base : on n'appelle pas Open Food Facts
    scrape_store_catalog("E.Leclerc Brest")
    web.assert_not_called()