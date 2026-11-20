"""
evaluation.py : évalue le modèle Gemini sur 3 cas fixes (carte #22, C13).
Pour chaque cas, on demande un menu de la semaine à Gemini, puis le code vérifie
les produits et les prix (verifier_menu). Le résultat est écrit dans rapport_evaluation.md.
"""
import time
from IA.llm_service import appeler_gemini_json, CLOUD_AI_MODEL
from IA.rag_service import construire_prompt, verifier_menu

# Petit catalogue fixe : les mêmes produits à chaque évaluation, pour pouvoir comparer
PLATS = [
    {"nom": "Filet de poulet", "prix": 2.80}, {"nom": "Steak haché", "prix": 2.20},
    {"nom": "Pavé de saumon", "prix": 3.00}, {"nom": "Escalope de dinde", "prix": 2.60},
    {"nom": "Jambon blanc", "prix": 1.60}, {"nom": "Oeufs frais", "prix": 1.20},
    {"nom": "Saucisses de Toulouse", "prix": 2.00}, {"nom": "Filet de colin", "prix": 2.50},
]
ACCOMPAGNEMENTS = [
    {"nom": "Riz basmati", "prix": 0.60}, {"nom": "Pâtes spaghetti", "prix": 0.50},
    {"nom": "Pommes de terre", "prix": 0.70}, {"nom": "Carottes", "prix": 0.60},
    {"nom": "Haricots verts", "prix": 1.10}, {"nom": "Semoule", "prix": 0.55},
    {"nom": "Brocolis", "prix": 1.20}, {"nom": "Lentilles vertes", "prix": 0.80},
]
CATALOGUE = {p["nom"].lower(): p for p in PLATS + ACCOMPAGNEMENTS}

# Les 3 cas testés : (budget par personne et par plat, nombre de personnes)
CAS = [(6.0, 2), (8.0, 3), (10.0, 4)]

lignes = []
conformes = 0
temps_total = 0
for budget, personnes in CAS:
    debut = time.time()
    try:
        reponse = appeler_gemini_json(construire_prompt(PLATS, ACCOMPAGNEMENTS, budget, personnes))
        if not reponse:
            raise RuntimeError("Clé API Gemini absente")
        # Le code contrôle la réponse : produits connus et plats dans le budget
        _, problemes = verifier_menu(reponse, CATALOGUE, budget)
        resultat = "conforme" if not problemes else f"{len(problemes)} problème(s)"
    except Exception as erreur:
        resultat = f"erreur : {erreur}"
    duree = time.time() - debut
    temps_total += duree
    conformes += resultat == "conforme"
    lignes.append(f"| {budget} € | {personnes} | {resultat} | {duree:.1f} s |")

rapport = f"""# Rapport d'évaluation du modèle

Modèle : {CLOUD_AI_MODEL}

| Budget | Personnes | Résultat | Temps |
|---|---|---|---|
""" + "\n".join(lignes) + f"""

Menus conformes du premier coup : {conformes} sur {len(CAS)}
Temps moyen : {temps_total / len(CAS):.1f} s
"""

with open("rapport_evaluation.md", "w", encoding="utf-8") as fichier:
    fichier.write(rapport)
print(rapport)