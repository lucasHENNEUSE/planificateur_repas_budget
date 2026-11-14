# Choix techniques d'Éco-Frigo (carte #13, C15)

Ce document explique pourquoi chaque outil a été choisi, ce qui a été écarté, et ce que le choix limite. Il complète le document d'architecture (carte #12).

## 1. Les contraintes du projet

Chaque choix part de ces contraintes :

| Contrainte | Conséquence sur les choix |
|---|---|
| Budget nul : projet personnel, aucun abonnement payant | Outils gratuits ou avec offre gratuite |
| Développeur débutant, code à expliquer à l'oral | Outils simples, peu de code, documentation claire |
| Application lancée en local (pas d'hébergement payant) | Pas d'infrastructure lourde |
| Données personnelles (email, mot de passe) | Authentification sécurisée, secrets hors du code |
| Résultats de l'IA parfois faux (voir incident #001) | Contrôle par du code, tests automatiques |
| Interface utilisable par tous (accessibilité) | Page HTML standard, contrôlable avec les outils du navigateur |

## 2. Les choix, un par un

### Langage et serveur : Python et FastAPI

- **Besoin** : un serveur qui reçoit des demandes de l'interface et répond en JSON.
- **Pourquoi** : Python est lisible et adapté à l'IA. FastAPI demande peu de code (une route = une fonction), vérifie automatiquement les données reçues grâce à Pydantic, et génère une documentation de l'API toute seule.
- **Écarté** : Django (plus complet mais plus lourd à apprendre pour ce besoin), Flask (aussi simple, mais sans vérification automatique des données).
- **Limite** : FastAPI est plus récent, avec moins de tutoriels que Flask ou Django.

### Interface : HTML, CSS et JavaScript simples

- **Besoin** : une page où l'utilisateur se connecte, règle son budget et lit ses menus.
- **Pourquoi** : le navigateur comprend directement ces langages, sans outil à installer. Une seule page (`index.html`), servie par FastAPI. C'est le bon niveau pour un projet débutant et c'est facile à tester pour l'accessibilité.
- **Écarté** : un framework comme React ou Vue (installation et notions supplémentaires pour une seule page), une interface écrite en Python (moins adaptée au navigateur).
- **Limite** : la page est un seul fichier assez long. Si l'interface grandit, il faudra la découper.

### Base de données : MongoDB

- **Besoin** : stocker des comptes, des produits de magasins (nombre variable de champs) et des menus.
- **Pourquoi** : MongoDB stocke des documents proches du JSON, donc proches de ce que l'API échange. Pas besoin de définir toutes les tables à l'avance. Les produits d'Open Food Facts n'ont pas tous les mêmes champs : cette souplesse est utile.
- **Écarté** : SQLite ou PostgreSQL (bien adaptés, mais les produits très variables demandent plus de préparation).
- **Limite** : moins de contrôle strict sur la forme des données. D'où les cartes #32 (index) et #33 (structure des menus).

### Intelligence artificielle : API Gemini (Google)

- **Besoin** : composer des menus, rédiger des recettes, retrouver les magasins d'une ville.
- **Pourquoi** : l'offre gratuite suffit pour le projet. Gemini peut répondre directement en JSON, ce qui évite de « lire » du texte libre. Un modèle léger (« flash-lite ») est assez rapide pour l'usage.
- **Écarté** : des modèles payants ou hébergés soi-même (coût ou matériel nécessaire).
- **Limite** : quota gratuit limité, service parfois surchargé (erreur 503), réponses parfois fausses. C'est pourquoi le code réessaie, contrôle chaque menu et affiche un message clair en cas d'échec (cartes #26 et #27).

### Principe RAG : l'IA compose, le code contrôle

- **Besoin** : des menus avec de vrais produits et de vrais prix.
- **Pourquoi** : l'IA ne reçoit que des produits pris dans la base. Le code vérifie que les produits existent, recalcule les prix et refuse les menus hors budget. L'incident #001 (plats à 4,50 € acceptés) a montré qu'il ne faut pas faire confiance à l'IA seule.
- **Écarté** : laisser l'IA inventer menus et prix librement.
- **Limite** : les prix des plats sont estimés, car les produits n'ont pas de prix réels.

### Source des produits : Open Food Facts

- **Besoin** : un catalogue de produits de supermarché.
- **Pourquoi** : base ouverte et gratuite, accessible par API, sans clé.
- **Écarté** : le site des magasins (accès non prévu, données protégées).
- **Limite** : données collectées par des bénévoles, prix absents ou incomplets.

### Sécurité : JWT et bcrypt

- **Besoin** : protéger les routes et les mots de passe.
- **Pourquoi** : bcrypt stocke uniquement une empreinte du mot de passe, jamais le mot de passe. Le jeton JWT prouve que l'utilisateur s'est connecté, sans stocker de session sur le serveur. Il expire après 2 heures. Les clés secrètes sont dans le fichier `.env`, hors de Git.
- **Écarté** : stocker les mots de passe en clair (interdit), des sessions serveur (plus de code à gérer).
- **Limite** : le jeton ne peut pas être annulé avant son expiration. Pas encore de double authentification.

### Suivi : logs et MLflow

- **Besoin** : savoir si l'IA répond, en combien de temps, et repérer les échecs.
- **Pourquoi** : MLflow enregistre durée et réussite de chaque génération, sans serveur à installer (fichier local). Le journal `logs/api_eco_frigo.log` garde les alertes.
- **Écarté** : outils de supervision complets (trop lourds pour un projet local).
- **Limite** : suivi limité à la machine du développeur (carte #18 pour le tableau de bord et les alertes).

### Tests et intégration continue : Pytest et GitHub Actions

- **Besoin** : vérifier que le code fonctionne après chaque changement.
- **Pourquoi** : Pytest est simple à lire et permet de remplacer Gemini et la base par de fausses réponses, donc des tests rapides et gratuits. GitHub Actions lance les tests à chaque pull request, directement dans le dépôt.
- **Écarté** : tests manuels uniquement (trop longs, trop d'oublis).
- **Limite** : les tests ne couvrent pas encore toutes les routes (cartes #15 et #16).

### Organisation : Git, GitHub, Scrum allégé

- **Besoin** : suivre le travail et garder l'historique.
- **Pourquoi** : une branche et une pull request par carte, avec le numéro de la carte dans le message. Le tableau GitHub Projects montre l'avancement sprint par sprint.
- **Limite** : projet à une seule personne, donc pas de relecture croisée de code.

### À venir : Docker

- **Besoin** : lancer l'application de la même façon sur n'importe quelle machine.


## 3. Résumé

| Domaine | Choix | Raison principale |
|---|---|---|
| Serveur | Python + FastAPI | Simple, peu de code, vérification automatique des données |
| Interface | HTML, CSS, JavaScript | Compris directement par le navigateur, une seule page |
| Base de données | MongoDB | Documents proches du JSON, produits variables |
| IA | Gemini | Offre gratuite, réponse en JSON |
| Fiabilité de l'IA | RAG + contrôle par le code | L'IA peut se tromper |
| Produits | Open Food Facts | Ouvert, gratuit |
| Sécurité | JWT + bcrypt | Standard, pas de mot de passe stocké en clair |
| Suivi | Logs + MLflow | Léger, local |
| Tests | Pytest + GitHub Actions | Rapide, automatique |