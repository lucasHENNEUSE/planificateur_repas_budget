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
- **Contexte :** `test_generation_menu_avec_mock` échoue sur mon ordinateur (le mock est appelé 0 fois), mais il passe dans la CI GitHub.
- **Cause :** la route renvoie un menu déjà enregistré dans le cache MongoDB. Sur mon ordinateur, la base contient déjà ce menu : l'IA n'est donc jamais appelée. Dans la CI, la base est neuve et vide : le cache est vide et le mock est appelé. Le test dépend de l'état de la base, ce qui est un défaut de conception du test.
- **Solution :** [à compléter au sprint 3 : simuler aussi la base avec un mock, comme pour `test_recherche_magasin`]
- **Ce que j'ai appris :** un test fiable doit donner le même résultat partout. Une CI verte ne prouve pas que les tests sont bons.

## 4. Interface Feedly inadaptée
- **Date :** 9 novembre 2026
- **Contexte :** Feedly proposait une offre orientée cybersécurité, payante après 30 jours.
- **Solution :** choix d'Inoreader (gratuit, flux RSS).

  ## 5. Fichiers générés suivis par Git
- **Date :** 10 novembre 2026
- **Contexte :** `git ls-files` montrait des dossiers `__pycache__`, le fichier de logs et `mlflow.db` dans le dépôt.
- **Cause :** mon `.gitignore` n'avait que 3 lignes et avait été créé après les premiers commits. Un `.gitignore` n'enlève pas ce que Git suit déjà.
- **Risque :** le fichier de logs contenait un email réel (donnée personnelle, RGPD).
- **Solution :** compléter le `.gitignore`, puis `git rm -r --cached` sur les fichiers concernés. Vérification : `git ls-files` ne les liste plus. `.env` n'avait jamais été suivi, donc aucune clé n'a été exposée.
- **Ce que j'ai appris :** le `.gitignore` se prépare avant le premier commit. L'email reste visible dans l'ancien historique, d'où la carte d'anonymisation des logs.

## 6. Routes appelant l'IA sans authentification
- **Date :** 10 novembre 2026
- **Contexte :** en relisant mon code, j'ai vu que `get-stores`, `get-recipe` et `modify-recipe` n'exigeaient pas de jeton.
- **Risque :** n'importe qui pouvait consommer mon quota gratuit Gemini (OWASP API : accès non contrôlé).
- **Solution :** ajout de `Depends(verify_token)` sur les trois routes, passage de `async def` à `def` (appels bloquants), fonction front unique `appelerApi` qui envoie le jeton et déconnecte l'utilisateur si le jeton est refusé.
- **Preuves :** 3 tests « sans jeton refusé », test d'expiration manuel (capture dans `docs/preuves/`), pull request #8.
- **Ce que j'ai appris :** une route qui coûte de l'argent ou du quota doit être protégée par défaut.

## 7. Erreurs 404 dans la console au lancement
- **Date :** 10 novembre 2026
- **Contexte :** `GET /.well-known/appspecific/com.chrome.devtools.json 404` au démarrage.
- **Cause :** Chrome demande ce fichier quand ses outils de développement sont ouverts. Mon site ne le propose pas.
- **Solution :** aucune, l'application fonctionne normalement.
- **Ce que j'ai appris :** lire un message d'erreur en entier avant de conclure à un bug.
