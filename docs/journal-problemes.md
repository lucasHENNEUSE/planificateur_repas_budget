# Journal des problèmes et solutions

## 1. Push refusé (non-fast-forward)
- **Date :** 10 novembre 2026
- **Contexte :** après le commit du .gitignore, `git push` refusé.
- **Cause :** GitHub avait 2 commits que mon ordinateur n'avait pas (fichier de veille créé depuis le site).
- **Solution :** `git pull --rebase` puis `git push`.
- **Ce que j'ai appris :** toujours récupérer avant de pusher.

## 2. Application qui plante sans SECRET_KEY
- **Date :** 10 novembre 2026
- **Contexte :** après la carte #7, `pytest` s'arrête avec « SECRET_KEY manquante ».
- **Cause :** la variable avait un autre nom dans mon .env.
- **Solution :** renommer la variable. Le plantage est voulu : mieux vaut un arrêt qu'une clé connue de tous.

## 3. Test qui dépend de la base de données
- **Date :** 10 novembre 2026
- **Contexte :** `test_generation_menu_avec_mock` échoue (mock appelé 0 fois).
- **Cause :** la vraie base MongoDB renvoie un menu en cache, donc l'IA n'est jamais appelée.
- **Solution :** à compléter à la carte tests, sprint 3

## 4. Interface Feedly inadaptée
- **Date :** 9 novembre 2026
- **Contexte :** Feedly proposait une offre orientée cybersécurité, payante après 30 jours.
- **Solution :** choix d'Inoreader (gratuit, flux RSS).
