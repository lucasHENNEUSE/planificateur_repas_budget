"""
rag_service.py : génération des menus par RAG (Retrieval-Augmented Generation).

1. RÉCUPÉRER : on choisit dans MongoDB des produits réels du magasin, avec leur prix.
2. GÉNÉRER   : on donne ces produits à Gemini, qui compose les plats de la semaine.
3. CONTRÔLER : le code vérifie les produits et recalcule lui-même le prix de chaque plat.
"""
import random
from data.database import menus_collection, get_store_products
from IA.llm_service import appeler_gemini_json

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

# Mots qui écartent un produit (desserts, boissons, snacks, condiments...)
MOTS_EXCLUS = [
    "yaourt", "chocolat", "biscuit", "bonbon", "glace", "sucre", "confiture",
    "gâteau", "dessert", "lait", "boisson", "céréales", "compote", "crème",
    "café", "thé", "jus", "soda", "cacao", "barre", "viennoiserie", "brioche",
    "miel", "nutella", "caramel", "coca", "eau", "sirop", "chips", "apéro",
    "apéritif", "cacahuète", "pistache", "amande", "noix", "sauce", "ketchup",
    "mayo", "moutarde", "tartinable", "tapenade", "crostini", "toast", "snack",
    "chewing", "sucette", "sablé", "tartelette", "gaufre", "crêpe", "confit",
    "pâté", "rillettes", "saucisson", "chorizo", "pétillant", "infusion",
    "vinaigrette", "vinaigre", "huile", "beurre", "margarine", "mayonnaise"
]

# Mots qui reconnaissent un plat principal (viande, poisson, oeufs...)
MOTS_PLATS = [
    "poulet", "boeuf", "porc", "poisson", "saumon", "thon", "colin", "jambon",
    "dinde", "tofu", "oeuf", "steak", "haché", "saucisse", "filet", "viande",
    "escalope", "cabillaud", "crevette", "canard", "veau", "agneau", "rôti",
    "pavé", "merguez", "chipolata", "cordon bleu", "nuggets", "seitan", "tempeh",
    "hoki", "lieu", "églefin", "sardine", "maquereau", "burger", "pizza", "quiche"
]

# Mots qui reconnaissent un accompagnement (légumes, féculents)
MOTS_ACCOMPAGNEMENTS = [
    "pâte", "riz", "pomme de terre", "semoule", "lentille", "tomate", "carotte",
    "courgette", "haricot", "petit pois", "brocoli", "salade", "légume",
    "champignon", "purée", "frite", "blé", "quinoa", "spaghetti", "macaroni",
    "ebly", "boulgour", "pois chiche", "flageolet", "poireau", "aubergine", "chou",
    "épinard", "navet", "potiron", "butternut", "penne", "coquillette", "tagliatelle"
]


def recuperer_produits(store_name, budget_max):
    """
    Retourne 20 plats principaux et 20 accompagnements du magasin (choisis au hasard).
    Un plat = 1 plat principal + 1 accompagnement : on ne garde que les produits à moins de
    la moitié du budget, ce qui garantit que n'importe quelle combinaison respecte le budget.
    """
    plats, accompagnements = [], []
    for produit in get_store_products(store_name, limit=800):
        nom = produit["nom"].lower()
        if any(mot in nom for mot in MOTS_EXCLUS) or produit["prix"] > budget_max / 2:
            continue
        if any(mot in nom for mot in MOTS_PLATS):
            plats.append(produit)
        elif any(mot in nom for mot in MOTS_ACCOMPAGNEMENTS):
            accompagnements.append(produit)

    if not plats or not accompagnements:
        raise ValueError("Pas assez de produits à ce prix dans ce magasin : augmentez le budget.")

    random.shuffle(plats)
    random.shuffle(accompagnements)
    return plats[:20], accompagnements[:20]


