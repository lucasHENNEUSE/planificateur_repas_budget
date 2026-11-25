# Benchmark des services d'intelligence artificielle d'Éco-Frigo (carte #24, C7)

**Date :** 21 novembre 2026
**Objet :** choisir le service d'IA qui génère les menus, les recettes et la liste des magasins d'Éco-Frigo, et expliquer pourquoi les autres n'ont pas été retenus.
**Document lié :** la configuration du service retenu est décrite dans `documentation-gemini.md` (C8).

## 1. L'expression de besoin reformulée

### Ce que fait Éco-Frigo

Éco-Frigo est un planificateur de repas de la semaine qui respecte un budget. L'utilisateur choisit un magasin, un budget et un nombre de personnes. L'application propose des menus avec des produits réels et leur prix.

### Ce que l'IA doit faire

Dans mon code, l'IA est appelée à trois endroits :

| Ensemble fonctionnel | Ce que l'IA doit produire | Fichier |
|---|---|---|
| A. Composer un menu | Un menu de la semaine à partir de produits pris dans ma base, dans le budget | `rag_service.py` |
| B. Rédiger une recette | Les ingrédients avec leurs quantités et 4 à 7 étapes, en français | `IA/llm_service.py` |
| C. Trouver des magasins | 2 à 4 supermarchés (Leclerc et Carrefour) d'une ville | `IA/llm_service.py` |

Dans les trois cas, la réponse doit être en **JSON** pour que le code la lise sans « deviner » du texte libre.

### Les objectifs du projet d'intégration

1. Générer des menus utilisables, c'est-à-dire qui respectent le budget (le code contrôle ensuite chaque menu).
2. Répondre dans un délai acceptable pour un utilisateur.
3. Rester simple à intégrer et à expliquer à l'oral.

### Les contraintes

| Contrainte | Explication |
|---|---|
| Coût nul | Projet personnel, aucun abonnement payant (voir `choix-techniques.md`). |
| Fonctionner en local | Mon souhait de départ était de tout garder sur ma machine : l'application, les données et l'IA. L'application se lance en local avec Docker, sans serveur d'hébergement. |
| Données personnelles | Aucune donnée personnelle ne doit être envoyée au service (RGPD, minimisation). Les prompts contiennent seulement des noms de produits, des prix, un budget, un nombre de personnes, un nom de plat et une ville. |
| Sortie en JSON | Le service doit pouvoir répondre en JSON. |
| Français | Menus et recettes en français. |
| Intégration en Python | Un SDK ou une API simple à appeler depuis FastAPI. |
| Disponibilité et quota | Le service doit rester utilisable pendant une démonstration. |
| Démarche éco-responsable | Je veux connaître l'impact du service quand l'information existe, et réduire mes appels (cache MongoDB). |

## 2. Les services étudiés et les services non étudiés

### Services étudiés (5)

Quatre sont des API d'IA générative de texte, accessibles à distance avec une clé. Le cinquième, Gemma, est une famille de modèles que j'ai utilisés dans un agent d'IA, en local (avec Ollama), parce que je voulais rester sur ma machine.

| Service | Fournisseur |
|---|---|
| API Gemini | Google |
| API Mistral (La Plateforme) | Mistral AI (France) |
| API OpenAI | OpenAI |
| API Claude | Anthropic |
| Modèles Gemma (`gemma3:4b` et `gemma2.1:2b`), utilisés dans un agent d'IA | Google |

### Services non étudiés

| Service | Raison |
|---|---|
| Modèles open source autres que Gemma, hébergés sur ma machine ou sur un serveur | Mes essais avec deux petits modèles Gemma ne m'ont pas convaincu : ils inventaient des données. Un modèle plus gros demanderait plus de ressources sur ma machine, que je n'ai pas évaluées. |
| Services d'IA qui ne génèrent pas de texte (reconnaissance d'images, traduction, voix) | Ils ne répondent à aucun des trois ensembles fonctionnels. |
| Autres fournisseurs d'API de texte | Je me suis limité à quatre fournisseurs. Ce choix est une limite du benchmark (voir la partie 8). |

### Raisons d'écarter un service après étude

