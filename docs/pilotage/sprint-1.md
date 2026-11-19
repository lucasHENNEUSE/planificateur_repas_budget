# Sprint 1 : du 9 au 22 novembre 2026

**Projet :** Éco-Frigo, planificateur de repas selon un budget.
**Méthode :** Scrum allégé, sprints de 2 semaines, suivi dans GitHub Projects.
**Rôles :** je suis à la fois Product Owner, développeur et Scrum Master. Mon formateur reçoit le tableau et les comptes rendus.

## 1. Planification (9 novembre)

**Objectif :** mettre en place le pilotage du projet (kanban, veille) et corriger les failles de sécurité les plus simples.

| Carte | Titre | Compétence |
|---|---|---|
| #2 | Créer le tableau kanban et le backlog | C16 |
| #3 | Rédiger le modèle de compte rendu | C16 |
| #4 | Choisir le thème de veille et installer le lecteur RSS | C6 |
| #5 | Fixer le créneau de veille et faire la 1re synthèse | C6 |
| #6 | Ajouter logs, base MLflow et `.env` au `.gitignore` | C20 |
| #7 | Rendre `SECRET_KEY` obligatoire | C9 |
| #8 | Protéger les routes par JWT | C9 |

**Rituels :** point quotidien à chaque séance, veille chaque samedi (14 h à 16 h), revue et rétrospective en fin de sprint.

## 2. Points quotidiens

| Date | Ce que j'ai fait | Blocage |
|---|---|---|
| 9 novembre | Projet GitHub, kanban, 24 cartes de backlog, compte Inoreader, dossier de veille. | Feedly payant : choix d'Inoreader (gratuit). |
| 10 novembre | `.gitignore`, `SECRET_KEY` obligatoire (PR #28), routes protégées par JWT (carte #8), 1re synthèse de veille. | Push refusé, résolu avec `git pull --rebase`. |
| 13 novembre | Nouveau moteur de menus RAG (PR #36), interface accessible (PR #35), captures annotées (PR #34), MCD et parcours. | Clé de l'IA invalide, erreur 503, plats trop chers : voir le journal. |
| 14 novembre | Architecture (#12), choix techniques (PR #40), tests des routes (PR #41), tests de données (PR #42). | Pull request absente : je n'avais pas poussé ma branche. |
| 19 novembre | Suivi MLflow du RAG (PR #44), `httpx2` (PR #45), veille complémentaire, pseudonymisation des e-mails dans les logs (#19), alerte après 3 échecs de suite (#18), messages d'erreur clairs de Gemini (#26), mention « IA » sur la page d'accueil, correction de `utcnow`. | Git refusait de changer de branche : `git stash`. 6 tests de routes écrasés par une autre carte : repérés avec le nombre de tests (42 au lieu de 48), restaurés. |

## 3. Imprévus et décisions

| Date | Imprévu | Décision |
|---|---|---|
| 9 novembre | Feedly inadapté | Inoreader |
| 10 novembre | Quota gratuit de Gemini limité (veille) | Cartes « erreur 429 » et « niveau de réflexion » ajoutées au sprint 3 |
| 13 novembre | Moteur de menus de mauvaise qualité | Refait tout de suite (carte #14, prévue au sprint 3) |
| 13 novembre | Défauts d'accessibilité dans l'interface | Corrigés tout de suite (carte #23, prévue au sprint 6) |
| 19 novembre | Une carte a écrasé 6 tests des routes en copiant une ancienne version du fichier | Fichier restauré avec une PR de correction. Règle : comparer le nombre de tests après chaque fusion |

Détail des problèmes : `docs/journal-problemes.md`.

## 4. Revue de sprint (20 novembre)

**Cartes terminées en plus, prévues pour des sprints suivants :** #10, #11, #12, #13, #14, #15, #16, #17, #18, #19, #23, #25 et #26 (PR #34 à #44, puis les PR des cartes du 19 novembre), plus la carte « mention IA » sur la page d'accueil.

**Démonstration :**
1. Connexion, choix du magasin et du budget, menus générés avec le RAG, recette d'un plat.
2. Une route sans jeton est refusée, un jeton expiré renvoie à la connexion.
3. Le tableau MLflow : temps de réponse, statut, nombre d'essais.

## 5. Rétrospective

**Ce qui a bien marché**
- Une branche et une pull request par carte, avec `Closes #N`.
- Je note les problèmes dans le journal quand ils arrivent.
- La veille m'a servi tout de suite (quota de Gemini, article 50 de l'AI Act).
- Le code contrôle l'IA : c'est lui qui garantit le budget.

**Ce qui a moins bien marché**
- Je n'ai pas fait les points quotidiens dès le premier jour.
- Mon plan ne suivait plus mon avancement : j'ai fini des cartes de sprints futurs sans replanifier.
- Plusieurs oublis avec Git : branche non poussée, images non ajoutées, fichier dans le mauvais dossier.
- Des informations privées visibles dans des captures (e-mail, `.env`).

**Actions pour le sprint 2**
1. Replanifier les sprints 2 à 6 avec ce qui reste à faire.
2. Écrire 3 lignes de point quotidien à la fin de chaque séance.
3. Avant chaque pull request : `git status` propre et `git diff main --stat` pour vérifier les fichiers envoyés.
4. Fermer `.env` avant chaque capture.

