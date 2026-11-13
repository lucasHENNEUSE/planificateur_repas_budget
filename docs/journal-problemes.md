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



....................................................................................


### Problème 1 : les menus et les recettes étaient de mauvaise qualité
 
- **Ce que j'ai vu :** les plats ressemblaient à des noms de produits collés ensemble, par exemple « Herta knacki veggie saucisses x6 -210g et son accompagnement de boulgour ». Les recettes avaient toujours les mêmes quatre phrases.
- **Cause :** le moteur ne faisait pas appel à l'IA. Il prenait deux noms de produits et les collait. Les prix venaient d'une formule, ils étaient inventés. De plus, quand l'IA échouait pour une recette, une fausse recette était enregistrée et resservie ensuite.
- **Solution :** le moteur de menus fonctionne maintenant en trois temps. D'abord, on choisit des produits réels du magasin dans la base. Ensuite, l'IA (Gemini) compose les plats avec ces produits. Enfin, le code vérifie que les produits existent et recalcule le prix lui-même. Si l'IA échoue, on affiche une erreur et on n'enregistre plus de fausse recette.
- **Preuve :** 6 nouveaux tests automatiques vérifient ce contrôle (produit inventé refusé, plat trop cher refusé, une correction demandée à l'IA, rien enregistré si l'IA ne répond pas).
- **Ce que j'en retiens :** on ne doit jamais faire confiance à une réponse d'IA sans la contrôler.
### Problème 2 : la clé de l'IA était refusée
 
- **Ce que j'ai vu :** le message « API key not valid » dans le terminal, et les menus ne se généraient plus.
- **Cause :** la variable `GOOGLE_API_KEY` du fichier `.env` contenait une mauvaise valeur : une ancienne clé secrète collée sous le mauvais nom. Ce n'était pas une clé Google.
- **Solution :** une nouvelle clé a été créée dans Google AI Studio et mise dans `.env`. Pour vérifier sans l'afficher, on affiche seulement ses 4 premiers caractères.
- **Autre point :** la ligne `SECRET_KEY` avait disparu du fichier, et l'application a refusé de démarrer. C'est voulu : cela évite de lancer le site sans clé de sécurité. La ligne a été recréée avec une valeur aléatoire.
- **Ce que j'en retiens :** je ne montre jamais le contenu de `.env`, ni dans un message ni dans une capture.
### Problème 3 : Google répondait « modèle surchargé » (erreur 503)
 
- **Ce que j'ai vu :** « 503 UNAVAILABLE : le modèle subit une forte demande ».
- **Cause :** une surcharge temporaire chez Google. Ce n'était pas une erreur de mon code ni de ma clé.
- **Solution :** l'application réessaie toute seule jusqu'à 3 fois, avec 3 secondes d'attente, mais seulement pour cette erreur. Les autres erreurs (clé, quota) ne sont pas répétées, pour ne pas gaspiller le quota gratuit. Un modèle plus léger de la même famille, `gemini-3.5-flash-lite`, a aussi été testé et a fonctionné.
- **Ce que j'en retiens :** un service externe peut tomber en panne. Il faut prévoir un nouvel essai et un message clair.
### Problème 4 : l'IA proposait des plats trop chers
 
- **Ce que j'ai vu :** « Menu refusé : le plat coûte 4.50 €, au-dessus du budget » (budget de 4 €), deux fois de suite.
- **Cause :** l'IA calcule mal les additions. Mon contrôle a bien refusé les plats, mais la génération échouait.
- **Solution :** avant d'appeler l'IA, le code retire les produits trop chers : un produit ne doit pas dépasser la moitié du budget. Comme un plat = 1 plat principal + 1 accompagnement, toute combinaison respecte alors le budget. C'est le code qui garantit le budget, pas l'IA.
- **Petit incident :** une mise à jour de fichier n'avait pas été faite et l'ancienne version tournait encore. On l'a repéré avec la commande `grep`, qui cherche une ligne dans un fichier.
- **Ce que j'en retiens :** je laisse le code faire les calculs, et je vérifie toujours que le bon fichier est en place.
### Problème 5 : des informations privées visibles dans des captures
 
- **Ce que j'ai vu :** mon adresse e-mail apparaissait sur une capture d'écran, et le contenu du fichier `.env` sur une autre.
- **Solution :** l'e-mail est flouté dans le document. La clé visible a été remplacée. Nouvelle règle : fermer `.env` avant une capture et utiliser un compte de test.
- **Suite :** une carte est prévue pour ne plus écrire les e-mails en clair dans les logs.
### Problème 6 : l'interface n'était pas accessible
 
- **Ce que j'ai vu :** en relisant `index.html`, les champs n'avaient pas d'étiquette, les messages d'erreur n'étaient pas annoncés aux lecteurs d'écran, les boutons « + » et « - » n'avaient pas de nom, et la fenêtre de recette ne gérait pas le clavier.
- **Solution :** étiquettes ajoutées, messages annoncés, noms ajoutés sur les boutons, fenêtre de recette fermée avec la touche Échap, cadre de focus visible, couleurs plus foncées pour le contraste. Les textes de l'IA sont aussi affichés comme du texte simple (plus de risque d'injection de code).
- **Preuve :** captures annotées dans `docs/analyse/wireframes.md`.