| Service | Statut | Raison |
|---|---|---|
| Agent d'IA avec Gemma (ma première approche) | Écarté après essai | Au début du projet, j'ai utilisé un agent d'IA avec des petits modèles Gemma (`gemma3:4b` puis `gemma2.1:2b`), lancés en local avec Ollama, pour composer les menus. Les résultats n'étaient pas ceux que j'attendais : il inventait des données, même avec des restrictions écrites dans le prompt de l'utilisateur. Je l'ai remplacé par la méthode actuelle : mon code choisit les produits réels de la base et les donne à Gemini, puis il contrôle chaque menu produit. |
| API Claude | Écarté pour ce projet | Pas d'offre gratuite permanente : elle est facturée à l'usage, avec seulement un petit crédit d'essai dont le montant n'est pas publié. Cela ne respecte pas la contrainte de coût nul. Ce n'est pas un jugement sur la qualité du service. |
| API OpenAI | Écarté pour l'instant | Les sources se contredisent sur l'existence d'un accès gratuit utilisable : le guide des limites mentionne un niveau gratuit réservé à certains pays, mais je n'ai pas trouvé quels modèles il permet d'utiliser. Je ne peux pas confirmer la contrainte de coût nul. |
| API Mistral | Non retenu | Offre gratuite, mode JSON, entreprise européenne, analyse du cycle de vie publiée : il répond au besoin sur le papier. Je ne l'ai pas retenu parce que les appels de mon application sont déjà écrits pour Gemini et testés avec lui, et que les chiffres du niveau gratuit de Mistral ont changé d'une page d'aide à l'autre. |
| API Gemini | **Retenu** | Voir la partie 7. |

## 3. Adéquation de chaque service aux ensembles fonctionnels

Je distingue trois niveaux de preuve :
- **Testé** : j'ai essayé le service dans Éco-Frigo.
- **Documenté** : la documentation officielle du fournisseur indique que la fonction existe, mais je ne l'ai pas essayée.

| Critère | Gemini | Gemma (Ollama) | Mistral | OpenAI | Claude |
|---|---|---|---|---|---|
| A. Menu (texte guidé par ma base) | **Testé** | **Testé : insuffisant** (données inventées) | Non testé | Non testé | Non testé |
| B. Recette en français | **Testé** | Non établi | Non testé | Non testé | Non testé |
| C. Magasins d'une ville | **Testé** | Non établi | Non testé | Non testé | Non testé |
| Réponse en JSON | **Testé** (`response_mime_type`) ; schéma documenté | Non établi | Documenté (mode JSON sur tous les modèles, sorties structurées avec schéma) | Documenté (Structured Outputs avec schéma) | Documenté (sorties structurées avec schéma JSON) |
| Intégration en Python | **Testé** (SDK `google-genai`) | Non établi | Documenté (SDK Python) | Documenté (SDK Python) | Documenté (SDK Python) |

### Résultat des tests de Gemini

