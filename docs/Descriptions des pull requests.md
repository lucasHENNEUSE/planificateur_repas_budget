# Descriptions des pull requests (cartes terminées)
 
Chaque description est à coller dans la pull request correspondante sur GitHub. La ligne `Closes #N` ferme la carte toute seule quand la pull request est fusionnée.
 
---
 
## Carte #5 : Fixer le créneau de veille et faire la première synthèse (C6)
 
```
Ajoute la première synthèse de veille technologique.
 
- Le créneau est fixé : le samedi de 14h à 16h.
- La synthèse (veille/2026-11-09.md) contient 3 informations, 1 information écartée avec la raison, un tableau de fiabilité des sources et les décisions prises pour le projet.
- Les informations ont été vérifiées sur des sources officielles (Google, EUR-Lex).
 
Pour vérifier : ouvrir veille/2026-11-09.md.
 
Closes #5
```
 
## Carte #6 : Ajouter logs/, mlflow.db et .env au .gitignore (C20)
 
```
Empêche les fichiers sensibles ou générés d'être envoyés sur GitHub.
 
- Le fichier .gitignore contient maintenant : .env, .venv/, __pycache__/, *.pyc, .pytest_cache/, .coverage, htmlcov/, logs/, *.log, mlflow.db, mlruns/ et .vscode/.
- Les fichiers qui étaient déjà suivis par Git ont été retirés du suivi (git rm -r --cached), sans être supprimés de mon ordinateur.
 
Pourquoi : le fichier .env contient des clés secrètes, et les logs contiennent des adresses e-mail.
 
Pour vérifier : git status ne doit plus montrer .env, logs/ ni mlflow.db.
 
Closes #6
```
 
## Carte #7 : Rendre SECRET_KEY obligatoire (C9)
 
```
Supprime la valeur par défaut de la clé qui signe les jetons de connexion.
 
- Avant : si la clé manquait, l'application utilisait une clé écrite dans le code, donc connue de tous.
- Maintenant : si SECRET_KEY manque dans le fichier .env, l'application refuse de démarrer et affiche « SECRET_KEY manquante : ajoute-la dans le fichier .env ».
 
Pourquoi : un secret écrit dans le code permet à n'importe qui de fabriquer un faux jeton de connexion (règle OWASP).
 
Pour vérifier : retirer SECRET_KEY du .env et lancer python3 main.py : l'application s'arrête avec ce message.
 
Closes #7
```
 
## Carte #8 : Protéger get-stores, get-recipe et modify-recipe par JWT (C9)
 
```
Toutes les routes qui appellent l'IA demandent maintenant un jeton de connexion valide.
 
- Les routes get-stores, generate-menus, get-recipe et modify-recipe sont protégées (Depends(verify_token)).
- Sans jeton, ou avec un jeton refusé, le serveur répond 401 ou 403.
- Le site envoie le jeton à chaque demande. Si le jeton est refusé, l'utilisateur est déconnecté et un message l'invite à se reconnecter.
- Quatre tests automatiques vérifient que les routes sont bloquées sans jeton.
 
Pourquoi : sans protection, n'importe qui pouvait consommer mon quota d'IA gratuit.
 
Pour vérifier : lancer python -m pytest (les tests de sécurité passent) et appeler une route sans jeton (réponse 401 ou 403).
 
Closes #8
```
 
## Carte #9 : Écrire les user stories avec critères d'acceptation et d'accessibilité (C14)
 
```
Ajoute les user stories du projet : docs/analyse/user-stories.md.
 
- 11 user stories (US1 à US11), chacune avec ses critères d'acceptation.
- Un tableau de 8 critères d'accessibilité (WCAG 2.1 AA) et les écarts connus de l'interface.
- Un état d'avancement pour chaque story (fait, partiel, à faire).
 
Pour vérifier : ouvrir docs/analyse/user-stories.md.
 
Closes #9
```
 
## Carte #10 : Dessiner le MCD (Merise) et les parcours utilisateurs (C14)
 
```
Ajoute la modélisation des données et le parcours utilisateur : docs/analyse/modele-donnees-et-parcours.md.
 
- Un inventaire des 4 collections MongoDB, vérifié dans MongoDB Compass.
- Un MCD Merise avec 7 entités, 5 associations et un tableau des cardinalités.
- Le passage au modèle physique MongoDB.
- Un parcours utilisateur avec les boucles d'erreur (mauvais identifiants, échec de génération, session expirée).
- Des constats sur la base actuelle et des évolutions prévues (index, structure du cache, prix estimés).
- Un texte alternatif pour chaque schéma.
 
Pour vérifier : ouvrir docs/analyse/modele-donnees-et-parcours.md et les images dans docs/analyse/schemas/.
 
Closes #10
```
 
