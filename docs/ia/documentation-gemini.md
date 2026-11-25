# Documentation du service Gemini dans Éco-Frigo (carte #24, C8)

**Date :** 21 novembre 2026
**Objet :** décrire comment le service d'IA retenu (l'API Gemini de Google) est installé, configuré, surveillé et testé dans Éco-Frigo, pour qu'une autre personne puisse le refaire.
**Document lié :** le choix de ce service est justifié dans `benchmark-services-ia.md` (C7).

## 1. Ce que fait le service dans l'application

Éco-Frigo appelle Gemini à trois endroits, tous par la même fonction `appeler_gemini_json` du fichier `IA/llm_service.py` :

| Usage | Où | Ce que Gemini reçoit | Ce qu'il renvoie |
|---|---|---|---|
| Magasins d'une ville | `obtenir_magasins_depuis_llm` | Le nom d'une ville | 2 à 4 magasins Leclerc ou Carrefour (nom, adresse) |
| Recette d'un plat | `rediger_recette_depuis_llm` | Le nom d'un plat et le nombre de personnes | Les ingrédients et 4 à 7 étapes |
| Menu de la semaine | `rag_service.py` | Des produits (plats et accompagnements) pris dans ma base avec leur prix, le budget, le nombre de personnes. Au second essai, il reçoit aussi les erreurs trouvées par le code. | Un menu : 2 plats par jour, avec leurs produits |

Dans tous les cas la réponse est demandée en JSON. Le code contrôle ensuite le résultat : l'IA compose, le code vérifie.

## 2. L'environnement d'exécution

| Élément | Choix |
|---|---|
| Service d'IA | API Gemini, service en ligne (SaaS) de Google. Rien n'est installé pour le modèle lui-même. |
| Modèle | `gemini-3.8-flash`, défini par la constante `CLOUD_AI_MODEL` dans `IA/llm_service.py` |
| Compte | Un compte Google, avec une clé API créée dans Google AI Studio |
| Offre | Niveau gratuit |
| Application | Deux conteneurs Docker lancés par `docker-compose.yml` : `mongodb` (port 27019) et `app` (port 8000) |
| Hébergement de l'application | Pas d'hébergement en ligne : l'application se lance en local avec Docker Compose. La livraison continue (`cd.yml`) publie l'image Docker sur ghcr.io, d'où elle peut être récupérée et lancée sur une autre machine. |

Changer de modèle demande de modifier une seule ligne : la constante `CLOUD_AI_MODEL`.

## 3. Les dépendances

| Dépendance | Rôle |
|---|---|
| Python 3.12 | Langage de l'application (image Docker et tests) |
| `google-genai` | Bibliothèque officielle de Google pour appeler Gemini |
| `mlflow` | Enregistrement des mesures de chaque génération |
| `pytest` et `pytest-cov` | Tests et mesure de la couverture |
| Docker et Docker Compose | Lancement de l'application et de MongoDB |
| MongoDB | Cache des menus, des recettes et des magasins déjà générés |

Les versions exactes sont dans `requirements.txt`, généré avec `pip freeze`.

## 4. Les accès et la gestion des secrets

| Sujet | Mise en œuvre |
|---|---|
| Qui a accès | Projet personnel : la clé appartient à un seul compte Google, le mien. Aucun groupe d'utilisateurs ni droits à gérer. |
| Où est la clé en local | Dans le fichier `.env`, variable `GOOGLE_API_KEY`. Le fichier est ignoré par Git (`.gitignore`) et exclu de l'image Docker (`.dockerignore`). |
| Où est la clé en intégration continue | Dans les secrets du dépôt GitHub (Settings, Secrets and variables, Actions), sous le nom `GOOGLE_API_KEY`. `cd.yml` y fait référence par `${{ secrets.GOOGLE_API_KEY }}`. |
| Si la clé est publiée par erreur | La protection GitHub bloque l'envoi d'un secret détecté. En cas de fuite réelle, je supprime la clé dans Google AI Studio et j'en crée une autre. |
| Si la clé est absente | `appeler_gemini_json` affiche une erreur et ne contacte pas Gemini. Si la clé est refusée, l'utilisateur voit « Clé API Gemini invalide, contacte l'administrateur. » |
| Limites d'usage | Elles s'appliquent par projet Google et non par clé : créer une seconde clé dans le même projet ne donne pas plus de requêtes. |

