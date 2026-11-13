# Incident 001 : la génération des menus échoue car les plats dépassent le budget

- **Date :** 13 novembre 2026
- **Carte :** #25 (C21)
- **Gravité :** forte. L'utilisateur ne reçoit aucun menu.
- **Corrigé par :** pull request de la carte #14 (moteur RAG)

## 1. Résumé

Quand je lançais la génération d'un menu avec un budget de 4 € par personne (valeur par défaut), la page affichait « La génération des menus a échoué ». Le moteur refusait les plats proposés par l'IA parce qu'ils coûtaient 4,50 €, donc plus que le budget. L'incident est corrigé : le code ne montre plus à l'IA que des produits assez peu chers, et le budget est maintenant garanti par le code.

## 2. Comment l'incident a été repéré

Le terminal du serveur affichait cette ligne (l'adresse e-mail est retirée) :

```
Motif : Échec de la génération : Menu refusé après correction :
Lundi : le plat « Penne au pesto et haricots verts » coûte 4.50 €, au-dessus du budget ;
Jeudi : le plat « Nuggets de poulet et purée de lentilles corail » coûte 4.50 €, au-dessus du budget ;
Samedi : le plat « Aiguillettes de poulet et haricots verts » coûte 4.50 €, au-dessus du budget
```

Le même message est revenu à la tentative suivante, avec d'autres plats à 4,50 € (« Dés de jambon et purée de lentilles corail », « Tofu nature et haricots verts »).

## 3. Reproduction en environnement de développement

1. Lancer l'application en local (`python3 main.py`).
2. Se connecter, chercher une ville, choisir un magasin.
3. Laisser le budget par défaut (4 € par personne) et cliquer sur « Ouvrir le frigo et générer le menu ».
4. Résultat avec l'ancienne version du moteur : message d'échec à chaque essai, et la ligne de log ci-dessus dans le terminal.

Le problème était donc **reproductible à chaque essai**, pas un hasard.

## 4. Analyse des causes

- **Ce que le moteur fait :** l'IA propose des plats avec des produits de la liste. Le code recalcule le prix de chaque plat en additionnant les prix des produits, puis le compare au budget.
- **Ce que le log montre :** l'IA a proposé des plats à 4,50 €, deux fois de suite, même après qu'on lui a renvoyé l'erreur.
- **Cause identifiée :** l'IA ne respecte pas le budget quand elle doit additionner des prix. Les prix des produits sont de 1,50 €, 2,00 €, 2,50 € ou 3,00 € : deux produits peuvent donc faire 4,50 €. Le modèle utilisé est un modèle léger, moins précis sur les calculs.
- **Ce qui n'était pas la cause :** la clé de l'IA et la connexion fonctionnaient (Gemini répondait bien). Le contrôle du code, lui, fonctionnait correctement : il a refusé des plats qui étaient réellement trop chers.

## 5. Solution, étape par étape

1. **Décision :** ne pas demander à l'IA de calculer. Le budget doit être garanti par le code.
2. **Modification du code** (`IA/rag_service.py`, fonction `recuperer_produits`) : avant d'appeler l'IA, on retire les produits dont le prix dépasse la moitié du budget (`produit["prix"] > budget_max / 2`).
3. **Pourquoi ça suffit :** un plat est composé d'un plat principal et d'un accompagnement, donc de deux produits. Si chaque produit coûte au plus la moitié du budget, la somme ne peut pas dépasser le budget.
4. **Modification de la consigne donnée à l'IA :** « exactement 2 produits par plat » (au lieu de 2 ou 3), pour que ce raisonnement soit toujours vrai.
5. **Budget trop bas :** si aucun produit ne passe le filtre, le moteur renvoie le message « Pas assez de produits à ce prix dans ce magasin : augmentez le budget ».
6. **Le contrôle du code est conservé :** il vérifie toujours le prix de chaque plat, comme filet de sécurité.

## 6. Vérification

- **Test automatique** `test_plat_hors_budget_refuse` : un plat plus cher que le budget est refusé.
- **Test automatique** `test_budget_trop_bas_refuse` : avec un budget de 1 €, le moteur s'arrête avec une erreur claire.
- **Test manuel :** après la correction, la génération avec 4 € a réussi. Les plats affichent des prix de 3,00 €, 3,50 € ou 4,00 €, tous dans le budget. La recette d'un plat s'ouvre avec ses quantités.
- **Commande :** `python -m pytest` donne 13 tests verts.

## 7. Versionnement

La correction est dans la pull request de la carte #14 (moteur RAG), branche `carte-NN-moteur-rag`. Le message de commit décrit le changement.

## 8. Ce que j'en retiens et comment éviter que ça revienne

- On ne fait pas confiance à une IA pour les calculs : c'est le code qui les fait et qui les vérifie.
- On réduit les choix donnés à l'IA, pour que toute réponse possible soit valable.
- Quand un contrôle refuse une réponse, il faut lire le détail dans les logs avant de modifier quoi que ce soit.
- Une règle simple sur les prix est plus fiable qu'une consigne écrite en français dans le prompt.