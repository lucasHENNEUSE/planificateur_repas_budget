# Spécifications fonctionnelles : user stories d'Éco-Frigo

## 1. Contexte

Éco-Frigo est une application web qui aide un foyer à planifier ses repas de la semaine selon un budget. L'utilisateur choisit un magasin dans sa ville, indique la composition de son foyer et son budget par personne. L'application propose des menus pour les 7 jours, avec deux choix par jour, et la recette de chaque plat. Une intelligence artificielle (Gemini) aide à trouver les magasins et à rédiger les recettes.

**Acteurs :**
- **Utilisateur :** une personne qui prépare les repas de son foyer.
- **Propriétaire :** la personne qui gère l'application, qui doit protéger le service et son quota d'IA.
- **Équipe technique :** la personne qui surveille le fonctionnement (suivi des appels à l'IA, journaux, alertes).

**Statuts :** Existant (déjà dans l'application), Partiel (existe mais à améliorer), À faire.

## 2. Objectifs d'accessibilité

Standard retenu : **WCAG 2.1 niveau AA**, le standard international sur lequel s'appuie le **RGAA** (référentiel français). Chaque numéro est une règle précise et vérifiable. Dans chaque user story, les critères d'accessibilité font partie des critères d'acceptation : une story n'est pas terminée tant qu'ils ne sont pas respectés.

Seuls les critères utilisés dans les stories sont listés ici :

| Critère WCAG | Règle | Ce que ça veut dire pour Éco-Frigo |
|---|---|---|
| 1.3.1 | Information et relations | Chaque champ est relié à son étiquette ; les titres sont de vrais titres |
| 1.4.1 | Utilisation de la couleur | Aucune information n'est portée uniquement par la couleur |
| 1.4.3 | Contraste minimum | Texte lisible (contraste d'au moins 4,5 pour 1) |
| 2.1.1 | Clavier | Toutes les actions sont possibles sans souris |
| 2.4.3 | Parcours du focus | L'ordre de navigation au clavier est logique |
| 3.3.1 | Identification des erreurs | Une erreur est décrite par un texte |
| 4.1.2 | Nom, rôle, valeur | Chaque bouton ou fenêtre a un nom et un rôle compris par un lecteur d'écran |
| 4.1.3 | Messages d'état | Les messages de chargement ou de résultat sont annoncés sans déplacer le focus |

**Écarts connus dans l'interface actuelle** (à corriger au sprint 6, carte « Corriger le front ») : champs de connexion repérés seulement par un texte d'exemple, boutons « + » et « − » sans nom accessible, fenêtre de recette sans rôle de boîte de dialogue, messages d'erreur affichés par des fenêtres d'alerte, chargement non annoncé.

## 3. User stories

### US1 : Créer un compte
- **Statut :** Existant. **Priorité :** haute.
- **En tant qu'**utilisateur, **je veux** créer un compte avec mon email et un mot de passe, **afin de** pouvoir utiliser l'application de manière sécurisée.
- **Contexte :** l'accès aux fonctions d'IA est réservé aux personnes connectées.
- **Scénario nominal :** je saisis un email valide et un mot de passe d'au moins 6 caractères, je valide, et l'application confirme que le compte est créé.
- **Scénarios d'erreur :** email vide ou mot de passe trop court, message d'erreur ; email déjà utilisé, message « Cet utilisateur existe déjà ».
- **Critères de validation :**
  - un compte avec un email déjà présent est refusé ;
  - le mot de passe est stocké haché, jamais en clair ;
  - un mot de passe de moins de 6 caractères est refusé.
- **Accessibilité :**
  - chaque champ a une étiquette visible reliée au champ (1.3.1) ;
  - les messages d'erreur sont écrits en texte (3.3.1) ;
  - le formulaire s'utilise entièrement au clavier (2.1.1).

### US2 : Se connecter et se déconnecter
- **Statut :** Existant. **Priorité :** haute.
- **En tant qu'**utilisateur, **je veux** me connecter et me déconnecter, **afin de** protéger l'accès à mon compte.
- **Contexte :** la connexion donne un jeton temporaire, valable 2 heures.
- **Scénario nominal :** je saisis mes identifiants, l'écran de configuration s'affiche ; « Se déconnecter » supprime le jeton et me ramène à l'écran de connexion.
- **Scénarios d'erreur :** identifiants incorrects, message « Identifiants incorrects » ; jeton expiré ou invalide pendant l'utilisation, message « Session expirée » et retour à l'écran de connexion.
- **Critères de validation :**
  - un identifiant ou un mot de passe faux ne donne pas de jeton ;
  - un jeton modifié ou expiré est refusé par l'API ;
  - après déconnexion, les actions protégées ne sont plus possibles.
- **Accessibilité :**
  - chaque champ a une étiquette reliée (1.3.1) ;
  - le formulaire s'utilise au clavier (2.1.1) ;
  - le message « Session expirée » est annoncé par un lecteur d'écran (4.1.3).

### US3 : Rechercher un magasin
- **Statut :** Existant. **Priorité :** haute.
- **En tant qu'**utilisateur connecté, **je veux** chercher les magasins d'une ville, **afin de** choisir l'enseigne où je fais mes courses.
- **Contexte :** l'application propose des magasins E.Leclerc et Carrefour. L'IA les cherche ; les résultats sont gardés en cache.
- **Scénario nominal :** je tape « Brest », je clique sur « Chercher », et une liste de magasins avec adresse s'affiche.
- **Scénarios d'erreur :** ville vide, message d'invitation ; IA indisponible ou quota atteint, des magasins par défaut sont proposés et un message le précise.
- **Critères de validation :**
  - la route refuse une requête sans jeton valide ;
  - seules les enseignes E.Leclerc et Carrefour sont proposées ;
  - une ville déjà recherchée est servie depuis le cache, sans nouvel appel à l'IA.
- **Accessibilité :**
  - le champ « Ville » a une étiquette reliée (1.3.1) ;
  - la liste des magasins se parcourt au clavier (2.1.1) ;
  - « Recherche en cours » puis le nombre de résultats sont annoncés (4.1.3).

### US4 : Indiquer mon foyer et mon budget
- **Statut :** Existant. **Priorité :** haute.
- **En tant qu'**utilisateur, **je veux** indiquer le nombre d'adultes, d'enfants et mon budget par personne, **afin d'** obtenir des menus adaptés.
- **Scénario nominal :** j'ajuste les compteurs, je saisis un budget (par exemple 4,00 €), et je lance la génération.
- **Scénarios d'erreur :** budget inférieur à 1 €, ou aucun adulte.
- **Critères de validation :**
  - au moins 1 adulte, 0 enfant ou plus ;
  - budget minimum de 1 € par personne ;
  - le total de personnes est calculé à partir des deux compteurs.
- **Accessibilité :**
  - les boutons « + » et « − » ont un nom accessible, par exemple « Ajouter un adulte » (4.1.2) ;
  - les compteurs s'utilisent au clavier (2.1.1).

### US5 : Générer les menus de la semaine
- **Statut :** Partiel (génération à base de règles, voir US6). **Priorité :** haute.
- **En tant qu'**utilisateur connecté, **je veux** obtenir des menus pour les 7 jours, avec deux choix par jour, **afin de** planifier mes repas.
- **Contexte :** la génération s'appuie sur les produits du magasin choisi. Un menu déjà calculé pour les mêmes paramètres est repris depuis le cache.
- **Scénario nominal :** je lance la génération, un message de chargement s'affiche, puis un menu par jour avec nom du plat et prix par personne.
- **Scénarios d'erreur :** service d'IA indisponible ou quota atteint, message clair et possibilité de réessayer ; session expirée, retour à la connexion.
- **Critères de validation :**
  - 7 jours présents, avec 2 options chacun ;
  - la route refuse une requête sans jeton valide ;
  - chaque appel à l'IA est mesuré (durée, succès) dans le suivi ;
  - une demande identique est servie depuis le cache.
- **Accessibilité :**
  - le chargement est annoncé (4.1.3) ;
  - chaque jour est un vrai titre (1.3.1) ;
  - les prix ont un contraste suffisant (1.4.3).

### US6 : Respecter mon budget avec des prix fiables
- **Statut :** À faire. **Priorité :** haute.
- **En tant qu'**utilisateur, **je veux** que chaque plat respecte mon budget avec des prix issus de données connues, **afin de** pouvoir faire confiance aux menus.
- **Contexte :** aujourd'hui, les prix du catalogue sont estimés (la source des produits n'en fournit pas) et le prix d'un plat est ajusté lorsqu'il sort du budget. Cette fonction sera revue au sprint 3.
- **Scénario nominal :** je demande 4 € par personne et tous les plats affichés coûtent au plus 4 €, avec le prix réellement calculé.
- **Scénario d'erreur :** aucun plat ne respecte le budget, un message l'indique et propose de l'augmenter.
- **Critères de validation :**
  - le prix affiché n'est jamais modifié pour le faire entrer dans le budget ;
  - un test automatique vérifie que chaque plat respecte le budget ;
  - la provenance des prix est documentée.
- **Accessibilité :**
  - le message d'impossibilité est écrit en texte (3.3.1) ;
  - un dépassement de budget n'est pas signalé par la couleur seule (1.4.1).

### US7 : Consulter la recette d'un plat
- **Statut :** Existant. **Priorité :** moyenne.
- **En tant qu'**utilisateur connecté, **je veux** voir les ingrédients et les étapes d'un plat, **afin de** le cuisiner.
- **Scénario nominal :** je clique sur « Voir la recette », une fenêtre affiche les ingrédients, les étapes et le coût par personne.
- **Scénarios d'erreur :** IA indisponible, une recette par défaut est proposée avec un message ; session expirée, retour à la connexion.
- **Critères de validation :**
  - la route refuse une requête sans jeton valide ;
  - une recette déjà générée est servie depuis le cache ;
  - le prix par personne et le prix total sont affichés.
- **Accessibilité :**
  - la fenêtre a le rôle de boîte de dialogue et un titre (4.1.2) ;
  - le focus entre dans la fenêtre et revient au bouton à la fermeture (2.4.3) ;
  - la touche Échap ferme la fenêtre (2.1.1).

### US8 : Adapter une recette à ma demande
- **Statut :** À faire (la route existe mais renvoie un texte fixe). **Priorité :** basse.
- **En tant qu'**utilisateur connecté, **je veux** demander une modification de recette (par exemple « sans lactose »), **afin de** l'adapter à mon foyer.
- **Scénario nominal :** je saisis ma demande, la recette est réécrite et affichée.
- **Critères de validation :**
  - la recette modifiée tient compte de la demande ;
  - la route est protégée par jeton ;
  - les appels sont mesurés dans le suivi.
- **Accessibilité :**
  - le champ de demande a une étiquette reliée (1.3.1) ;
  - le résultat est annoncé (4.1.3).

### US9 : Obtenir ma liste de courses
- **Statut :** À faire (le bouton existe mais n'a pas d'action). **Priorité :** basse.
- **En tant qu'**utilisateur, **je veux** une liste de courses issue des menus choisis, **afin de** faire mes achats.
- **Scénario nominal :** je clique sur « Liste de courses » et je vois les ingrédients des plats choisis, regroupés, avec un total estimé.
- **Critères de validation :**
  - la liste regroupe les ingrédients des plats choisis, sans doublon ;
  - un total estimé est affiché.
- **Accessibilité :**
  - la liste est une vraie liste (1.3.1) ;
  - le bouton et la liste s'utilisent au clavier (2.1.1).

### US10 : Protéger l'accès à l'IA
- **Statut :** Existant (réalisé au sprint 1). **Priorité :** haute.
- **En tant que** propriétaire, **je veux** que seules les personnes connectées puissent déclencher les fonctions d'IA, **afin de** protéger mon quota et les données.
- **Critères de validation :**
  - les routes de recherche de magasins, de menus et de recettes refusent toute requête sans jeton valide (tests automatiques) ;
  - la clé secrète des jetons vient de l'environnement et l'application refuse de démarrer sans elle ;
  - aucun secret n'est présent dans le dépôt.
- **Accessibilité :** non applicable (fonction sans interface).

### US11 : Suivre le fonctionnement et être alerté
- **Statut :** Partiel (suivi de la durée et du succès, pas d'alerte). **Priorité :** moyenne.
- **En tant qu'**équipe technique, **je veux** suivre la durée et le taux de réussite des générations et être alerté en cas de problème, **afin de** réagir vite.
- **Critères de validation :**
  - chaque appel à l'IA est enregistré (durée, succès) ;
  - les seuils d'alerte sont documentés ;
  - les journaux ne contiennent pas d'email en clair.
- **Accessibilité :**
  - le tableau de suivi n'utilise pas la couleur seule pour signaler un problème (1.4.1) ;
  - le contraste est suffisant (1.4.3).

## 4. Suivi

| Story | Statut | Sprint prévu |
|---|---|---|
| US1, US2, US3, US4, US7 | Existant | Améliorations d'accessibilité au sprint 6 |
| US5, US6 | Partiel, à faire | Sprint 3 |
| US8, US9 | À faire | Après le sprint 6 si le temps le permet |
| US10 | Existant | Réalisé au sprint 1 |
| US11 | Partiel | Sprint 4 |