La clé ne doit jamais être écrite dans un fichier suivi par Git, dans un message de commit ou dans un échange.

## 5. La configuration du service

| Paramètre | Valeur | Raison |
|---|---|---|
| Modèle | `gemini-3.8-flash` | Modèle de la gamme « Flash », rapide, avec accès gratuit |
| Format de réponse | `response_mime_type="application/json"` | Le code lit directement du JSON |
| Délai maximum | 60 secondes | Pour ne jamais attendre sans fin (un blocage de 13 minutes dans la chaîne de livraison a motivé ce réglage) |
| Nouvelles tentatives | Jusqu'à 3 essais, seulement après une erreur 503, avec 3 secondes d'attente | Gemini est parfois surchargé. Pour les autres erreurs, réessayer ne sert à rien. |
| Erreur 429 (quota) | Message : « Limite d'utilisation de Gemini atteinte, réessaie plus tard. » | Message clair pour l'utilisateur, au lieu d'une réponse vide |
| Erreur 503 (surcharge) | Message : « Gemini est surchargé, réessaie dans un instant. » | Idem |
| Niveau de réflexion | Valeur par défaut du modèle. Le niveau « low » est en test (carte #27) et n'est pas encore adopté. | Réduire le temps de réponse |
| Mention pour l'utilisateur | Une phrase sur la page d'accueil indique que menus et recettes sont générés par une IA (Gemini) | Information de transparence (AI Act, article 50) |

Limite connue : le format JSON est demandé sans schéma de réponse. Sans schéma, Google indique que ce n'est qu'une forte consigne. Mon code contrôle chaque menu, donc je garde cette version simple.

## 6. Le monitorage

Chaque génération de menu est enregistrée dans MLflow par la fonction `monitorer_ia_mlflow` du fichier `monitoring.py`.

| Élément enregistré | Contenu |
|---|---|
| Paramètres | magasin, budget, nombre de personnes, modèle utilisé |
| Mesures | `temps_reponse_secondes`, `statut_reussite` (1 ou 0), `nombre_essais` (en cas de réussite) |
| Étiquette | `erreur`, la raison de l'échec |
| Alerte | Après 3 échecs de génération de suite, une ligne « ALERTE IA » est écrite dans `logs/api_eco_frigo.log`. Une réussite remet le compteur à zéro. |
| Sécurité | Les alertes de sécurité n'écrivent jamais l'e-mail : une empreinte de 8 caractères le remplace. |

**Voir le tableau de bord.** Dans un terminal, à la racine du projet :

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Puis ouvrir l'adresse indiquée dans le terminal (par défaut `http://127.0.0.1:5000`), choisir l'expérience `Eco-Frigo-RAG` et ouvrir la vue graphique. Le tableau de bord montre le temps de réponse, la réussite et le nombre d'essais. Il est réglé à la main dans MLflow ; une capture d'écran en garde la trace.

## 7. La procédure d'installation

1. Récupérer le code : `git clone https://github.com/lucasHENNEUSE/planificateur_repas_budget.git`, puis entrer dans le dossier.
2. Créer une clé API dans Google AI Studio.
3. Créer à la racine un fichier `.env` contenant une ligne `GOOGLE_API_KEY=` suivie de la clé (sans espace). Ne pas ajouter ce fichier à Git.
4. Lancer l'application et MongoDB :

```bash
docker compose up --build
```

5. Ouvrir `http://localhost:8000` dans le navigateur.

Installation sans Docker : créer un environnement virtuel Python 3.12, lancer `pip install -r requirements.txt`, démarrer MongoDB, puis `uvicorn main:app`.

## 8. La procédure de test

| Test | Commande | Ce qu'il vérifie | Requêtes Gemini consommées |
|---|---|---|---|
| Tests automatiques | `pytest` | 54 tests, avec Gemini et la base remplacés par de fausses réponses. Couverture mesurée, seuil de 80 %. | 0 |
| Accès au service | Générer une recette depuis l'interface | La clé est acceptée et Gemini répond. | 1 |
| Évaluation du modèle | `python evaluation.py` | 3 demandes de menu, avec un rapport (menus conformes, temps de réponse) écrit dans `rapport_evaluation.md`. | 3 |

L'évaluation peut aussi être lancée depuis l'onglet Actions de GitHub (« Run workflow »). Elle n'est plus lancée automatiquement, pour ne pas vider le quota. Le fichier `rapport_evaluation.md` est généré : il ne doit pas être ajouté à Git.

## 9. Les données impliquées

| Donnée | Envoyée à Gemini ? | Où elle est conservée |
|---|---|---|
| Nom d'une ville | Oui | Cache MongoDB (liste de magasins) |
| Nom d'un plat, nombre de personnes | Oui | Cache MongoDB (recette) |
| Produits, prix, budget | Oui | Menus enregistrés dans MongoDB |
| E-mail, mot de passe | **Non, jamais** | Base MongoDB (mot de passe haché avec bcrypt). Dans les journaux, l'e-mail est remplacé par une empreinte. |

Avec le niveau gratuit, Google indique que des réviseurs humains peuvent lire les échanges et que les contenus peuvent servir à améliorer ses produits. Comme aucune donnée personnelle n'est envoyée, ce niveau reste acceptable pour une démonstration. Pour de vrais utilisateurs, il faudrait le niveau payant (veille du 20 novembre).

## 10. Les interconnexions

| Avec | Rôle |
|---|---|
| MongoDB | Cache des menus, recettes et magasins : évite des appels à Gemini et économise le quota |
| MLflow | Mesures et tableau de bord |
| GitHub Actions (`ci.yml`, `cd.yml`) | Les tests tournent à chaque push ; après des tests réussis, `cd.yml` publie l'image Docker sur ghcr.io ; l'évaluation de Gemini se lance à la demande et utilise le secret `GOOGLE_API_KEY` |
| Docker Compose | Lance l'application, MongoDB et lit le fichier `.env` |

## 11. Les limites connues et ce qui s'est passé

| Sujet | Constat | Réponse |
|---|---|---|
| Quota | 20 requêtes par jour observées pour `gemini-3.8-flash` (message d'erreur 429, à confirmer sur la page officielle) | Message clair, cache MongoDB, évaluation lancée à la main |
| Surcharge | Erreurs 503 fréquentes le 20 et le 21 novembre, qui allongent les temps mesurés à plusieurs minutes | Nouvelles tentatives, délai maximum de 60 secondes, mesure à refaire à un moment plus calme |
| Blocage de la livraison | Une évaluation sans délai maximum a tourné plus de 13 minutes | Délai de 60 secondes côté Gemini et de 10 minutes pour le travail GitHub |
| Clé API | Une clé a failli être publiée dans `cd.yml` | La protection GitHub a bloqué l'envoi ; la clé est lue dans les secrets |
| Données inventées | Ma première approche, un agent d'IA avec de petits modèles Gemma lancés en local avec Ollama (`gemma3:4b`, `gemma2.1:2b`), inventait des données malgré les restrictions du prompt | Mon code fournit à Gemini les produits réels de la base et contrôle chaque menu (`verifier_menu`) : un produit absent de la liste ou un plat au-dessus du budget est refusé |
| Dépendance | Les appels dépendent du SDK `google-genai` | Appels regroupés dans `IA/llm_service.py` |

## Accessibilité de ce document

Le document suit une hiérarchie de titres, les tableaux ont une ligne d'en-tête, les commandes sont dans des blocs séparés, aucune information n'est donnée par la couleur seule et il ne contient pas d'image. Il est écrit en langage simple. À l'export en PDF, je vérifierai que les titres et les tableaux sont bien balisés pour un lecteur d'écran. Il pourra être transmis aux parties prenantes en PDF.