J'ai testé plusieurs modèles dans l'application : `gemini-3.8-flash`, et deux petits modèles Gemma (voir la partie 2). Pour `gemini-3.8-flash`, sur trois mesures de mon évaluation (`evaluation.py`, 3 demandes chacune, les 20 et 21 novembre, dont une avec le niveau de réflexion réduit de la carte #27) : 2 menus conformes sur 3 à chaque fois. La ligne en échec venait des erreurs 503 de Google (« forte demande ») : je n'ai pas relevé de menu faux dans ces mesures. Elles sont trop peu nombreuses pour conclure sur la qualité. Elles montrent surtout que le service peut être surchargé.

## 4. La démarche éco-responsable

Les chiffres des fournisseurs ne sont **pas comparables entre eux** : ils n'ont pas la même méthode, ni le même périmètre, ni la même unité. Je les donne pour information, sans classement.

| Service | Information publiée par le fournisseur | Ce qu'elle mesure |
|---|---|---|
| Gemini (Google) | Un prompt texte médian de l'application Gemini consomme 0,24 Wh, émet 0,03 gCO₂e et consomme 0,26 mL d'eau (étude de mai 2025). | L'**application** Gemini, pas l'API, et pas mon modèle précis. Elle compte les machines inactives et le refroidissement. |
| Mistral | Une réponse de 400 jetons de l'assistant Le Chat : 1,14 gCO₂e et 45 mL d'eau. Pour Mistral Large 2, 18 mois d'usage et entraînement : 20,4 ktCO₂e et 281 000 m³ d'eau. | Une analyse de cycle de vie réalisée avec Carbone 4 et l'ADEME, relue par deux cabinets. Elle indique que l'impact croît fortement avec la taille du modèle. |
| OpenAI | Je n'ai pas trouvé de chiffre publié dans mes recherches. | — |
| Claude (Anthropic) | Je n'ai pas trouvé de chiffre publié dans mes recherches. | — |
| Gemma en local (Ollama) | Je n'ai pas cherché de chiffre. Le modèle tourne sur ma machine : l'énergie dépend d'elle et je ne l'ai pas mesurée. | — |

« Je n'ai pas trouvé » ne veut pas dire que l'information n'existe pas.

**Ce que j'en retiens pour Éco-Frigo :**
- Le seul point commun fiable est que l'impact augmente avec la taille du modèle. J'utilise donc un modèle de la gamme « Flash », pensé pour la vitesse, plutôt qu'un modèle plus gros.
- Mon cache MongoDB évite de redemander un menu ou une recette déjà générés : c'est mon action la plus directe pour réduire les appels.
- Je teste un niveau de réflexion réduit (carte #27) pour répondre plus vite. Je n'ai pas de mesure de son effet sur l'énergie, seulement sur le temps.

## 5. Les contraintes techniques et les prérequis de chaque solution

| | Gemini | Mistral | OpenAI | Claude |
|---|---|---|---|---|
| Compte et clé | Compte Google, clé créée dans Google AI Studio | Compte sur la console Mistral, clé API | Compte, clé API | Compte sur la console Anthropic, clé API |
| Accès gratuit | Oui | Oui (niveau gratuit, limites à vérifier dans la console) | Niveau gratuit annoncé pour certains pays, modèles utilisables non établis | Non permanent : petit crédit d'essai |
| Limites observées ou publiées | **20 requêtes par jour** pour `gemini-3.8-flash` (message d'erreur 429 du 20 novembre) ; limites par projet | Une ancienne page d'aide donne 1 requête par seconde, 500 000 jetons par minute et 1 milliard de jetons par mois ; une page plus récente renvoie à la console | Limites par palier, liées aux dépenses | Limites par palier de dépense |
| Données envoyées (niveau gratuit) | Peuvent être lues par des réviseurs et servir à améliorer les produits de Google | Une source non officielle indique que le niveau gratuit demande d'accepter l'usage des données pour l'entraînement : à vérifier | Pas d'entraînement sur les données de l'API par défaut ; journaux de surveillance conservés jusqu'à 30 jours | Pas d'entraînement sur le contenu des clients d'après les conditions commerciales |
| Données envoyées (niveau payant) | Non utilisées pour améliorer les produits | Isolation des données, option de non-conservation annoncée | Idem niveau gratuit | Idem |
| Points d'attention | Erreurs 503 en période de forte demande ; tarif d'introduction jusqu'au 31 décembre 2026 | Pas testé | Pas testé | Pour les clients de l'Espace économique européen, le contrat est avec Anthropic Ireland |
| Effort pour changer de service | Réécrire `IA/llm_service.py`, le seul fichier qui appelle l'API, ainsi que le SDK dans `requirements.txt` | Idem | Idem | Idem |

Je n'ai pas comparé les tarifs payants : mon projet reste sur l'offre gratuite, et les prix changent souvent. À faire si Éco-Frigo passait en production.

## 6. Les conséquences pour le projet

1. **Quota.** 20 requêtes par jour, c'est très peu. Mon évaluation automatique en consommait 3 à chaque fusion : je l'ai rendue manuelle (modification de `cd.yml` du 20 novembre).
2. **Données.** Mes prompts ne contiennent aucune donnée personnelle, ce qui rend le niveau gratuit acceptable pour une démonstration. Pour de vrais utilisateurs en France, il faudrait un niveau payant (voir ma veille du 20 novembre).
3. **Fiabilité du JSON.** Mon code demande du JSON sans fournir de schéma. La documentation de Google indique qu'avec un schéma la structure est plus fiable ; sans schéma, le format JSON n'est qu'une forte consigne, avec un petit risque de JSON invalide. Mon code contrôle déjà chaque menu, donc je garde cette version simple et je note la limite.
4. **Fin du « tout en local ».** Avec Gemini, les prompts passent par les serveurs de Google, ce que le mode local évitait. Je limite l'effet en n'y mettant aucune donnée personnelle.
5. **Dépendance à un fournisseur.** Mes appels sont regroupés dans un seul fichier : changer de service est possible, mais ce n'est pas immédiat.

## 7. Les conclusions

### Services qui répondent au besoin

| Service | Avantages | Inconvénients |
|---|---|---|
| **Gemini — retenu** | Testé dans mon projet, après mes essais avec Gemma. Accès gratuit. JSON demandé et lu sans difficulté. Informations d'impact publiées par Google (pour l'application). | Quota de 20 requêtes par jour. Erreurs 503 en période de forte demande, qui rallongent les temps. Contenus du niveau gratuit utilisables par Google. |
| **Mistral — répond au besoin, non retenu** | Offre gratuite, mode JSON sur tous les modèles, entreprise européenne, analyse de cycle de vie publiée. | Non testé. Limites du niveau gratuit peu claires. Il faudrait réécrire `IA/llm_service.py`. |

### Services qui ne couvrent pas le besoin (aujourd'hui)

| Service | Pourquoi |
|---|---|
| Agent d'IA avec Gemma et Ollama (première approche) | Les petits modèles Gemma essayés en local (`gemma3:4b`, `gemma2.1:2b`) inventaient des données malgré les restrictions du prompt : un menu avec de faux produits ou de faux prix est inutilisable pour un projet dont le but est de respecter un budget. |
| OpenAI | Impossible de confirmer un accès gratuit utilisable. |
| Claude | Pas d'offre gratuite permanente : contrainte de coût nul non respectée. |

### Recommandation

**Je garde Gemini (`gemini-3.8-flash`) pour Éco-Frigo.** C'est le service que j'ai retenu après avoir essayé d'autres modèles (Gemma), et il respecte la contrainte de coût nul. La décision sera revue si Éco-Frigo est mis à disposition de vrais utilisateurs.

## 8. Les limites de ce benchmark

- Je n'ai testé dans l'application que des modèles de Google (Gemini et Gemma). Pour Mistral, OpenAI et Claude, mes constats viennent de la documentation.
- Mes essais avec Gemma portent sur deux petits modèles (4 et 2 milliards de paramètres). Ils ne disent rien des grands modèles Gemma.
- Quatre fournisseurs seulement ont été étudiés.
- Les offres, les limites et les tarifs changent vite. Les informations ont été lues le 21 novembre 2026 et seront relues lors de ma veille du samedi.
- Plusieurs chiffres viennent de sites tiers. Je le précise dans le tableau des sources, et je ne retiens que ce que confirme une page officielle.
- Le chiffre de 20 requêtes par jour vient du message d'erreur de l'API. Je dois encore le confirmer sur la page officielle des limites, comme prévu dans ma veille.

## Sources et fiabilité

| Source | Type | Fiabilité et remarque |
|---|---|---|
| ai.google.dev/gemini-api/docs/pricing | Officielle (Google) | Offres gratuite et payante, tarif d'introduction. Lue en extraits seulement. |
| ai.google.dev/gemini-api/docs/rate-limits | Officielle (Google) | Limites par projet, quota remis à zéro à minuit heure du Pacifique. |
| ai.google.dev/gemini-api/docs/structured-output | Officielle (Google) | Sorties structurées. |
| docs.cloud.google.com (Vertex AI, structured output) | Officielle (Google) | Précise qu'un type MIME JSON sans schéma n'est qu'une forte consigne. Page de Vertex AI, pas de l'API Gemini. |
| cloud.google.com/blog/products/infrastructure/measuring-the-environmental-impact-of-ai-inference | Officielle (Google) | Chiffres de l'application Gemini, pas de l'API. |
| mistral.ai/news/our-contribution-to-a-global-environmental-standard-for-ai | Officielle (Mistral) | Analyse de cycle de vie, relue par des cabinets externes. |
| help.mistral.ai (limites du niveau gratuit) | Officielle (Mistral) | Page non datée avec des chiffres ; une page plus récente renvoie à la console. |
| docs.mistral.ai (mode JSON, sorties structurées) | Officielle (Mistral) | Fonctions documentées. |
| mistral.ai/news/september-24-release | Officielle (Mistral) | Annonce de 2024 : niveau gratuit, isolation des données et option de non-conservation sur l'offre commerciale. Ancienne, à revérifier. |
| cheahjs/free-llm-api-resources (mintlify.com) | Liste communautaire | Non officielle. Seule source de l'obligation d'accepter l'entraînement sur le niveau gratuit : à vérifier. |
| developers.openai.com (limites, Structured Outputs, données) | Officielle (OpenAI) | Niveau gratuit mentionné, modèles accessibles non précisés. |
| openai.com/business-data | Officielle (OpenAI) | Pas d'entraînement par défaut sur les données de l'API. |
| anthropic.com/legal/commercial-terms | Officielle (Anthropic) | Pas d'entraînement sur le contenu des clients. |
| platform.claude.com (sorties structurées) | Officielle (Anthropic) | Fonction documentée. |
| benchlm.ai (niveaux gratuits OpenAI et Anthropic) | Site tiers | Résume les pages officielles. Utilisé pour l'absence d'offre gratuite permanente chez Anthropic. |
| activepieces.com (tarifs de l'API Claude) | Blog d'un éditeur | Intérêt commercial possible. Source secondaire. |
| Message d'erreur 429 de l'API Gemini | Observation personnelle | 20 novembre 2026. À confirmer sur la page officielle. |

## Accessibilité de ce document

Le document suit une hiérarchie de titres, les tableaux ont une ligne d'en-tête, aucune information n'est donnée par la couleur seule et il ne contient pas d'image. À l'export en PDF, je vérifierai que les titres et les tableaux sont bien balisés.