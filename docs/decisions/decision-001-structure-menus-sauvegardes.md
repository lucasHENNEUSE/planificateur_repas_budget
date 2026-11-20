# Décision 001 : structure de `menus_sauvegardes` (carte #33)

**Date :** 20 novembre 2026
**Statut :** décidé

## 1. Le contexte

Ma collection MongoDB `menus_sauvegardes` contient trois sortes de documents, séparés par un champ `type`.

| Type de document | Recherche par | Contenu | Utilisé par |
|---|---|---|---|
| `menu_cache` | `key` (magasin, budget, personnes) | le menu de la semaine | `generer_menu_rag` (`rag_service.py`) |
| `stores_cache` | `city` (la ville) | la liste des magasins | route `/api/get-stores` |
| `recipe_cache` | `key` (plat, personnes) | la recette | route `/api/get-recipe` |

Ce sont trois **caches** : des copies des réponses de Gemini, gardées pour ne pas rappeler l'IA et économiser mon quota gratuit. Elles peuvent toutes être refaites à tout moment. Les autres collections (`users`, `produits_leclerc`, `produits_carrefour`) ne sont pas concernées.

## 2. Ma décision : je garde la structure actuelle

Je garde une seule collection `menus_sauvegardes`, avec le champ `type` pour distinguer les documents.

Pourquoi :
- **Ça marche déjà** : la recherche par `type` est utilisée partout dans le code et dans les tests, et je n'ai aucune modification à faire.
- **C'est simple à expliquer** : une collection pour les caches de Gemini, une pour les utilisateurs, deux pour les produits.
- **Le volume est petit** : ce sont seulement des caches, que je peux vider et refaire sans rien perdre.

Pour que le nom ne trompe pas, je précise dans la documentation que `menus_sauvegardes` est le cache des réponses de Gemini.

## 3. Conséquences pour la carte #32 (index)

- `users.email` : index unique, pour qu'on ne puisse pas créer deux comptes avec la même adresse.
- `menus_sauvegardes` : un index sur (`type`, `key`) pour les menus et les recettes, et un index sur (`type`, `city`) pour les magasins.

## 4. Quand je reverrai cette décision

Si j'ajoute d'autres types de caches, ou si la collection devient grosse, je réexaminerai sa structure.