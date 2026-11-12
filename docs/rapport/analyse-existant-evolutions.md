## Analyse de l'existant et évolutions

### 1. Le code d'origine
Éco-Frigo est une application web de planification de repas selon un budget. Elle suit une architecture en couches (n-tiers) :
- **Interface (front-end) :** une page HTML/JavaScript (connexion, choix du magasin, budget, affichage des menus et des recettes).
- **API REST (FastAPI) :** routes d'inscription, de connexion, de recherche de magasins, de génération de menus et de recettes.
- **Services :** authentification (mots de passe hachés avec bcrypt, jetons JWT), catalogue de produits issu d'Open Food Facts, génération des menus par un moteur à base de règles, appel à l'API Gemini pour les magasins et les recettes.
- **Données :** base MongoDB (produits, menus en cache, utilisateurs).
- **Qualité :** journalisation, suivi des appels à l'IA avec MLflow, tests Pytest avec mocks, intégration continue GitHub Actions.

### 2. Analyse
J'ai analysé le code selon trois axes : sécurité (Top 10 OWASP API), fiabilité des tests et cohérence avec les exigences du référentiel.

**Points solides :** hachage des mots de passe, jetons JWT avec expiration, séparation en modules, tests avec mocks, intégration continue, monitorage MLflow.

**Points à améliorer :**

| Constat | Risque | Évolution | Statut |
|---|---|---|---|
| Fichiers générés, logs avec un email et base MLflow suivis par Git | Fuite de données personnelles (RGPD) | `.gitignore` complété, fichiers retirés du suivi | Réalisé (sprint 1) |
| Clé secrète des jetons écrite en dur dans le code | Fabrication de faux jetons | Clé obligatoire via variable d'environnement | Réalisé (PR #28) |
| 3 routes appelant l'IA sans authentification | Épuisement du quota gratuit, accès non contrôlé | Authentification JWT, fonctions bloquantes en `def`, fonction front unique d'envoi du jeton, tests | Réalisé (sprint 1) |
| Tests peu nombreux, un test dépend de l'état de la base | Tests peu fiables | Tests sur toutes les routes, base simulée, mesure de couverture | Prévu (sprint 3) |
| Génération des menus sans IA, prix du catalogue estimés et non réels | Menus peu fiables, résultat difficile à défendre | Chaîne récupération puis génération avec l'IA, vérification du budget sans modifier les prix | Prévu (sprint 3) |
| Erreur du quota Gemini non gérée | Réponse vide, pas de message à l'utilisateur | Message clair et trace dans les logs, suivi MLflow | Prévu (sprint 3) |
| Logs avec des emails en clair, pas d'alertes | Non-conformité RGPD, incidents non détectés | Anonymisation, seuils et alertes | Prévu (sprint 4) |
| Pas d'empaquetage ni de livraison continue | Déploiement non reproductible | Dockerfile, chaîne de livraison continue | Prévu (sprint 5) |
| Affichage de contenus sans protection, accessibilité de l'interface limitée | Faille XSS, interface peu accessible | Échappement des contenus, étiquettes et rôles d'accessibilité | Prévu (sprint 6) |

### 3. Évolutions réalisées
Chaque évolution passe par une carte du backlog, une branche Git, des tests et une pull request. Les preuves (commits, pull requests, tests, captures) sont référencées dans le journal des problèmes et dans les comptes rendus de sprint.