## Carte #11 : Faire les wireframes des écrans (C14)
 
```
Ajoute le document des écrans de l'interface : docs/analyse/wireframes.md.
 
- 8 captures réelles de l'interface, annotées avec des repères numérotés.
- Pour chaque écran : les exigences d'accessibilité (WCAG 2.1 AA) et ce qui est constaté.
- Les contrastes sont calculés. L'adresse e-mail visible sur une capture est floutée.
- Une section sur les limites : pas encore de test avec un lecteur d'écran, ni de zoom à 200 %.
 
Pour vérifier : ouvrir docs/analyse/wireframes.md.
 
Closes #11
```
 
## Carte #14 : Décider et implémenter le vrai RAG (récupération puis génération) (C9)
 
```
Remplace l'ancien moteur de menus, qui collait des noms de produits, par un vrai RAG.
 
Le moteur fonctionne en 3 temps :
1. Récupérer : on choisit dans MongoDB des produits réels du magasin, avec leur prix. On ne garde que les produits à moins de la moitié du budget.
2. Générer : un seul appel à Gemini compose les plats de la semaine avec ces produits.
3. Contrôler : le code vérifie que les produits existent et recalcule lui-même le prix de chaque plat. Si l'IA se trompe, on lui renvoie ses erreurs pour une seule correction.
 
Aussi dans cette pull request :
- Réessai automatique (3 fois) quand Gemini répond « surchargé » (erreur 503).
- Si l'IA échoue, une erreur est affichée et aucune fausse recette n'est enregistrée.
- Le cache est versionné (clés « v2 ») : les anciens menus sont ignorés.
- 6 nouveaux tests (test_rag.py) ; le test de génération n'a plus besoin de la vraie base.
 
Pour vérifier : python -m pytest (13 tests verts), puis générer un menu avec un budget d'au moins 4 €.
 
Closes #14
```
 
## Carte #23 : Corriger le front (XSS, accessibilité) (C17)
 
```
Rend l'interface plus sûre et plus accessible.
 
Sécurité :
- Les textes venant de l'IA (noms de plats) sont affichés comme du texte simple : plus de risque d'injection de code (XSS).
 
Accessibilité :
- Chaque champ a une étiquette visible reliée.
- Les messages d'erreur et de résultat sont annoncés aux lecteurs d'écran.
- Les boutons « + » et « - » et les boutons « Voir la recette » ont un nom clair.
- La fenêtre de recette se ferme avec la touche Échap et garde le focus.
- Le cadre de focus au clavier est toujours visible.
- Les couleurs sont plus foncées (contraste d'au moins 4,5:1).
 
Nouveautés d'usage :
- Un bouton « Réessayer » apparaît quand la génération échoue.
- Le bouton « Valider et créer la liste de courses » est grisé avec une explication, car il n'existe pas encore.

**Carte #11 : captures annotées**
```
Ajoute le document des écrans de l'interface : 8 captures réelles annotées, avec les exigences d'accessibilité (WCAG 2.1 AA) et ce qui est constaté sur chaque écran.
Les contrastes sont calculés. L'adresse e-mail visible sur une capture est floutée.
 
Closes #11
```
 
**Carte « Accessibilité de l'interface »**
```
Rend l'interface plus accessible : étiquettes reliées aux champs, messages d'erreur annoncés, noms sur les boutons, fenêtre de recette utilisable au clavier (touche Échap), cadre de focus visible, couleurs plus contrastées, bouton « Réessayer » en cas d'échec.
Les textes venant de l'IA sont affichés comme du texte simple.
 
Closes #NN
```
 
**Carte « Moteur de menus RAG avec Gemini »**
```
Remplace l'ancien moteur (qui collait des noms de produits) par un vrai RAG : produits récupérés dans MongoDB, plats composés par Gemini, produits et prix contrôlés par le code.
Ajoute un réessai automatique en cas d'erreur 503 de Gemini.
Si l'IA échoue, une erreur est affichée et aucune fausse recette n'est enregistrée.
Ajoute 6 tests (test_rag.py) et corrige le test de génération qui dépendait de la base.
 
Closes #NN

## Carte #25 : Incident 

   Incident documenté dans docs/incidents/incident-001-plats-hors-budget.md.
   Cause : l'IA calcule mal les prix (plats à 4,50 € pour un budget de 4 €).
   Solution : le code retire les produits trop chers avant l'appel à l'IA. Corrigé dans la PR de la carte #14.