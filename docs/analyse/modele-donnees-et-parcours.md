# Modélisation des données et parcours utilisateur d'Éco-Frigo

Ce document complète les user stories (`user-stories.md`). Il répond à deux exigences de la compétence C14 : la modélisation des données selon un formalisme (Merise) et la modélisation du parcours utilisateur (schéma fonctionnel).

## 1. Les données existantes

La base MongoDB `planificateur_repas_db` contient 4 collections (constat dans MongoDB Compass le 12 novembre 2026, complété par la lecture du code).

| Collection | Documents | Contenu | Champs |
|---|---|---|---|
| `users` | 1 | Les comptes | `email`, `password` (mot de passe haché avec bcrypt) |
| `produits_leclerc` | 598 | Produits issus d'Open Food Facts pour E.Leclerc | `nom`, `prix`, `rayon`, `enseigne` |
| `produits_carrefour` | 594 | Produits issus d'Open Food Facts pour Carrefour | `nom`, `prix`, `rayon`, `enseigne` |
| `menus_sauvegardes` | 112 | Les réponses déjà calculées (cache), de trois sortes | voir ci-dessous |

La collection `menus_sauvegardes` mélange trois sortes de documents, distinguées par le champ `type` :

| Valeur de `type` | Rôle | Champs |
|---|---|---|
| `stores_cache` | Magasins déjà cherchés pour une ville | `city`, `stores` (liste de `nom` et `adresse`) |
| `menu_cache` | Menu de la semaine déjà généré | `key` (magasin, budget, nombre de personnes), `enseigne` (nom du magasin), `menus` (7 jours, 2 plats par jour ; chaque plat a `nom`, `prix_par_personne`, `ingredients`, `etapes`) |
| `recipe_cache` | Recette déjà rédigée | `key` (nom du plat, nombre de personnes), `recipe` (`ingredients`, `etapes`). Les anciens documents contiennent aussi `nom`, `prix_par_personne` et `prix_total` |

## 2. Modèle conceptuel des données (MCD, méthode Merise)