def construire_prompt(plats, accompagnements, budget_max, total_people, remarques=""):
    """Écrit la consigne donnée à Gemini : les produits disponibles + les règles."""
    liste_plats = "\n".join(f"- {p['nom']} : {p['prix']:.2f} €" for p in plats)
    liste_acc = "\n".join(f"- {p['nom']} : {p['prix']:.2f} €" for p in accompagnements)
    return f"""Tu composes les repas de la semaine pour {total_people} personnes.
Budget maximum : {budget_max:.2f} € par personne et par plat.

PRODUITS DISPONIBLES (nom exact : prix par personne)
Plats principaux :
{liste_plats}
Accompagnements :
{liste_acc}

Propose 2 plats différents pour chaque jour, de Lundi à Dimanche.
RÈGLES :
1. Chaque plat utilise exactement 2 produits de la liste : un plat principal et un accompagnement, avec leur nom exact. N'invente aucun produit.
2. Le nom du plat est un vrai nom de plat français (ex : "Poulet rôti, riz et carottes"), pas un nom de produit.
3. Réponds uniquement en JSON, de cette forme :
{{"Lundi": [{{"nom": "...", "produits": ["nom exact", "nom exact"]}}, {{"nom": "...", "produits": ["nom exact", "nom exact"]}}], "Mardi": [...]}}
{remarques}"""


def verifier_menu(menu_ia, catalogue, budget_max):
    """
    Contrôle la réponse de l'IA. Retourne (menu, problemes).
    catalogue : {nom du produit en minuscules : produit}
    """
    menu, problemes = {}, []
    for jour in JOURS:
        menu[jour] = []
        for numero, plat in enumerate(menu_ia[jour], start=1):
            prix = 0
            for nom_produit in plat["produits"]:
                produit = catalogue.get(nom_produit.strip().lower())
                if produit is None:
                    problemes.append(f"{jour} : le produit « {nom_produit} » n'est pas dans la liste")
                else:
                    prix += produit["prix"]
            if prix > budget_max:
                problemes.append(f"{jour} : le plat « {plat['nom']} » coûte {prix:.2f} €, au-dessus du budget")
            menu[jour].append({
                "option": numero,
                "nom": plat["nom"],
                "prix_par_personne": round(prix, 2),
                "ingredients": plat["produits"]
            })
    return menu, problemes


def generer_menu_rag(store_name, budget, total_people):
    """Retourne le menu de la semaine {jour: [plat 1, plat 2]}. Lève une erreur si l'IA échoue."""
    budget_max = float(budget)
    cle = f"menu_v2_{store_name.lower().replace(' ', '_')}_b{budget}_p{total_people}"

    # Cache : si ce menu existe déjà, on n'appelle pas l'IA (économie de quota)
    en_cache = menus_collection.find_one({"type": "menu_cache", "key": cle})
    if en_cache:
        return en_cache["menus"]

    plats, accompagnements = recuperer_produits(store_name, budget_max)
    catalogue = {p["nom"].strip().lower(): p for p in plats + accompagnements}

    # 2 essais au maximum : si le contrôle trouve des erreurs, on les renvoie à l'IA
    remarques = ""
    for _ in range(2):
        reponse = appeler_gemini_json(construire_prompt(plats, accompagnements, budget_max, total_people, remarques))
        if not reponse:
            raise RuntimeError("Gemini n'a pas répondu (clé invalide, quota atteint ou service indisponible : voir le terminal).")

        menu, problemes = verifier_menu(reponse, catalogue, budget_max)
        if not problemes:
            menus_collection.update_one(
                {"type": "menu_cache", "key": cle},
                {"$set": {"menus": menu, "enseigne": store_name}},
                upsert=True
            )
            return menu
        remarques = "Ta réponse précédente contenait des erreurs, corrige-les :\n- " + "\n- ".join(problemes)

    raise ValueError("Menu refusé après correction : " + " ; ".join(problemes[:3]))