[Voir le MCD d'Éco-Frigo (méthode Merise, PDF)](schemas/mcd-parcours-merise.pdf)

**Description du schéma (texte alternatif) :** le schéma comporte sept entités (rectangles) et cinq associations (ovales). Une ville regroupe un ou plusieurs magasins. Un magasin vend zéro ou plusieurs produits, chaque produit appartenant à un seul magasin. Un magasin sert de base à zéro ou plusieurs menus, chaque menu étant calculé pour un seul magasin. Un menu est composé de plats (14 : 7 jours, 2 choix par jour). Un plat peut avoir zéro ou une recette, et une recette peut servir plusieurs plats portant le même nom. L'entité UTILISATEUR n'est reliée à aucune autre.

**Lecture des cardinalités** (le premier nombre est le minimum, le second le maximum) :

| Association | Côté 1 | Côté 2 | Signification |
|---|---|---|---|
| SITUER | VILLE (1,n) | MAGASIN (1,1) | une ville a au moins un magasin ; un magasin est dans une seule ville |
| VENDRE | MAGASIN (0,n) | PRODUIT (1,1) | un magasin a 0 à n produits chargés ; un produit appartient à un seul magasin |
| CALCULER | MAGASIN (0,n) | MENU (1,1) | un magasin a 0 à n menus ; un menu est calculé pour un seul magasin |
| COMPOSER | MENU (1,n) | PLAT (1,1) | un menu contient des plats (14) ; un plat appartient à un seul menu |
| DETAILLER | PLAT (0,1) | RECETTE (1,n) | un plat a 0 ou 1 recette ; une recette peut servir plusieurs plats de même nom |

**Choix de modélisation à connaître pour l'oral :**
- **UTILISATEUR est isolé.** Les menus et les recettes ne sont pas rattachés à un compte : ce sont des caches partagés entre tous les utilisateurs, pour limiter les appels à l'IA et donc le quota. Conséquence positive pour le RGPD : les menus et les recettes ne contiennent aucune donnée personnelle. Conséquence négative : un utilisateur ne retrouve pas « ses » menus après coup. Un historique par compte serait une évolution possible (nouvelle association entre UTILISATEUR et MENU), non prévue pour l'instant.
- **Les prix d'une recette ne sont pas stockés** dans la version actuelle du code : ils sont calculés à chaque réponse à partir du prix du plat et du nombre de personnes. Les anciens documents du cache qui contiennent des prix datent d'une version précédente.
- **Les prix des produits sont estimés.** La source (Open Food Facts) ne fournit pas de prix. L'attribut `prix` est donc une valeur calculée par l'application, pas une donnée réelle. Cette limite est traitée par la user story US6.

## 3. Modèle physique : l'implémentation dans MongoDB

MongoDB est une base de documents : le modèle physique est la liste des collections et de leurs champs (section 1). Le passage du MCD au physique donne :

| Entités du MCD | Collection MongoDB | Remarque |
|---|---|---|
| UTILISATEUR | `users` | l'identifiant est l'`email` |
| PRODUIT, MAGASIN (nom) | `produits_leclerc`, `produits_carrefour` | une collection par enseigne ; le champ `enseigne` contient le nom du magasin |
| VILLE, MAGASIN (adresse) | `menus_sauvegardes` (`type` = `stores_cache`) | la ville et ses magasins sont enregistrés ensemble |
| MENU, PLAT | `menus_sauvegardes` (`type` = `menu_cache`) | les plats sont imbriqués dans le menu, par jour |
| RECETTE | `menus_sauvegardes` (`type` = `recipe_cache`) | recette imbriquée dans le document |

## 4. Constats sur le modèle actuel et évolutions prévues

| Constat | Risque | Évolution proposée |
|---|---|---|
| Compass n'affiche qu'un seul index par collection (l'index automatique sur `_id`). Rien n'empêche deux comptes avec le même email au niveau de la base : seule une vérification dans le code le fait | Deux inscriptions simultanées pourraient créer un doublon | Créer un index unique sur `users.email` |
| Les requêtes sur `menus_sauvegardes` cherchent par `type` et `key` sans index | Lenteur quand le cache grossira | Créer un index sur `type` et `key` |
| Trois sortes de documents dans une même collection | Collection peu lisible | Les conserver (simple, justifié par un même rôle de cache) ou les séparer en trois collections : à trancher au sprint 3 |
| Prix des produits estimés par l'application | Menus peu fiables | Voir US6 : chercher de vrais prix ou le dire clairement dans l'interface |
| Le cache contient des documents créés par d'anciennes versions du code (recettes avec `nom` et prix, plats dont le nom ressemble à un nom de produit) | Des résultats périmés ou incohérents sont servis depuis le cache | Vider le cache quand le moteur de menus change (sprint 3) |
| Chaque plat d'un menu stocke `ingredients` et `etapes`, mais l'interface ne les affiche pas (elle demande la recette à l'IA) | Données stockées pour rien | Les retirer, ou les utiliser comme recette de secours |

Ces évolutions deviennent des cartes du backlog (sprint 3).

## 5. Parcours utilisateur (schéma fonctionnel)

[Voir le parcours utilisateur (PDF, page du parcours)](schemas/mcd-parcours-merise.pdf)

**Description du schéma (texte alternatif) :** l'utilisateur ouvre l'application. S'il n'a pas de compte, il en crée un (US1), puis il se connecte (US2). Si ses identifiants sont faux, un message d'erreur en texte s'affiche et il recommence. Une fois connecté, il cherche les magasins de sa ville (US3), choisit un magasin, indique son foyer et son budget (US4) et lance la génération des menus (US5, US6). Si la génération échoue, un message clair lui permet de réessayer. Sinon il consulte les menus de la semaine, peut ouvrir la recette d'un plat (US7) puis revenir aux menus, et enfin se déconnecter. À tout moment après la connexion, si le jeton est refusé, la session expire et il est renvoyé à l'écran de connexion.

| Étape du parcours | User story | Écran |
|---|---|---|
| Créer un compte, se connecter | US1, US2 | Écran de connexion |
| Chercher et choisir un magasin | US3 | Écran de configuration |
| Indiquer foyer et budget | US4 | Écran de configuration |
| Générer les menus | US5, US6 | Écran de chargement puis menus |
| Consulter une recette | US7 | Fenêtre de recette |
| Session expirée | US2 | Retour à la connexion |

Les wireframes de ces écrans font l'objet de la carte suivante (#11).

## Annexe : sources des schémas

Les schémas sont générés à partir de ces textes, versionnés avec le dépôt, pour pouvoir les modifier.

  UTILISATEUR -- PRODUIT [style=invis];
  VILLE -- SITUER    [label="  1,n  "];
  SITUER -- MAGASIN  [label="  1,1  "];
  MAGASIN -- VENDRE  [label="  0,n  "];
  VENDRE -- PRODUIT  [label="  1,1  "];
  MAGASIN -- CALCULER [label="  0,n  "];
  CALCULER -- MENU   [label="  1,1  "];
  MENU -- COMPOSER   [label="  1,n  "];
  COMPOSER -- PLAT   [label="  1,1  "];
  PLAT -- DETAILLER  [label="  0,1  "];
  DETAILLER -- RECETTE [label="  1,n  "];


