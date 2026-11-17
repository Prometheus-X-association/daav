# Rapport d'issues SonarQube – daav

- **Commit analysé** : `365cde1371412b93d57e2472a70675403bdabe99`
- **Date d'analyse** : 2026-10-22T11:24:16+0000
- **Rapport généré le** : 2026-10-22T14:02:36
- **Source** : `docs/daav-issues.html` (rapport interactif ; ce fichier reprend ses données embarquées)

> **Attention :** le commit analysé (`365cde1`, « Fix docker front end git (#23) ») est antérieur de 10 commits au `main` actuel. Les corrections faites depuis (durcissement sécurité, accessibilité WCAG, page compte…) ne sont pas prises en compte dans ce rapport.

## Contexte et démarche demandée

Ce rapport fait partie des *Technical Sustainability Reports* générés avec SonarQube pour chaque dépôt du projet, sur l'état le plus récent de la branche principale. Le fichier `daav-issues.html` s'ouvre dans n'importe quel navigateur, hors ligne et sans serveur SonarQube. Il a quatre onglets :

- **Summary** : les métriques principales (note de maintenabilité, dette technique, nombre d'issues, complexité) et leur explication.
- **Issues** : toutes les issues ouvertes, filtrables par qualité, sévérité, règle, langage et répertoire, avec le code concerné et la raison d'être de la règle.
- **Recurring rules** : les règles triées par nombre d'issues. **C'est ici que se prennent les décisions.**
- **Decisions** : la liste des règles qu'on a choisi d'ignorer, avec leurs justifications.

**Ce qui est demandé :** relire l'onglet *Recurring rules* et indiquer les règles à ignorer. Un ignore s'applique à **toute une règle** dans le dépôt, pas à des issues isolées.

**Règles pour les justifications :**

- Chaque ignore doit être justifié. Les justifications figureront dans le rapport final du projet.
- Elles doivent être **précises et vérifiables**, par exemple « the findings are false positives because the framework requires this pattern » ou « this rule conflicts with our coding standard, which requires X ».
- Des raisons comme « too many issues » sont refusées.
- Plusieurs règles de style et de modernisation ont déjà été ignorées pour tous les dépôts ; elles n'apparaissent pas dans ce rapport.

**Export des décisions :**

1. Ouvrir `daav-issues.html` → onglet *Recurring rules* → cocher « Ignore » pour chaque règle à ignorer et saisir la justification (obligatoire).
2. Vérifier la liste dans l'onglet *Decisions* et, si on le souhaite, saisir son nom.
3. Cliquer sur « Download decisions » (en haut à droite). Le navigateur enregistre `decisions-daav.json`.
4. Déposer ce JSON dans le dossier *Responses* : <https://drive.google.com/drive/u/0/folders/17txiDUjLXQ-4c2go4-CYJ_Eujn2CDNP2>

## Sommaire

- [Contexte et démarche demandée](#contexte-et-démarche-demandée)
- [Résumé](#resume)
- [Répartition des issues](#repartition)
- [Règles récurrentes](#regles-recurrentes)
- [Propositions de décisions](#propositions)
- [Issues par sévérité](#issues-par-severite)
- [Décisions](#decisions)

<a id="resume"></a>
## Résumé

### Totaux du projet

| Note | Dette (h) | Dette % | Issues | Cyclomatique | Cognitive |
|:---:|---:|---:|---:|---:|---:|
| **A** | 66.7 | 0.4 % | 843 | 4343 | 3799 |

### Par fichier

| Fichiers | Dette moy. (h) | Dette max (h) | Cyclomatique moy. | Cyclomatique max | Cognitive moy. | Cognitive max |
|---:|---:|---:|---:|---:|---:|---:|
| 302 | 0.22 | 7.62 | 11.09 | 150 | 12.35 | 282 |

### Signification des colonnes

- **Note** : note de maintenabilité de A à E selon le ratio de dette — A jusqu'à 5.0 %, B jusqu'à 10.0 %, C jusqu'à 20.0 %, D jusqu'à 50.0 %, E au-delà. A est la meilleure note.
- **Dette (h)** : estimation SonarQube de l'effort total pour corriger tous les code smells (problèmes de maintenabilité), en heures (1 jour = 8 h).
- **Dette %** : dette technique divisée par le coût estimé de réécriture complète du code (30.0 minutes par ligne). Plus bas = mieux.
- **Issues** : toutes les issues ouvertes (bugs, vulnérabilités, code smells ; statut ouvert ou confirmé).
- **Cyclomatique** : complexité cyclomatique cumulée — nombre de chemins indépendants dans le code (chaque condition, boucle ou case ajoute 1).
- **Cognitive** : complexité cognitive cumulée — difficulté de lecture ; les structures imbriquées et les ruptures de flux pèsent davantage.
- **Fichiers** : nombre de fichiers analysés hors fichiers de test (répertoires `test/`, `tests/`, `__tests__/`, `e2e/`, ou noms `*.spec.ts`, `test_*.py`…). Valeur approximative.
- **Dette moy. / max** : dette moyenne et maximale d'un fichier, en heures.
- **Cyclomatique / Cognitive moy. / max** : valeurs par fichier (SonarQube ne fournit pas la complexité par fonction).

<a id="repartition"></a>
## Répartition des issues

### Sévérité la plus haute par issue

| Valeur | Issues |
|---|---:|
| Bloquant | 45 |
| Haute | 159 |
| Moyenne | 261 |
| Basse | 378 |

### Sévérité (tous impacts confondus)

| Valeur | Issues |
|---|---:|
| Bloquant | 46 |
| Haute | 163 |
| Moyenne | 261 |
| Basse | 391 |

### Qualité logicielle impactée

| Valeur | Issues |
|---|---:|
| Maintenabilité | 724 |
| Fiabilité | 125 |
| Sécurité | 12 |

### Type (legacy)

| Valeur | Issues |
|---|---:|
| Code smell | 744 |
| Bug | 91 |
| Vulnérabilité | 8 |

### Catégorie Clean Code

| Valeur | Issues |
|---|---:|
| Intentional | 528 |
| Consistent | 250 |
| Adaptable | 56 |
| Responsible | 9 |

### Langage

| Valeur | Issues |
|---|---:|
| TypeScript | 373 |
| Python | 350 |
| HTML | 76 |
| CSS | 41 |
| Secrets | 2 |
| JavaScript | 1 |

### Partie du projet

| Valeur | Issues |
|---|---:|
| frontendApp | 489 |
| backendApi | 350 |
| docker-compose.yml | 2 |
| docs | 2 |

### Fichiers les plus concernés (top 20)

| Fichier | Issues |
|---|---:|
| `backendApi/app/routes/datasets.py` | 72 |
| `backendApi/app/routes/ptx.py` | 35 |
| `backendApi/app/nodes/outputs/file_output.py` | 29 |
| `backendApi/app/nodes/outputs/mongo_output.py` | 15 |
| `backendApi/app/routes/api.py` | 15 |
| `backendApi/app/routes/output.py` | 15 |
| `backendApi/app/nodes/outputs/mysql_output.py` | 14 |
| `backendApi/app/routes/workflows.py` | 14 |
| `backendApi/app/utils/utils.py` | 13 |
| `frontendApp/src/app/components/user-profile/user-profile.component.html` | 13 |
| `frontendApp/src/app/components/main/render/render.component.ts` | 12 |
| `frontendApp/src/app/components/user-profile/user-profile.component.ts` | 12 |
| `frontendApp/src/app/services/dataset.service.ts` | 11 |
| `frontendApp/src/app/pages/worflow/workflow.page.ts` | 10 |
| `backendApi/app/services/dataset_service.py` | 10 |
| `frontendApp/src/app/core/workflow-editor.ts` | 10 |
| `backendApi/app/nodes/inputs/service-chain-input.py` | 9 |
| `backendApi/app/nodes/transforms/merge_transform.py` | 9 |
| `frontendApp/src/app/core/contextMenuDaav.ts` | 9 |
| `frontendApp/src/app/nodes/input/input-data-block.ts` | 9 |

<a id="regles-recurrentes"></a>
## Règles récurrentes

Règles triées par nombre d'issues. Dans le rapport HTML, chaque règle peut être marquée « ignorée » avec une justification.

| # | Règle | Intitulé | Langage | Sévérité max | Issues |
|---:|---|---|---|---|---:|
| 1 | `python:S117` | Local variable and function parameter names should comply with a naming convention | Python | Basse | 115 |
| 2 | `typescript:S1128` | Unnecessary imports should be removed | TypeScript | Basse | 112 |
| 3 | `typescript:S2933` | Fields that are only assigned in the constructor should be "readonly" | TypeScript | Moyenne | 76 |
| 4 | `python:S8415` | HTTPException responses should be documented in endpoint metadata | Python | Haute | 61 |
| 5 | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Mouse events should have corresponding keyboard events | HTML | Basse | 56 |
| 6 | `python:S3776` | Cognitive Complexity of functions should not be too high | Python | Haute | 44 |
| 7 | `typescript:S7648` | Components, Directives, and Pipes should use standalone architecture | TypeScript | Bloquant | 37 |
| 8 | `typescript:S3863` | Imports from the same module should be merged | TypeScript | Basse | 37 |
| 9 | `python:S1542` | Function names should comply with a naming convention | Python | Moyenne | 23 |
| 10 | `css:S125` | Sections of code should not be commented out | CSS | Moyenne | 15 |
| 11 | `typescript:S125` | Sections of code should not be commented out | TypeScript | Moyenne | 13 |
| 12 | `css:S4667` | CSS files should not be empty | CSS | Moyenne | 12 |
| 13 | `python:S7503` | Async functions should use async features | Python | Moyenne | 12 |
| 14 | `python:S1481` | Unused local variables should be removed | Python | Basse | 11 |
| 15 | `typescript:S4325` | Redundant casts and non-null assertions should be avoided | TypeScript | Basse | 11 |
| 16 | `typescript:S1186` | Functions should not be empty | TypeScript | Haute | 9 |
| 17 | `Web:S6853` | Label elements should have a text label and an associated control | HTML | Moyenne | 9 |
| 18 | `typescript:S1854` | Unused assignments should be removed | TypeScript | Moyenne | 9 |
| 19 | `python:S3358` | Conditional expressions should not be nested | Python | Moyenne | 7 |
| 20 | `typescript:S2486` | Exceptions should not be ignored | TypeScript | Basse | 7 |
| 21 | `typescript:S6644` | Ternary operator should not be used instead of simpler alternatives | TypeScript | Basse | 7 |
| 22 | `python:S7493` | Async functions should not contain synchronous file operations | Python | Haute | 6 |
| 23 | `python:S7499` | Async functions should not contain synchronous HTTP client calls | Python | Haute | 6 |
| 24 | `css:S4656` | Properties should not be duplicated | CSS | Moyenne | 6 |
| 25 | `python:S3457` | String formatting should be used correctly | Python | Moyenne | 6 |
| 26 | `typescript:S6671` | Literals should not be used for promise rejection | TypeScript | Moyenne | 6 |
| 27 | `typescript:S3504` | Variables should be declared with "let" or "const" | TypeScript | Haute | 5 |
| 28 | `typescript:S3776` | Cognitive Complexity of functions should not be too high | TypeScript | Haute | 5 |
| 29 | `Web:AvoidCommentedOutCodeCheck` | Sections of code should not be commented out | HTML | Moyenne | 5 |
| 30 | `python:S5886` | Function return types should be consistent with their type hint | Python | Moyenne | 5 |
| 31 | `python:S5890` | Values assigned to variables should match their type annotations | Python | Moyenne | 5 |
| 32 | `python:S5754` | "SystemExit" should be re-raised | Python | Haute | 4 |
| 33 | `css:S7924` | Text and background colors should have sufficient contrast | CSS | Moyenne | 4 |
| 34 | `python:S112` | "Exception" and "BaseException" should not be raised | Python | Moyenne | 4 |
| 35 | `typescript:S6544` | Promises should not be misused | TypeScript | Moyenne | 4 |
| 36 | `typescript:S905` | Non-empty statements should change control flow or have at least one side-effect | TypeScript | Moyenne | 4 |
| 37 | `python:S1313` | IP addresses should not be hardcoded | Python | Basse | 4 |
| 38 | `python:S930` | The number and name of arguments passed to a function should match its parameters | Python | Bloquant | 3 |
| 39 | `typescript:S5443` | Temporary files should not be created in publicly writable directories | TypeScript | Haute | 3 |
| 40 | `python:S7483` | Asynchronous functions should not accept timeout parameters | Python | Moyenne | 3 |
| 41 | `typescript:S6535` | Unnecessary character escapes should be removed | TypeScript | Moyenne | 3 |
| 42 | `typescript:S7753` | "indexOf()" and "lastIndexOf()" should be used instead of "findIndex()" and "findLastIndex()" for simple equality searches | TypeScript | Moyenne | 3 |
| 43 | `typescript:S101` | Class names should comply with a naming convention | TypeScript | Basse | 3 |
| 44 | `typescript:S7741` | "typeof" should not be used to check for "undefined" | TypeScript | Basse | 3 |
| 45 | `python:S3516` | Functions returns should not be invariant | Python | Bloquant | 2 |
| 46 | `secrets:S6694` | MongoDB database passwords should not be disclosed | Secrets | Bloquant | 2 |
| 47 | `python:S1186` | Functions and methods should not be empty | Python | Haute | 2 |
| 48 | `python:S2638` | Method overrides should not change contracts | Python | Haute | 2 |
| 49 | `python:S4487` | Unread "private" attributes should be removed | Python | Haute | 2 |
| 50 | `python:S8510` | Loop variables should not be reused in nested loops | Python | Haute | 2 |
| 51 | `typescript:S4123` | "await" should only be used with promises | TypeScript | Haute | 2 |
| 52 | `Web:S4084` | Videos should have subtitles | HTML | Moyenne | 2 |
| 53 | `css:S4649` | Font declarations should contain at least one generic font family | CSS | Moyenne | 2 |
| 54 | `python:S1172` | Unused function parameters should be removed | Python | Moyenne | 2 |
| 55 | `python:S125` | Sections of code should not be commented out | Python | Moyenne | 2 |
| 56 | `python:S2068` | Credentials should not be hard-coded | Python | Moyenne | 2 |
| 57 | `python:S8513` | "startswith" and "endswith" calls should use tuples instead of multiple "or" operators | Python | Moyenne | 2 |
| 58 | `typescript:S1121` | Assignments should not be made from within sub-expressions | TypeScript | Moyenne | 2 |
| 59 | `typescript:S3923` | All branches in a conditional structure should not have exactly the same implementation | TypeScript | Moyenne | 2 |
| 60 | `python:S1940` | Boolean checks should not be inverted | Python | Basse | 2 |
| 61 | `python:S5713` | A subclass should not be in the same "except" statement as a parent class | Python | Basse | 2 |
| 62 | `python:S6660` | "isinstance()" should be preferred to direct type comparisons | Python | Basse | 2 |
| 63 | `python:S8414` | CORSMiddleware should be added last in the middleware chain | Python | Bloquant | 1 |
| 64 | `css:S4670` | Selectors should be known | CSS | Haute | 1 |
| 65 | `python:S2208` | Wildcard imports should not be used | Python | Haute | 1 |
| 66 | `python:S8396` | Optional Pydantic fields should have explicit default values | Python | Haute | 1 |
| 67 | `typescript:S2004` | Functions should not be nested too deeply | TypeScript | Haute | 1 |
| 68 | `typescript:S7059` | Constructors should not contain asynchronous operations | TypeScript | Haute | 1 |
| 69 | `typescript:S7768` | Modern DOM manipulation methods should be used instead of legacy alternatives | TypeScript | Haute | 1 |
| 70 | `Web:MetaRefreshCheck` | Meta tags should not be used to refresh or redirect | HTML | Moyenne | 1 |
| 71 | `Web:PageWithoutTitleCheck` | "<title>" should be present in all pages | HTML | Moyenne | 1 |
| 72 | `Web:S7926` | Meta viewport tags should allow users to zoom | HTML | Moyenne | 1 |
| 73 | `css:S4666` | Selectors should not be duplicated | CSS | Moyenne | 1 |
| 74 | `python:S1854` | Unused assignments should be removed | Python | Moyenne | 1 |
| 75 | `python:S1871` | Two branches in a conditional structure should not have exactly the same implementation | Python | Moyenne | 1 |
| 76 | `python:S5864` | Type checks shouldn't be confusing | Python | Moyenne | 1 |
| 77 | `python:S8519` | "list(...)[0]" should not be used to get the first element | Python | Moyenne | 1 |
| 78 | `typescript:S1871` | Two branches in a conditional structure should not have exactly the same implementation | TypeScript | Moyenne | 1 |
| 79 | `typescript:S6564` | Redundant type aliases should not be used | TypeScript | Moyenne | 1 |
| 80 | `typescript:S6660` | If statements should not be the only statement in else blocks | TypeScript | Moyenne | 1 |
| 81 | `Web:S5725` | Remote artifacts should not be used without integrity checks | HTML | Basse | 1 |
| 82 | `javascript:S7726` | Default exports should be named | JavaScript | Basse | 1 |
| 83 | `typescript:S6551` | Objects and classes converted or coerced to strings should define a "toString()" method | TypeScript | Basse | 1 |
| 84 | `typescript:S6571` | Type constituents of unions and intersections should not be redundant | TypeScript | Basse | 1 |
| 85 | `typescript:S6647` | Unnecessary constructors should be removed | TypeScript | Basse | 1 |
| 86 | `typescript:S7723` | Built-in constructors should be called consistently with or without "new" | TypeScript | Basse | 1 |

<a id="propositions"></a>
## Propositions de décisions

Propositions issues d'une relecture du code (commit analysé `365cde1` et `main` actuel). Elles restent **à valider par l'équipe** avant d'être saisies dans le rapport HTML. Les justifications sont rédigées en anglais, car elles seront reprises telles quelles dans le rapport final.

### Règles à ignorer (faux positifs vérifiables)

| Règle | Issues | Justification proposée (à copier dans le rapport) | Vérification |
|---|---:|---|---|
| `Web:MouseEventWithoutKeyboardEquivalentCheck` | 56 | *False positives: 46 of the 56 findings are on `<ion-button>` / `<ion-fab-button>`, Ionic web components that render a native `<button>` in their shadow DOM, so `(click)` is already triggered by Enter and Space. The analyzer only sees the custom tag and cannot know this. The other findings (clickable `<ion-icon>`, `<div>`, `<ion-card-header>`) were fixed in commit c1219ea (WCAG 2.1 AA): they are now native buttons or have `keydown.enter`/`keydown.space` handlers.* | 45 `ion-button` + 1 `ion-fab-button` ; sur `main`, plus aucun `<ion-icon (click)>`, `data-mapper` utilise un `<button>`, `ptxdashboard` a des handlers clavier. Restent `ion-radio` (géré au clavier par `ion-radio-group`) et un `ion-item` d'en-tête d'accordéon dont le bouton voisin offre déjà le même toggle au clavier. |
| `typescript:S5443` | 3 | *False positives: the three findings are in `dataset.service.spec.ts`, where `'/tmp/data.csv'` is a string value of a mocked HTTP response used as a test fixture. No file is created or read; the frontend runs in a browser and has no file system access.* | `frontendApp/src/app/services/dataset.service.spec.ts` lignes 64, 68, 134. |
| `python:S1313` | 4 | *False positives: the flagged values are the RFC 1918 private ranges and the link-local range (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`) of the SSRF protection, i.e. the networks the backend refuses to connect to. They are not hard-coded host addresses.* | `dataset_interface.py` l. 21–25 dans le commit analysé. Sur `main`, ce code a été remplacé par `utils/ssrf.py` (`is_private`…), donc les issues ont disparu : cet ignore est facultatif. |

### `typescript:S7648` (37 issues) — **fait** : le front est entièrement standalone (aucun NgModule, `bootstrapApplication`, routes en `loadComponent`)

*Analyse initiale :*

Le front est **hybride** : l'application démarre par `bootstrapModule(AppModule)`, 21 fichiers déclarent des `NgModule` et 45 composants ont `standalone: false`. En revanche, les 5 composants les plus récents sont déjà standalone (`confirm-deletion-modal`, `elastic-dashboard`, `ptxdashboard`, `loading`, `workflow-update-rules-modal`). Une migration est donc déjà amorcée, ce qui contredit l'argument d'une architecture NgModule voulue et cohérente. Mieux vaut garder la règle et poursuivre la migration (`ng generate @angular/core:standalone`).

### Règles à garder et à corriger

| Règle(s) | Issues | Raison de ne pas ignorer | Correction suggérée |
|---|---:|---|---|
| `python:S117`, `python:S1542` | 138 | Le projet n'a pas de convention camelCase documentée pour le Python, et le code mélange déjà les deux styles. PEP 8, le guide de style officiel de Python, impose le snake_case pour les variables et les fonctions ; c'est ce que vérifie la règle. | **Fait** : 147 noms renommés (23 fonctions, 30 paramètres, 94 variables) avec rope. Les URL des routes viennent des décorateurs et ne changent pas ; les paramètres de requête `includeHidden` et `hasSigned` gardent leur nom public grâce à un `alias`. |
| `typescript:S1128`, `typescript:S3863`, `typescript:S2933` | 225 | Vraies issues, corrigeables automatiquement. | **Fait** : imports inutiles supprimés (service de langage TypeScript), imports en double fusionnés (`import/no-duplicates`), champs privés passés en `readonly` (`@typescript-eslint/prefer-readonly`). |
| `python:S8415` | 61 | La doc OpenAPI est exposée (pas de `docs_url=None` dans `main.py`), donc documenter les erreurs a du sens. | `responses={500: …, 404: …}` sur les routeurs ou les routes. |
| `python:S7503` | 12 | Contenait un vrai bug : `DatabaseConfig.disconnect` appelait `self.client.close()` sans `await`, alors que `close()` d'`AsyncMongoClient` est une coroutine, donc la connexion n'était pas fermée. `mysql_content`, `mongo_content` et `elastic_content` sont en fait du code mort (aucune route). | **Fait (non commité)** : `await` ajouté dans `disconnect` ; vérifications en mémoire (`can_access_*`, `can_modify_*`, `authenticate_m2m_credentials`, dépendances d'authentification) passées en synchrone ; code mort supprimé (`mysql_content`, `mongo_content`, `elastic_content`, `api_content` — ce qui règle aussi un des `python:S930` —, `verify_admin`). En plus : les routes `getContentDataset` et `getDfContentDataset` exécutent désormais leurs lectures synchrones (fichier, MongoDB, MySQL, Elasticsearch) dans le thread pool, et un accès refusé à un fichier est bien journalisé. |
| `css:S4667` | 12 | Fichiers SCSS vides générés par l'Angular CLI. | Supprimer les fichiers et leurs `styleUrls`. |
| `secrets:S6694`, `python:S2068` | 4 | La mise à jour de sécurité (`067d7b3`) n'a réglé le problème qu'en partie. Elle a ajouté `must_change_password = True` sur l'admin créé par défaut et passé `ELASTIC_PASSWORD` en variable d'environnement. Mais `admin123` reste en clair 4 fois dans `docker-compose.yml` (Mongo et mongo-express), et la chaîne `"Admin123!"` est toujours dans le code : SonarQube la signalera encore. Une des deux issues S2068 (`_SPECIAL_PASSWORD_CHARS`) est un faux positif, mais ignorer la règle masquerait l'autre. | MongoDB : **fait (non commité)** — mot de passe lu depuis le secret Docker obligatoire `secrets/mongo_root_password` par MongoDB, le backend (`MONGODB_PASSWORD_FILE`) et mongo-express (dont l'authentification basique, jusque-là désactivée, est maintenant activée). Admin : **fait (non commité)** — le mot de passe initial est lu depuis le secret Docker obligatoire `secrets/admin_firstlaunch` (`ADMIN_PASSWORD_FILE`) et doit être changé à la première connexion ; plus aucun mot de passe en dur dans le code. |
| Autres règles (≤ 15 issues chacune) | — | Pas de justification générique identifiée ; à corriger au cas par cas. | — |

<a id="issues-par-severite"></a>
## Issues par sévérité

Issues triées par sévérité la plus haute, puis par fichier et par ligne. Colonnes : ligne, message, règle, impacts (qualité / sévérité), type, effort estimé.

### Bloquant (45)

#### `backendApi/app/main.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 108 | Add CORSMiddleware last in the middleware chain. <sub>fastapi, cors, configuration, middleware</sub> | `python:S8414` | Fiabilité / Bloquant, Maintenabilité / Bloquant | Code smell | 5min |
| 316 | Remove this unexpected named argument 'limit_max_request_size'. <sub>cwe</sub> | `python:S930` | Fiabilité / Bloquant | Bug | 10min |

#### `backendApi/app/routes/datasets.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 337 | Remove this unexpected named argument 'dictionary'. <sub>cwe</sub> | `python:S930` | Fiabilité / Bloquant | Bug | 10min |
| 629 | Remove 1 unexpected arguments; 'getApiContent' expects 2 positional arguments. <sub>cwe</sub> | `python:S930` | Fiabilité / Bloquant | Bug | 10min |

#### `backendApi/app/services/auth_service.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 262 | Refactor this method to not always return the same value. <sub>design, confusing</sub> | `python:S3516` | Maintenabilité / Bloquant | Code smell | 2min |

#### `backendApi/app/utils/utils.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 567 | Refactor this method to not always return the same value. <sub>design, confusing</sub> | `python:S3516` | Maintenabilité / Bloquant | Code smell | 2min |

#### `docker-compose.yml` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 28 | Make sure this MongoDB password gets changed and removed from the code. <sub>cwe</sub> | `secrets:S6694` | Sécurité / Bloquant | Vulnérabilité | 30min |
| 48 | Make sure this MongoDB password gets changed and removed from the code. <sub>cwe</sub> | `secrets:S6694` | Sécurité / Bloquant | Vulnérabilité | 30min |

#### `frontendApp/src/app/app.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 7 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/dashboards/dashboard/dashboard.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 10 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/dashboards/file-dashboard/file-dashboard.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 9 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/data-filter/data-filter.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 11 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/data-mapper/data-mapper.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 12 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/datasets-modal/datasets-modal.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 20 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/main/datasets/datasets.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 13 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/main/render/render.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 15 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/main/transformation/transformation.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 16 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/nodes/input/nodes.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 22 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/nodes/output/nodes.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 22 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/nodes/transform/nodes.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 22 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/sockets/deep-socket-component/deep-socket.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 7 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/sockets/flat-socket-component/flat-socket.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 7 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/sockets/global-socket-component/global-socket.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 7 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/sockets/socket-component/socket.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 7 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/transformation-modal/transformation-modal.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 7 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/user-profile/user-profile.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 13 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/auto-complete-widget/input-auto-complete-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 52 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/button-widget/button-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 20 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/checkbox-widget/checkbox-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 34 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/data-filter-widget/data-filter-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 32 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/data-mapper-widget/data-mapper-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 23 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/json-inputs-widget/json-inputs-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 25 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/node-loader-widget/node-loader-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 19 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/select-widget/select-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 41 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/status-component/status-component.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 21 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/text-display-widget/text-display-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 43 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/main/main.page.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 22 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/models/data-mapper-types.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 46 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/pages/forgot-password/forgot-password.page.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 11 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/pages/login/login.page.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 11 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/pages/register/register.page.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 11 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/pages/reset-password/reset-password.page.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 11 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/pages/test-composant/test-composant.page.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 7 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/pages/worflow/workflow.page.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 15 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

#### `frontendApp/src/app/tabs/tabs.page.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 11 | Components, Directives and Pipes should not opt out of standalone. Following this guide is highly recommended: https://angular.dev/reference/migrations/standalone <sub>angular</sub> | `typescript:S7648` | Maintenabilité / Bloquant | Code smell | 5min |

### Haute (159)

#### `backendApi/app/main.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 294 | Use an asynchronous file API instead of synchronous open() in this async function. <sub>async, trio, asyncio, anyio</sub> | `python:S7493` | Fiabilité / Haute | Bug | 5min |

#### `backendApi/app/models/interface/dataset_schema.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 9 | Add an explicit default value to this optional field. <sub>pydantic, type-hint, validation</sub> | `python:S8396` | Fiabilité / Haute, Maintenabilité / Haute | Code smell | 5min |

#### `backendApi/app/models/interface/node_data.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 55 | Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 9min |

#### `backendApi/app/models/interface/pdc_interface.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 381 | Remove this unread private attribute '__v' or refactor the code to use its value. <sub>cwe, unused</sub> | `python:S4487` | Maintenabilité / Haute | Code smell | 5min |

#### `backendApi/app/models/interface/workflow_interface.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 39 | Remove this unread private attribute '__type' or refactor the code to use its value. <sub>cwe, unused</sub> | `python:S4487` | Maintenabilité / Haute | Code smell | 5min |
| 91 | Specify an exception class to catch or reraise the exception <sub>error-handling, bad-practice, suspicious</sub> | `python:S5754` | Maintenabilité / Haute | Code smell | 5min |

#### `backendApi/app/nodes/inputs/data_hugging_block.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 20 | Add a nested comment explaining why this method is empty, or complete the implementation. <sub>suspicious</sub> | `python:S1186` | Maintenabilité / Haute | Code smell | 5min |
| 20 | Add missing parameters sample. <sub>suspicious</sub> | `python:S2638` | Maintenabilité / Haute | Code smell | 15min |

#### `backendApi/app/nodes/inputs/data_lrs_block.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 20 | Add a nested comment explaining why this method is empty, or complete the implementation. <sub>suspicious</sub> | `python:S1186` | Maintenabilité / Haute | Code smell | 5min |
| 20 | Add missing parameters sample. <sub>suspicious</sub> | `python:S2638` | Maintenabilité / Haute | Code smell | 15min |

#### `backendApi/app/nodes/inputs/data_mysql_block.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 36 | Refactor this function to reduce its Cognitive Complexity from 56 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 46min |

#### `backendApi/app/nodes/inputs/service-chain-input.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 37 | Refactor this function to reduce its Cognitive Complexity from 64 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 54min |

#### `backendApi/app/nodes/node.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 46 | Refactor this function to reduce its Cognitive Complexity from 27 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 17min |

#### `backendApi/app/nodes/node_factory.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 24 | Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 11min |

#### `backendApi/app/nodes/outputs/file_output.py` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 42 | Refactor this function to reduce its Cognitive Complexity from 115 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 1h45min |
| 153 | Use an asynchronous file API instead of synchronous open() in this async function. <sub>async, trio, asyncio, anyio</sub> | `python:S7493` | Fiabilité / Haute | Bug | 5min |
| 211 | Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 9min |
| 336 | Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 7min |

#### `backendApi/app/nodes/outputs/mongo_output.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 36 | Refactor this function to reduce its Cognitive Complexity from 43 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 33min |
| 116 | Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 7min |

#### `backendApi/app/nodes/outputs/mysql_output.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 33 | Refactor this function to reduce its Cognitive Complexity from 34 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 24min |
| 108 | Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 7min |

#### `backendApi/app/nodes/outputs/pdc_output.py` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 77 | Refactor this function to reduce its Cognitive Complexity from 25 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 15min |
| 129 | Use an asynchronous file API instead of synchronous open() in this async function. <sub>async, trio, asyncio, anyio</sub> | `python:S7493` | Fiabilité / Haute | Bug | 5min |
| 142 | Use an asynchronous file API instead of synchronous open() in this async function. <sub>async, trio, asyncio, anyio</sub> | `python:S7493` | Fiabilité / Haute | Bug | 5min |
| 150 | Use an async HTTP client in this async function instead of a synchronous one. <sub>async, trio, asyncio, anyio, http</sub> | `python:S7499` | Fiabilité / Haute | Bug | 5min |

#### `backendApi/app/nodes/outputs/service_chain_output.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 34 | Refactor this function to reduce its Cognitive Complexity from 24 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 14min |
| 97 | Use an async HTTP client in this async function instead of a synchronous one. <sub>async, trio, asyncio, anyio, http</sub> | `python:S7499` | Fiabilité / Haute | Bug | 5min |

#### `backendApi/app/nodes/transforms/example_transform.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 41 | Rename this loop variable; it shadows the outer loop variable "key". <sub>confusing, pitfall</sub> | `python:S8510` | Fiabilité / Haute, Maintenabilité / Haute | Code smell | 2min |

#### `backendApi/app/nodes/transforms/filter_transform.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 46 | Refactor this function to reduce its Cognitive Complexity from 40 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 30min |

#### `backendApi/app/nodes/transforms/flatten_transform.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 27 | Refactor this function to reduce its Cognitive Complexity from 28 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 18min |

#### `backendApi/app/nodes/transforms/merge_transform.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 45 | Refactor this function to reduce its Cognitive Complexity from 24 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 14min |
| 109 | Refactor this function to reduce its Cognitive Complexity from 124 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 1h54min |

#### `backendApi/app/routes/api.py` — 14

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 28 | Refactor this function to reduce its Cognitive Complexity from 23 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 13min |
| 70 | Document this HTTPException with status code 404 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 94 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 101 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 117 | Document this HTTPException with status code 400 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 128 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 137 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 166 | Document this HTTPException with status code 404 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 175 | Document this HTTPException with status code 400 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 205 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 212 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 228 | Document this HTTPException with status code 400 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 239 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 248 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |

#### `backendApi/app/routes/datasets.py` — 19

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 43 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 62 | Document this HTTPException with status code 404 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 68 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 90 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 118 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 124 | Document this HTTPException with status code 400 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 129 | Document this HTTPException with status code 400 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 145 | Document this HTTPException with status code 400 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 154 | Document this HTTPException with status code 400 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 166 | Document this HTTPException with status code 400 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 171 | Document this HTTPException with status code 413 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 176 | Use an asynchronous file API instead of synchronous open() in this async function. <sub>async, trio, asyncio, anyio</sub> | `python:S7493` | Fiabilité / Haute | Bug | 5min |
| 328 | Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 9min |
| 425 | Refactor this function to reduce its Cognitive Complexity from 23 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 13min |
| 461 | Rename this loop variable; it shadows the outer loop variable "key". <sub>confusing, pitfall</sub> | `python:S8510` | Fiabilité / Haute, Maintenabilité / Haute | Code smell | 2min |
| 471 | Refactor this function to reduce its Cognitive Complexity from 30 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 20min |
| 647 | Refactor this function to reduce its Cognitive Complexity from 28 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 18min |
| 804 | Refactor this function to reduce its Cognitive Complexity from 26 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 16min |
| 857 | Refactor this function to reduce its Cognitive Complexity from 39 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 29min |

#### `backendApi/app/routes/output.py` — 15

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 31 | Refactor this function to reduce its Cognitive Complexity from 25 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 15min |
| 69 | Document this HTTPException with status code 404 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 100 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 107 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 123 | Document this HTTPException with status code 400 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 134 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 143 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 146 | Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 11min |
| 175 | Document this HTTPException with status code 404 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 186 | Document this HTTPException with status code 400 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 217 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 224 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 240 | Document this HTTPException with status code 400 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 251 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 260 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |

#### `backendApi/app/routes/ptx.py` — 23

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 11 | Import only needed names or import the module and then use its members. <sub>bad-practice, pitfall</sub> | `python:S2208` | Maintenabilité / Haute | Code smell | 5min |
| 122 | Document this HTTPException with status code 400 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 157 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 177 | Use an async HTTP client in this async function instead of a synchronous one. <sub>async, trio, asyncio, anyio, http</sub> | `python:S7499` | Fiabilité / Haute | Bug | 5min |
| 185 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 256 | Refactor this function to reduce its Cognitive Complexity from 39 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 29min |
| 277 | Specify an exception class to catch or reraise the exception <sub>error-handling, bad-practice, suspicious</sub> | `python:S5754` | Maintenabilité / Haute | Code smell | 5min |
| 286 | Specify an exception class to catch or reraise the exception <sub>error-handling, bad-practice, suspicious</sub> | `python:S5754` | Maintenabilité / Haute | Code smell | 5min |
| 335 | Specify an exception class to catch or reraise the exception <sub>error-handling, bad-practice, suspicious</sub> | `python:S5754` | Maintenabilité / Haute | Code smell | 5min |
| 440 | Refactor this function to reduce its Cognitive Complexity from 75 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 1h5min |
| 539 | Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 9min |
| 557 | Use an async HTTP client in this async function instead of a synchronous one. <sub>async, trio, asyncio, anyio, http</sub> | `python:S7499` | Fiabilité / Haute | Bug | 5min |
| 581 | Refactor this function to reduce its Cognitive Complexity from 35 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 25min |
| 635 | Use an async HTTP client in this async function instead of a synchronous one. <sub>async, trio, asyncio, anyio, http</sub> | `python:S7499` | Fiabilité / Haute | Bug | 5min |
| 734 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 785 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 835 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 838 | Refactor this function to reduce its Cognitive Complexity from 26 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 16min |
| 847 | Document this HTTPException with status code 404 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 849 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 859 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 867 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 875 | Use an async HTTP client in this async function instead of a synchronous one. <sub>async, trio, asyncio, anyio, http</sub> | `python:S7499` | Fiabilité / Haute | Bug | 5min |

#### `backendApi/app/routes/workflows.py` — 14

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 59 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 108 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 331 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 388 | Document this HTTPException with status code 400 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 399 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 434 | Document this HTTPException with status code 404 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 444 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 493 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 538 | Document this HTTPException with status code 404 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 547 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 604 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 667 | Document this HTTPException with status code 404 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 676 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |
| 721 | Document this HTTPException with status code 500 in the "responses" parameter. <sub>fastapi, openapi, documentation</sub> | `python:S8415` | Maintenabilité / Haute | Code smell | 5min |

#### `backendApi/app/services/dataset_service.py` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 324 | Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 9min |
| 515 | Refactor this function to reduce its Cognitive Complexity from 20 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 10min |
| 579 | Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 7min |
| 637 | Refactor this function to reduce its Cognitive Complexity from 53 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 43min |

#### `backendApi/app/services/migration_service.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 23 | Use an asynchronous file API instead of synchronous open() in this async function. <sub>async, trio, asyncio, anyio</sub> | `python:S7493` | Fiabilité / Haute | Bug | 5min |

#### `backendApi/app/utils/auth_utils.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 232 | Refactor this function to reduce its Cognitive Complexity from 20 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 10min |

#### `backendApi/app/utils/drupal_filter_converter.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 103 | Refactor this function to reduce its Cognitive Complexity from 37 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 27min |
| 187 | Refactor this function to reduce its Cognitive Complexity from 23 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 13min |

#### `backendApi/app/utils/security.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 62 | Refactor this function to reduce its Cognitive Complexity from 20 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 10min |

#### `backendApi/app/utils/utils.py` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 100 | Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 7min |
| 179 | Refactor this function to reduce its Cognitive Complexity from 83 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 1h13min |
| 325 | Refactor this function to reduce its Cognitive Complexity from 72 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 1h2min |
| 567 | Refactor this function to reduce its Cognitive Complexity from 37 to the 15 allowed. <sub>brain-overload</sub> | `python:S3776` | Maintenabilité / Haute | Code smell | 27min |

#### `frontendApp/src/app/components/main/render/render.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 155 | Refactor this function to reduce its Cognitive Complexity from 30 to the 15 allowed. <sub>brain-overload</sub> | `typescript:S3776` | Maintenabilité / Haute | Code smell | 20min |

#### `frontendApp/src/app/components/main/transformation/transformation.component.spec.ts` _(test)_ — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 94 | Unexpected `await` of a non-Promise (non-"Thenable") value. <sub>es2017</sub> | `typescript:S4123` | Maintenabilité / Haute | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/json-inputs-widget/json-inputs-widget.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 25 | Unknown type selector "ace" | `css:S4670` | Fiabilité / Haute | Bug | 5min |

#### `frontendApp/src/app/components/widgets/text-display-widget/text-display-widget.component.spec.ts` _(test)_ — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 56 | Unexpected `await` of a non-Promise (non-"Thenable") value. <sub>es2017</sub> | `typescript:S4123` | Maintenabilité / Haute | Code smell | 1min |

#### `frontendApp/src/app/core/contextMenuDaav.ts` — 5

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 41 | Unexpected var, use let or const instead. <sub>es2015, bad-practice</sub> | `typescript:S3504` | Maintenabilité / Haute | Code smell | 5min |
| 42 | Unexpected var, use let or const instead. <sub>es2015, bad-practice</sub> | `typescript:S3504` | Maintenabilité / Haute | Code smell | 5min |
| 47 | Unexpected var, use let or const instead. <sub>es2015, bad-practice</sub> | `typescript:S3504` | Maintenabilité / Haute | Code smell | 5min |
| 57 | Unexpected var, use let or const instead. <sub>es2015, bad-practice</sub> | `typescript:S3504` | Maintenabilité / Haute | Code smell | 5min |
| 104 | Unexpected var, use let or const instead. <sub>es2015, bad-practice</sub> | `typescript:S3504` | Maintenabilité / Haute | Code smell | 5min |

#### `frontendApp/src/app/core/presets/CustomDock/index.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 88 | Prefer `beforeChild.before(element)` over `container.insertBefore(element, beforeChild)`. <sub>modernization, dom, best-practice</sub> | `typescript:S7768` | Maintenabilité / Haute | Code smell | 5min |

#### `frontendApp/src/app/main/main.page.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 96 | Unexpected empty method 'ionViewWillEnter'. <sub>suspicious</sub> | `typescript:S1186` | Maintenabilité / Haute | Code smell | 5min |

#### `frontendApp/src/app/models/data-mapper-types.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 166 | Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed. <sub>brain-overload</sub> | `typescript:S3776` | Maintenabilité / Haute | Code smell | 9min |
| 223 | Refactor this function to reduce its Cognitive Complexity from 20 to the 15 allowed. <sub>brain-overload</sub> | `typescript:S3776` | Maintenabilité / Haute | Code smell | 10min |

#### `frontendApp/src/app/nodes/input/input-data-block.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 128 | Refactor this code to not nest functions more than 4 levels deep. <sub>brain-overload</sub> | `typescript:S2004` | Maintenabilité / Haute | Code smell | 20min |
| 176 | Unexpected empty method 'dataSourceChange'. <sub>suspicious</sub> | `typescript:S1186` | Maintenabilité / Haute | Code smell | 5min |
| 214 | Unexpected empty method 'testConnection'. <sub>suspicious</sub> | `typescript:S1186` | Maintenabilité / Haute | Code smell | 5min |

#### `frontendApp/src/app/nodes/inputs/data-api-block.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 13 | Unexpected empty method 'execute'. <sub>suspicious</sub> | `typescript:S1186` | Maintenabilité / Haute | Code smell | 5min |

#### `frontendApp/src/app/nodes/inputs/data-elastic-block.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 13 | Unexpected empty method 'execute'. <sub>suspicious</sub> | `typescript:S1186` | Maintenabilité / Haute | Code smell | 5min |

#### `frontendApp/src/app/nodes/inputs/data-lrs-block.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 13 | Unexpected empty method 'execute'. <sub>suspicious</sub> | `typescript:S1186` | Maintenabilité / Haute | Code smell | 5min |

#### `frontendApp/src/app/nodes/inputs/data-mongo-block.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 309 | Unexpected empty method 'execute'. <sub>suspicious</sub> | `typescript:S1186` | Maintenabilité / Haute | Code smell | 5min |

#### `frontendApp/src/app/nodes/inputs/data-mysql-block.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 298 | Unexpected empty method 'execute'. <sub>suspicious</sub> | `typescript:S1186` | Maintenabilité / Haute | Code smell | 5min |

#### `frontendApp/src/app/nodes/outputs/api-output.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 49 | Unexpected empty method 'addSourceSelect'. <sub>suspicious</sub> | `typescript:S1186` | Maintenabilité / Haute | Code smell | 5min |

#### `frontendApp/src/app/nodes/transforms/merge-transform.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 89 | Refactor this function to reduce its Cognitive Complexity from 39 to the 15 allowed. <sub>brain-overload</sub> | `typescript:S3776` | Maintenabilité / Haute | Code smell | 29min |

#### `frontendApp/src/app/pages/register/register.page.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 181 | Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed. <sub>brain-overload</sub> | `typescript:S3776` | Maintenabilité / Haute | Code smell | 6min |

#### `frontendApp/src/app/services/dataset.service.spec.ts` _(test)_ — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 64 | Make sure publicly writable directories are used safely here. <sub>cwe, former-hotspot</sub> | `typescript:S5443` | Sécurité / Haute | Vulnérabilité | 30min |
| 68 | Make sure publicly writable directories are used safely here. <sub>cwe, former-hotspot</sub> | `typescript:S5443` | Sécurité / Haute | Vulnérabilité | 30min |
| 134 | Make sure publicly writable directories are used safely here. <sub>cwe, former-hotspot</sub> | `typescript:S5443` | Sécurité / Haute | Vulnérabilité | 30min |

#### `frontendApp/src/app/services/token.service.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 20 | Refactor this asynchronous operation outside of the constructor. <sub>es2017, type-dependent</sub> | `typescript:S7059` | Fiabilité / Haute, Maintenabilité / Haute | Code smell | 5min |

### Moyenne (261)

#### `backendApi/app/config/database.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 41 | Use asynchronous features in this function or remove the `async` keyword. <sub>async</sub> | `python:S7503` | Fiabilité / Basse, Maintenabilité / Moyenne | Code smell | 5min |

#### `backendApi/app/config/logging.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 61 | Remove this commented out code. <sub>unused</sub> | `python:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `backendApi/app/core/execution_context.py` — 6

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 123 | Extract this nested conditional expression into an independent statement. <sub>confusing</sub> | `python:S3358` | Maintenabilité / Moyenne | Code smell | 5min |
| 124 | Extract this nested conditional expression into an independent statement. <sub>confusing</sub> | `python:S3358` | Maintenabilité / Moyenne | Code smell | 5min |
| 125 | Extract this nested conditional expression into an independent statement. <sub>confusing</sub> | `python:S3358` | Maintenabilité / Moyenne | Code smell | 5min |
| 128 | Extract this nested conditional expression into an independent statement. <sub>confusing</sub> | `python:S3358` | Maintenabilité / Moyenne | Code smell | 5min |
| 129 | Extract this nested conditional expression into an independent statement. <sub>confusing</sub> | `python:S3358` | Maintenabilité / Moyenne | Code smell | 5min |
| 130 | Extract this nested conditional expression into an independent statement. <sub>confusing</sub> | `python:S3358` | Maintenabilité / Moyenne | Code smell | 5min |

#### `backendApi/app/middleware/auth.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 43 | Use asynchronous features in this function or remove the `async` keyword. <sub>async</sub> | `python:S7503` | Fiabilité / Basse, Maintenabilité / Moyenne | Code smell | 5min |
| 66 | Use asynchronous features in this function or remove the `async` keyword. <sub>async</sub> | `python:S7503` | Fiabilité / Basse, Maintenabilité / Moyenne | Code smell | 5min |

#### `backendApi/app/models/interface/auth_interface.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | "password" detected here, review this potentially hard-coded credential. <sub>cwe, former-hotspot</sub> | `python:S2068` | Sécurité / Moyenne | Vulnérabilité | 30min |

#### `backendApi/app/models/interface/pdc_interface.py` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 316 | Replace the type hint "Input" with "Optional[Input]" or don't assign "None" to "input" <sub>typing, confusing</sub> | `python:S5890` | Maintenabilité / Moyenne | Code smell | 5min |
| 317 | Replace the type hint "Output" with "Optional[Output]" or don't assign "None" to "output" <sub>typing, confusing</sub> | `python:S5890` | Maintenabilité / Moyenne | Code smell | 5min |
| 378 | Replace the type hint "Union[str, list[B2CDescription]]" with "Optional[Union[str, list[B2CDescription]]]" or don't assign "None" to "b2cDescription" <sub>typing, confusing</sub> | `python:S5890` | Maintenabilité / Moyenne | Code smell | 5min |

#### `backendApi/app/nodes/inputs/data_mysql_block.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 57 | Add replacement fields or use a normal string instead of an f-string. <sub>confusing</sub> | `python:S3457` | Maintenabilité / Moyenne | Code smell | 1min |

#### `backendApi/app/nodes/outputs/example_ouput.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 29 | Add replacement fields or use a normal string instead of an f-string. <sub>confusing</sub> | `python:S3457` | Maintenabilité / Moyenne | Code smell | 1min |

#### `backendApi/app/nodes/outputs/file_output.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 221 | Replace the type hint "str" with "Optional[str]" or don't assign "None" to "datasetId" <sub>typing, confusing</sub> | `python:S5890` | Maintenabilité / Moyenne | Code smell | 5min |

#### `backendApi/app/nodes/outputs/mysql_output.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 86 | Remove this commented out code. <sub>unused</sub> | `python:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `backendApi/app/nodes/transforms/flatten_transform.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 43 | Add replacement fields or use a normal string instead of an f-string. <sub>confusing</sub> | `python:S3457` | Maintenabilité / Moyenne | Code smell | 1min |
| 59 | Add replacement fields or use a normal string instead of an f-string. <sub>confusing</sub> | `python:S3457` | Maintenabilité / Moyenne | Code smell | 1min |

#### `backendApi/app/nodes/transforms/merge_transform.py` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 144 | Replace this generic exception class with a more specific one. <sub>cwe, error-handling</sub> | `python:S112` | Maintenabilité / Moyenne | Code smell | 20min |
| 187 | Remove this assignment to local variable 'file_path'; the value is never used. <sub>cwe, unused</sub> | `python:S1854` | Maintenabilité / Moyenne | Code smell | 1min |
| 207 | Replace this generic exception class with a more specific one. <sub>cwe, error-handling</sub> | `python:S112` | Maintenabilité / Moyenne | Code smell | 20min |

#### `backendApi/app/routes/datasets.py` — 28

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 186 | Rename function "getContentDataset" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 220 | Rename function "getDfContentDataset" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 252 | Rename function "getDfFromJson" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 273 | Use asynchronous features in this function or remove the `async` keyword. <sub>async</sub> | `python:S7503` | Fiabilité / Basse, Maintenabilité / Moyenne | Code smell | 5min |
| 307 | Rename function "getAll" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 322 | Rename function "getTables" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 328 | Rename function "getMysqlContent" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 395 | Use asynchronous features in this function or remove the `async` keyword. <sub>async</sub> | `python:S7503` | Fiabilité / Basse, Maintenabilité / Moyenne | Code smell | 5min |
| 425 | Rename function "rem_ObjectId" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 471 | Rename function "getMongoContent" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 530 | Use asynchronous features in this function or remove the `async` keyword. <sub>async</sub> | `python:S7503` | Fiabilité / Basse, Maintenabilité / Moyenne | Code smell | 5min |
| 559 | Rename function "getElasticContent" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 599 | Remove the unused function parameter "datasetParams". <sub>unused</sub> | `python:S1172` | Maintenabilité / Moyenne | Code smell | 5min |
| 599 | Remove the unused function parameter "pagination". <sub>unused</sub> | `python:S1172` | Maintenabilité / Moyenne | Code smell | 5min |
| 599 | Rename function "getPTXContent" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 631 | Rename function "apiContent" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 647 | Rename function "getApiContent" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 735 | Rename function "toRow" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 737 | Replace "list(...)[0]" with "next(iter(...))" to avoid materializing the entire iterable. <sub>performance, pythonic</sub> | `python:S8519` | Fiabilité / Moyenne | Code smell | 5min |
| 749 | Rename function "JSONFile" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 755 | Rename function "ColFile" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 773 | Rename function "XLSFile" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 781 | Rename function "AvroFile" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 792 | Rename function "XMLFile" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 804 | Rename function "CSVFile" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 857 | Rename function "getFileContent" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 886 | Replace chained "endswith" calls with a single call using a tuple argument. <sub>performance, pythonic</sub> | `python:S8513` | Maintenabilité / Moyenne | Code smell | 5min |
| 890 | Replace chained "endswith" calls with a single call using a tuple argument. <sub>performance, pythonic</sub> | `python:S8513` | Maintenabilité / Moyenne | Code smell | 5min |

#### `backendApi/app/routes/ptx.py` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 188 | Rename function "executeChainService" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 234 | Either merge this branch with the identical one on line "231" or change one of the implementations. <sub>design, suspicious</sub> | `python:S1871` | Maintenabilité / Moyenne | Code smell | 10min |
| 301 | Extract this nested conditional expression into an independent statement. <sub>confusing</sub> | `python:S3358` | Maintenabilité / Moyenne | Code smell | 5min |
| 539 | Rename function "get_service_Chain" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |

#### `backendApi/app/scripts/migrate_ownership.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 72 | Add replacement fields or use a normal string instead of an f-string. <sub>confusing</sub> | `python:S3457` | Maintenabilité / Moyenne | Code smell | 1min |

#### `backendApi/app/services/auth_service.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 239 | Use asynchronous features in this function or remove the `async` keyword. <sub>async</sub> | `python:S7503` | Fiabilité / Basse, Maintenabilité / Moyenne | Code smell | 5min |

#### `backendApi/app/services/dataset_service.py` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 48 | Replace the type hint "PdcChainHeaders" with "Optional[PdcChainHeaders]" or don't assign "None" to this expression <sub>typing, confusing</sub> | `python:S5890` | Maintenabilité / Moyenne | Code smell | 5min |
| 437 | Replace this generic exception class with a more specific one. <sub>cwe, error-handling</sub> | `python:S112` | Maintenabilité / Moyenne | Code smell | 20min |
| 440 | Replace this generic exception class with a more specific one. <sub>cwe, error-handling</sub> | `python:S112` | Maintenabilité / Moyenne | Code smell | 20min |

#### `backendApi/app/services/pdc_service.py` — 6

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 108 | Return a value of type "Optional[str]" instead of "dict" or update function "get_provider_name_and_img_from_contract" type hint. <sub>typing</sub> | `python:S5886` | Maintenabilité / Moyenne | Code smell | 5min |
| 115 | Return a value of type "Optional[str]" instead of "dict" or update function "get_provider_name_and_img_from_contract" type hint. <sub>typing</sub> | `python:S5886` | Maintenabilité / Moyenne | Code smell | 5min |
| 121 | Return a value of type "Optional[str]" instead of "dict" or update function "get_provider_name_and_img_from_contract" type hint. <sub>typing</sub> | `python:S5886` | Maintenabilité / Moyenne | Code smell | 5min |
| 148 | Remove this "timeout" parameter and use a timeout context manager instead. <sub>async, trio, asyncio, anyio</sub> | `python:S7483` | Maintenabilité / Moyenne | Code smell | 5min |
| 156 | Remove this "timeout" parameter and use a timeout context manager instead. <sub>async, trio, asyncio, anyio</sub> | `python:S7483` | Maintenabilité / Moyenne | Code smell | 5min |
| 164 | Remove this "timeout" parameter and use a timeout context manager instead. <sub>async, trio, asyncio, anyio</sub> | `python:S7483` | Maintenabilité / Moyenne | Code smell | 5min |

#### `backendApi/app/services/user_service.py` — 5

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 360 | "password" detected here, review this potentially hard-coded credential. <sub>cwe, former-hotspot</sub> | `python:S2068` | Sécurité / Moyenne | Vulnérabilité | 30min |
| 386 | Use asynchronous features in this function or remove the `async` keyword. <sub>async</sub> | `python:S7503` | Fiabilité / Basse, Maintenabilité / Moyenne | Code smell | 5min |
| 411 | Use asynchronous features in this function or remove the `async` keyword. <sub>async</sub> | `python:S7503` | Fiabilité / Basse, Maintenabilité / Moyenne | Code smell | 5min |
| 430 | Use asynchronous features in this function or remove the `async` keyword. <sub>async</sub> | `python:S7503` | Fiabilité / Basse, Maintenabilité / Moyenne | Code smell | 5min |
| 455 | Use asynchronous features in this function or remove the `async` keyword. <sub>async</sub> | `python:S7503` | Fiabilité / Basse, Maintenabilité / Moyenne | Code smell | 5min |

#### `backendApi/app/utils/auth_utils.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 222 | Return a value of type "datetime" instead of "NoneType" or update function "ensure_utc_aware" type hint. <sub>typing</sub> | `python:S5886` | Maintenabilité / Moyenne | Code smell | 5min |
| 232 | Use asynchronous features in this function or remove the `async` keyword. <sub>async</sub> | `python:S7503` | Fiabilité / Basse, Maintenabilité / Moyenne | Code smell | 5min |

#### `backendApi/app/utils/utils.py` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 170 | Fix this equality check; Previous type checks suggest that operands have incompatible types. <sub>typing, confusing</sub> | `python:S5864` | Maintenabilité / Moyenne | Code smell | 5min |
| 473 | Rename function "decodeDictionary" to match the regular expression ^[a-z_][a-z0-9_]*$. <sub>convention, pep</sub> | `python:S1542` | Maintenabilité / Moyenne | Code smell | 10min |
| 560 | Return a value of type "dict" instead of "list" or update function "filter_data_with_duckdb" type hint. <sub>typing</sub> | `python:S5886` | Maintenabilité / Moyenne | Code smell | 5min |
| 628 | Add replacement fields or use a normal string instead of an f-string. <sub>confusing</sub> | `python:S3457` | Maintenabilité / Moyenne | Code smell | 1min |

#### `docs/index.html` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 3 | Add a <title> tag to this page. <sub>user-experience</sub> | `Web:PageWithoutTitleCheck` | Fiabilité / Moyenne | Bug | 5min |
| 5 | Remove this meta refresh tag. <sub>user-experience</sub> | `Web:MetaRefreshCheck` | Maintenabilité / Moyenne | Code smell | 20min |

#### `frontendApp/src/app/app.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Empty source | `css:S4667` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/components/confirm-deletion-modal/confirm-deletion-modal.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Empty source | `css:S4667` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/components/connections/connections.component.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this commented out code. <sub>unused</sub> | `typescript:S125` | Maintenabilité / Moyenne | Code smell | 5min |
| 3 | Remove this commented out code. <sub>unused</sub> | `typescript:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/dashboards/dashboard/dashboard.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Empty source | `css:S4667` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/components/dashboards/file-dashboard/file-dashboard.component.html` — 7

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 8 | A form label must be associated with a control and have accessible text. <sub>accessibility</sub> | `Web:S6853` | Fiabilité / Moyenne | Code smell | 5min |
| 13 | A form label must be associated with a control and have accessible text. <sub>accessibility</sub> | `Web:S6853` | Fiabilité / Moyenne | Code smell | 5min |
| 18 | A form label must be associated with a control and have accessible text. <sub>accessibility</sub> | `Web:S6853` | Fiabilité / Moyenne | Code smell | 5min |
| 23 | A form label must be associated with a control and have accessible text. <sub>accessibility</sub> | `Web:S6853` | Fiabilité / Moyenne | Code smell | 5min |
| 28 | A form label must be associated with a control and have accessible text. <sub>accessibility</sub> | `Web:S6853` | Fiabilité / Moyenne | Code smell | 5min |
| 33 | A form label must be associated with a control and have accessible text. <sub>accessibility</sub> | `Web:S6853` | Fiabilité / Moyenne | Code smell | 5min |
| 38 | A form label must be associated with a control and have accessible text. <sub>accessibility</sub> | `Web:S6853` | Fiabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/dashboards/file-dashboard/file-dashboard.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 74 | Text does not meet the minimal contrast requirement with its background. <sub>css, accessibility, wcag, contrast</sub> | `css:S7924` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/dashboards/ptxdashboard/ptxdashboard.component.scss` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 203 | Text does not meet the minimal contrast requirement with its background. <sub>css, accessibility, wcag, contrast</sub> | `css:S7924` | Maintenabilité / Moyenne | Code smell | 5min |
| 209 | Text does not meet the minimal contrast requirement with its background. <sub>css, accessibility, wcag, contrast</sub> | `css:S7924` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/dashboards/ptxdashboard/ptxdashboard.component.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 63 | Member '_snackBar' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 76 | Remove this commented out code. <sub>unused</sub> | `typescript:S125` | Maintenabilité / Moyenne | Code smell | 5min |
| 256 | Remove this commented out code. <sub>unused</sub> | `typescript:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/data-filter/data-filter.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Empty source | `css:S4667` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/components/data-mapper/data-mapper.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 146 | Text does not meet the minimal contrast requirement with its background. <sub>css, accessibility, wcag, contrast</sub> | `css:S7924` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/data-mapper/data-mapper.component.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 15 | Member 'destroy$' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 53 | 'If' statement should not be the only statement in 'else' block | `typescript:S6660` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/datasets-modal/datasets-modal.component.html` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 217 | Remove this commented out code. <sub>unused</sub> | `Web:AvoidCommentedOutCodeCheck` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/datasets-modal/datasets-modal.component.scss` — 6

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 36 | Duplicate selector "ion-modal .ion-page", first used at line 23 | `css:S4666` | Maintenabilité / Moyenne | Code smell | 1min |
| 154 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |
| 195 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |
| 196 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |
| 197 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |
| 198 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/datasets-modal/datasets-modal.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 216 | Expected an assignment or function call and instead saw an expression. <sub>cwe, unused</sub> | `typescript:S905` | Fiabilité / Moyenne | Bug | 10min |

#### `frontendApp/src/app/components/main/datasets/datasets.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 130 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/main/datasets/datasets.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 2 | Remove this commented out code. <sub>unused</sub> | `typescript:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/main/render/render.component.html` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 49 | A form label must be associated with a control and have accessible text. <sub>accessibility</sub> | `Web:S6853` | Fiabilité / Moyenne | Code smell | 5min |
| 107 | Add subtitles and description files for this video. <sub>accessibility, html5</sub> | `Web:S4084` | Maintenabilité / Moyenne | Code smell | 5min |
| 180 | Add subtitles and description files for this video. <sub>accessibility, html5</sub> | `Web:S4084` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/main/render/render.component.scss` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 158 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |
| 235 | Duplicate property "overflow" | `css:S4656` | Fiabilité / Moyenne | Bug | 1min |
| 236 | Duplicate property "padding" | `css:S4656` | Fiabilité / Moyenne | Bug | 1min |

#### `frontendApp/src/app/components/main/render/render.component.ts` — 7

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 55 | Member 'render: Renderer2' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 55 | Member 'cd : ChangeDetectorRef' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 106 | Remove this commented out code. <sub>unused</sub> | `typescript:S125` | Maintenabilité / Moyenne | Code smell | 5min |
| 209 | Extract the assignment of "keys" from this expression. <sub>cwe, suspicious</sub> | `typescript:S1121` | Maintenabilité / Moyenne | Code smell | 5min |
| 209 | Extract the assignment of "keys" from this expression. <sub>cwe, suspicious</sub> | `typescript:S1121` | Maintenabilité / Moyenne | Code smell | 5min |
| 230 | Expected the Promise rejection reason to be an Error. <sub>type-dependent</sub> | `typescript:S6671` | Fiabilité / Moyenne | Code smell | 5min |
| 245 | Expected the Promise rejection reason to be an Error. <sub>type-dependent</sub> | `typescript:S6671` | Fiabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/main/transformation/transformation.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 25 | Member 'datasetService: DatasetService' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/components/nodes/input/nodes.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 35 | Member 'cdr: ChangeDetectorRef' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/components/nodes/nodes-main.scss` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 30 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |
| 34 | Duplicate property "font-family" | `css:S4656` | Fiabilité / Moyenne | Bug | 1min |
| 65 | Duplicate property "font-family" | `css:S4656` | Fiabilité / Moyenne | Bug | 1min |

#### `frontendApp/src/app/components/nodes/output/nodes.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 35 | Member 'cdr: ChangeDetectorRef' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/components/nodes/transform/nodes.component.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 35 | Member 'cdr: ChangeDetectorRef' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 36 | Remove this commented out code. <sub>unused</sub> | `typescript:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/sockets/deep-socket-component/deep-socket.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 16 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/sockets/deep-socket-component/deep-socket.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 18 | Member 'cdr: ChangeDetectorRef' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/components/sockets/flat-socket-component/flat-socket.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 16 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/sockets/flat-socket-component/flat-socket.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 18 | Member 'cdr: ChangeDetectorRef' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/components/sockets/global-socket-component/global-socket.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 17 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/sockets/global-socket-component/global-socket.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 18 | Member 'cdr: ChangeDetectorRef' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/components/sockets/socket-component/socket.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 15 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/sockets/socket-component/socket.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 18 | Member 'cdr: ChangeDetectorRef' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/components/sockets/socket.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 14 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/transformation-modal/transformation-modal.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Empty source | `css:S4667` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/components/user-profile/user-profile.component.ts` — 7

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 35 | Member 'formBuilder: FormBuilder' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 36 | Member 'authService: AuthService' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 37 | Member 'modalController: ModalController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 38 | Member 'toastController: ToastController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 39 | Member 'alertController: AlertController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 40 | Member 'loadingController: LoadingController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 41 | Member 'router: Router' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/components/widgets/auto-complete-widget/input-auto-complete-widget.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Empty source | `css:S4667` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/button-widget/button-widget.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Empty source | `css:S4667` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/checkbox-widget/checkbox-widget.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Empty source | `css:S4667` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/checkbox-widget/checkbox-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 43 | Remove this commented out code. <sub>unused</sub> | `typescript:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/data-filter-widget/data-filter-widget.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Empty source | `css:S4667` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/select-widget/select-widget.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Empty source | `css:S4667` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/status-component/status-component.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 41 | Remove this useless assignment to variable "ev". <sub>cwe, unused</sub> | `typescript:S1854` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/text-display-widget/text-display-widget.component.html` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 2 | A form label must be associated with a control and have accessible text. <sub>accessibility</sub> | `Web:S6853` | Fiabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/components/workflow-update-rules-modal/workflow-update-rules-modal.component.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Empty source | `css:S4667` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/components/workflow-update-rules-modal/workflow-update-rules-modal.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 25 | Member 'dialogRef' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/core/contextMenuDaav.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 38 | Remove this commented out code. <sub>unused</sub> | `typescript:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/core/workflow-editor.ts` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 170 | Remove this commented out code. <sub>unused</sub> | `typescript:S125` | Maintenabilité / Moyenne | Code smell | 5min |
| 397 | Remove this commented out code. <sub>unused</sub> | `typescript:S125` | Maintenabilité / Moyenne | Code smell | 5min |
| 486 | Expected an assignment or function call and instead saw an expression. <sub>cwe, unused</sub> | `typescript:S905` | Fiabilité / Moyenne | Bug | 10min |
| 573 | Expected an assignment or function call and instead saw an expression. <sub>cwe, unused</sub> | `typescript:S905` | Fiabilité / Moyenne | Bug | 10min |

#### `frontendApp/src/app/guards/auth.guard.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 23 | Member 'authService: AuthService' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 24 | Member 'router: Router' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/interceptors/auth.interceptor.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 13 | Member 'tokenService: TokenService' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/interceptors/error.interceptor.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 21 | Member 'authService: AuthService' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 22 | Member 'router: Router' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 23 | Member 'toastController: ToastController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/main/main.page.html` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 44 | Remove this commented out code. <sub>unused</sub> | `Web:AvoidCommentedOutCodeCheck` | Maintenabilité / Moyenne | Code smell | 5min |
| 54 | Remove this commented out code. <sub>unused</sub> | `Web:AvoidCommentedOutCodeCheck` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/main/main.page.scss` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 18 | Duplicate property "width" | `css:S4656` | Fiabilité / Moyenne | Bug | 1min |
| 62 | Missing generic font family | `css:S4649` | Fiabilité / Moyenne | Bug | 1min |

#### `frontendApp/src/app/main/main.page.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 78 | Member 'modalController: ModalController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 78 | Member 'cd: ChangeDetectorRef' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/models/data-mapper-types.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 120 | Expected an assignment or function call and instead saw an expression. <sub>cwe, unused</sub> | `typescript:S905` | Fiabilité / Moyenne | Bug | 10min |

#### `frontendApp/src/app/nodes/input/input-data-block.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 119 | Remove this useless assignment to variable "result". <sub>cwe, unused</sub> | `typescript:S1854` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/nodes/inputs/data-file-block.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 40 | Promise-returning method provided where a void return was expected by extended/implemented type 'InputDataBlock<PandasSchema, NodeDataPandasDf>'. <sub>async, es2017, type-dependent, promise</sub> | `typescript:S6544` | Fiabilité / Moyenne | Bug | 5min |

#### `frontendApp/src/app/nodes/inputs/data-mongo-block.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 36 | Member 'node' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 66 | Promise-returning method provided where a void return was expected by extended/implemented type 'InputDataBlock<PandasSchema, NodeDataPandasDf>'. <sub>async, es2017, type-dependent, promise</sub> | `typescript:S6544` | Fiabilité / Moyenne | Bug | 5min |

#### `frontendApp/src/app/nodes/inputs/data-mysql-block.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 30 | Member 'node' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 60 | Promise-returning method provided where a void return was expected by extended/implemented type 'InputDataBlock<MysqlSchema, NodeDataMysql>'. <sub>async, es2017, type-dependent, promise</sub> | `typescript:S6544` | Fiabilité / Moyenne | Bug | 5min |

#### `frontendApp/src/app/nodes/inputs/example-input.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 9 | Remove this commented out code. <sub>unused</sub> | `typescript:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/nodes/inputs/service-chain-input.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 27 | Member 'node' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 47 | Remove this conditional structure or edit its code blocks so that they're not all the same. | `typescript:S3923` | Fiabilité / Moyenne | Bug | 15min |
| 52 | This branch's code block is the same as the block for the branch on line 47. <sub>design, suspicious</sub> | `typescript:S1871` | Maintenabilité / Moyenne | Code smell | 10min |

#### `frontendApp/src/app/nodes/node-block.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 28 | Member 'statusControl' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 135 | Remove this redundant type alias and replace its occurrences with "string". | `typescript:S6564` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/nodes/output/output-data-block.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 62 | Remove this useless assignment to variable "result". <sub>cwe, unused</sub> | `typescript:S1854` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/nodes/outputs/api-output.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 17 | Member 'node' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 184 | Unnecessary escape character: \/. | `typescript:S6535` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/nodes/outputs/file-output.spec.ts` _(test)_ — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 28 | Remove this useless assignment to variable "mockHttp". <sub>cwe, unused</sub> | `typescript:S1854` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/nodes/outputs/file-output.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 28 | Member 'node' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/nodes/outputs/mongo-output.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 28 | Member 'node' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/nodes/outputs/mysql-output.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 27 | Member 'node' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/nodes/outputs/pdc-output.ts` — 5

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 23 | Member 'node' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 112 | Unnecessary escape character: \.. | `typescript:S6535` | Maintenabilité / Moyenne | Code smell | 5min |
| 113 | Unnecessary escape character: \-. | `typescript:S6535` | Maintenabilité / Moyenne | Code smell | 5min |
| 247 | Remove this useless assignment to variable "baseUrl". <sub>cwe, unused</sub> | `typescript:S1854` | Maintenabilité / Moyenne | Code smell | 1min |
| 341 | Remove this conditional structure or edit its code blocks so that they're not all the same. | `typescript:S3923` | Fiabilité / Moyenne | Bug | 15min |

#### `frontendApp/src/app/nodes/outputs/service-chain-output.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 19 | Member 'node' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/nodes/transforms/filter-transform.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 47 | Remove this useless assignment to variable "source". <sub>cwe, unused</sub> | `typescript:S1854` | Maintenabilité / Moyenne | Code smell | 1min |
| 55 | Use `.indexOf()` instead of `.findIndex()` when looking for the index of an item. <sub>performance, array, javascript</sub> | `typescript:S7753` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/nodes/transforms/flatten-transform.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 48 | Remove this useless assignment to variable "source". <sub>cwe, unused</sub> | `typescript:S1854` | Maintenabilité / Moyenne | Code smell | 1min |
| 57 | Use `.indexOf()` instead of `.findIndex()` when looking for the index of an item. <sub>performance, array, javascript</sub> | `typescript:S7753` | Maintenabilité / Moyenne | Code smell | 2min |
| 73 | Remove this useless assignment to variable "worflowEditor". <sub>cwe, unused</sub> | `typescript:S1854` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/nodes/transforms/merge-transform.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 52 | Remove this useless assignment to variable "source". <sub>cwe, unused</sub> | `typescript:S1854` | Maintenabilité / Moyenne | Code smell | 1min |
| 61 | Use `.indexOf()` instead of `.findIndex()` when looking for the index of an item. <sub>performance, array, javascript</sub> | `typescript:S7753` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/pages/forgot-password/forgot-password.page.ts` — 5

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 19 | Member 'formBuilder: FormBuilder' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 20 | Member 'authService: AuthService' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 21 | Member 'router: Router' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 22 | Member 'toastController: ToastController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 23 | Member 'loadingController: LoadingController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/pages/login/login.page.ts` — 6

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 19 | Member 'formBuilder: FormBuilder' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 20 | Member 'authService: AuthService' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 21 | Member 'router: Router' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 22 | Member 'route: ActivatedRoute' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 23 | Member 'toastController: ToastController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 24 | Member 'loadingController: LoadingController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/pages/register/register.page.ts` — 5

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 18 | Member 'formBuilder: FormBuilder' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 19 | Member 'authService: AuthService' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 20 | Member 'router: Router' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 21 | Member 'toastController: ToastController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 22 | Member 'loadingController: LoadingController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/pages/reset-password/reset-password.page.ts` — 7

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 20 | Member 'formBuilder: FormBuilder' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 21 | Member 'authService: AuthService' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 22 | Member 'router: Router' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 23 | Member 'route: ActivatedRoute' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 24 | Member 'toastController: ToastController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 25 | Member 'loadingController: LoadingController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 26 | Member 'alertController: AlertController' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/pages/test-composant/test-composant.page.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Empty source | `css:S4667` | Maintenabilité / Moyenne | Code smell | 1min |

#### `frontendApp/src/app/pages/worflow/workflow.page.scss` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 101 | Duplicate property "height" | `css:S4656` | Fiabilité / Moyenne | Bug | 1min |
| 111 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/pages/worflow/workflow.page.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 24 | Member 'injector: Injector' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 24 | Member 'route: ActivatedRoute' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/services/auth.service.ts` — 7

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 27 | Member 'currentUserSubject' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 33 | Member 'http: HttpClient' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 34 | Member 'tokenService: TokenService' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 35 | Member 'baseService: BaseService' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 36 | Member 'router: Router' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 37 | Member 'injector: Injector' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 136 | Expected non-Promise value in a boolean conditional. <sub>async, es2017, type-dependent, promise</sub> | `typescript:S6544` | Fiabilité / Moyenne | Bug | 5min |

#### `frontendApp/src/app/services/dataset.service.ts` — 7

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 28 | Member 'apiUrl' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 32 | Member 'datasetsSignal' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 47 | Member 'http: HttpClient' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 60 | Expected the Promise rejection reason to be an Error. <sub>type-dependent</sub> | `typescript:S6671` | Fiabilité / Moyenne | Code smell | 5min |
| 77 | Expected the Promise rejection reason to be an Error. <sub>type-dependent</sub> | `typescript:S6671` | Fiabilité / Moyenne | Code smell | 5min |
| 94 | Expected the Promise rejection reason to be an Error. <sub>type-dependent</sub> | `typescript:S6671` | Fiabilité / Moyenne | Code smell | 5min |
| 111 | Expected the Promise rejection reason to be an Error. <sub>type-dependent</sub> | `typescript:S6671` | Fiabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/app/services/token.service.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 19 | Member 'storage: Storage' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/services/worflow.service.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 13 | Member 'apiUrl' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 15 | Member 'workflowsSignals' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |
| 18 | Member 'http: HttpClient' is never reassigned; mark it as `readonly`. <sub>type-dependent, confusing</sub> | `typescript:S2933` | Maintenabilité / Moyenne | Code smell | 2min |

#### `frontendApp/src/app/tabs/tabs.page.html` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 2 | Remove this commented out code. <sub>unused</sub> | `Web:AvoidCommentedOutCodeCheck` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/environments/environment.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 17 | Remove this commented out code. <sub>unused</sub> | `typescript:S125` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/global.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 116 | Missing generic font family | `css:S4649` | Fiabilité / Moyenne | Bug | 1min |

#### `frontendApp/src/index.html` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 11 | Meta viewport disables zoom via user-scalable=no. <sub>accessibility, wcag, html</sub> | `Web:S7926` | Maintenabilité / Moyenne | Code smell | 5min |
| 21 | Remove this commented out code. <sub>unused</sub> | `Web:AvoidCommentedOutCodeCheck` | Maintenabilité / Moyenne | Code smell | 5min |

#### `frontendApp/src/theme/ptx.scss` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 2 | Remove this commented out code. <sub>unused</sub> | `css:S125` | Maintenabilité / Moyenne | Code smell | 5min |

### Basse (378)

#### `backendApi/app/core/workflow.py` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 73 | Rename this local variable "nodeInput" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 76 | Rename this local variable "nodeOutput" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 114 | Rename this local variable "outputDict" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/models/interface/dataset_interface.py` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 21 | Make sure using this hardcoded IP address "10.0.0.0" is safe here. <sub>bad-practice, former-hotspot</sub> | `python:S1313` | Sécurité / Basse | Code smell | 30min |
| 22 | Make sure using this hardcoded IP address "172.16.0.0" is safe here. <sub>bad-practice, former-hotspot</sub> | `python:S1313` | Sécurité / Basse | Code smell | 30min |
| 23 | Make sure using this hardcoded IP address "192.168.0.0" is safe here. <sub>bad-practice, former-hotspot</sub> | `python:S1313` | Sécurité / Basse | Code smell | 30min |
| 25 | Make sure using this hardcoded IP address "169.254.0.0" is safe here. <sub>bad-practice, former-hotspot</sub> | `python:S1313` | Sécurité / Basse | Code smell | 30min |

#### `backendApi/app/models/interface/node_data.py` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 41 | Rename this parameter "dataExample" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 88 | Rename this parameter "dataExample" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 98 | Rename this parameter "nodeSchema" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/nodes/inputs/data_file_block.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 72 | Rename this local variable "datasetId" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/nodes/inputs/data_mongo_block.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 40 | Rename this local variable "datasetParam" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 89 | Rename this local variable "datasetId" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/nodes/inputs/data_mysql_block.py` — 5

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 46 | Rename this local variable "parquetSave" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 47 | Rename this local variable "parquetPath" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 58 | Rename this local variable "result_dataFrame" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 148 | Rename this local variable "datasetId" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 156 | Rename this local variable "parquetSave" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/nodes/inputs/service-chain-input.py` — 8

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 47 | Rename this local variable "parquetSave" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 47 | Rename this local variable "inputDataSourceExample" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 59 | Rename this local variable "additionalData" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 63 | Rename this local variable "chainHeaders" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 69 | Rename this local variable "parquetPath" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 145 | Rename this local variable "datasetId" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 152 | Rename this local variable "inputDataSourceExample" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 155 | Rename this local variable "parquetSave" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/nodes/outputs/api_output.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 68 | Replace the unused local variable "token" with "_". <sub>unused</sub> | `python:S1481` | Maintenabilité / Basse | Code smell | 5min |
| 68 | Replace the unused local variable "name" with "_". <sub>unused</sub> | `python:S1481` | Maintenabilité / Basse | Code smell | 5min |

#### `backendApi/app/nodes/outputs/file_output.py` — 24

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 52 | Rename this local variable "fileExist" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 52 | Rename this local variable "fileName" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 52 | Rename this local variable "fileType" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 146 | Rename this local variable "chunkSize" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 147 | Rename this local variable "firstChunk" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 148 | Rename this local variable "parquetFilePath" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 149 | Rename this local variable "parquetFile" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 221 | Rename this local variable "datasetId" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 229 | Remove the unused local variable "e". <sub>unused</sub> | `python:S1481` | Maintenabilité / Basse | Code smell | 5min |
| 233 | Rename this local variable "fileType" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 234 | Rename this local variable "fileName" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 241 | Rename this local variable "fileExist" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 248 | Rename this parameter "fileExist" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 274 | Rename this parameter "fileExist" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 300 | Rename this parameter "chunkSize" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 300 | Rename this parameter "fileExist" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 300 | Rename this parameter "parquetFile" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 306 | Rename this local variable "firstChunk" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 336 | Rename this parameter "chunkSize" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 336 | Rename this parameter "parquetFile" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 336 | Rename this parameter "fileExist" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 353 | Rename this local variable "firstChunk" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 373 | Rename this parameter "filePath" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 373 | Rename this parameter "fileType" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/nodes/outputs/mongo_output.py` — 13

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 46 | Rename this local variable "ifExist" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 46 | Rename this local variable "createIndex" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 46 | Replace the unused local variable "createIndex" with "_". <sub>unused</sub> | `python:S1481` | Maintenabilité / Basse | Code smell | 5min |
| 46 | Rename this local variable "indexTable" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 46 | Replace the unused local variable "indexTable" with "_". <sub>unused</sub> | `python:S1481` | Maintenabilité / Basse | Code smell | 5min |
| 86 | Rename this local variable "chunkSize" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 87 | Rename this local variable "isFistChunk" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 88 | Rename this local variable "parquetFile" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 96 | Remove the unused local variable "if_exists". <sub>unused</sub> | `python:S1481` | Maintenabilité / Basse | Code smell | 5min |
| 125 | Rename this local variable "datasetId" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 133 | Rename this local variable "ifExist" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 134 | Rename this local variable "createIndex" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 135 | Rename this local variable "indexTable" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/nodes/outputs/mysql_output.py` — 11

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 43 | Rename this local variable "indexTable" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 43 | Rename this local variable "createIndex" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 43 | Rename this local variable "ifExist" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 73 | Rename this local variable "chunkSize" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 74 | Rename this local variable "isFistChunk" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 75 | Rename this local variable "parquetFile" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 78 | Rename this local variable "chunkDf" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 117 | Rename this local variable "datasetId" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 125 | Rename this local variable "ifExist" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 126 | Rename this local variable "createIndex" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 127 | Rename this local variable "indexTable" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/nodes/outputs/pdc_output.py` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 123 | Rename this local variable "parquetFilePath" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 150 | Remove the unused local variable "response". <sub>unused</sub> | `python:S1481` | Maintenabilité / Basse | Code smell | 5min |
| 166 | Rename this local variable "datasetId" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/nodes/outputs/service_chain_output.py` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 72 | Rename this local variable "parquetFilePath" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 97 | Remove the unused local variable "response". <sub>unused</sub> | `python:S1481` | Maintenabilité / Basse | Code smell | 5min |
| 110 | Rename this local variable "datasetId" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/nodes/transforms/filter_transform.py` — 7

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 59 | Rename this local variable "dataSource" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 59 | Rename this local variable "parquetSave" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 59 | Rename this local variable "filterRules" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 67 | Rename this local variable "whereClause" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 211 | Rename this local variable "dataSource" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 212 | Rename this local variable "filterRules" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 213 | Rename this local variable "parquetSave" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/nodes/transforms/flatten_transform.py` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 40 | Rename this local variable "parquetSave" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 108 | Rename this local variable "parqueSave" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/nodes/transforms/merge_transform.py` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 59 | Rename this local variable "parquetSave" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 149 | Rename this local variable "parquetPath" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 151 | Rename this local variable "parquetWriter" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 248 | Rename this local variable "parqueSave" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/routes/api.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 56 | Rename this local variable "tokenInput" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/routes/datasets.py` — 23

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 196 | Rename this local variable "datasetParams" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 203 | Remove the unused local variable "e". <sub>unused</sub> | `python:S1481` | Maintenabilité / Basse | Code smell | 5min |
| 230 | Rename this local variable "datasetParams" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 237 | Remove the unused local variable "e". <sub>unused</sub> | `python:S1481` | Maintenabilité / Basse | Code smell | 5min |
| 279 | Rename this parameter "datasetParams" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 328 | Rename this parameter "datasetParams" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 401 | Rename this parameter "datasetParams" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 449 | Use the opposite operator ("not in") instead. <sub>pitfall</sub> | `python:S1940` | Maintenabilité / Basse | Code smell | 2min |
| 471 | Rename this parameter "datasetParams" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 536 | Rename this parameter "datasetParams" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 559 | Rename this parameter "datasetParams" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 599 | Rename this parameter "datasetParams" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 609 | Rename this parameter "datasetParams" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 654 | Rename this local variable "authBody" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 658 | Rename this local variable "authHeaders" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 660 | Rename this local variable "authRequest" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 667 | Rename this local variable "authResponse" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 804 | Rename this parameter "filePath" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 804 | Rename this parameter "csvDelimiter" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 804 | Rename this parameter "csvHeader" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 822 | Replace the unused loop index "x" with "_". <sub>unused</sub> | `python:S1481` | Maintenabilité / Basse | Code smell | 5min |
| 860 | Rename this local variable "columnarFile" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 871 | Rename this local variable "validated_filePath" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/routes/ptx.py` — 8

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 127 | Rename this local variable "dataResourcesId" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 128 | Rename this local variable "newUrl" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 135 | Rename this local variable "dataResource_url" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 136 | Rename this local variable "dataResources" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 194 | Rename this parameter "Authorization" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 272 | Rename this local variable "fileFormat" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 443 | Rename this parameter "hasSigned" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 1027 | Rename this parameter "fileFormat" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/services/dataset_service.py` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 515 | Rename this parameter "datasetParams" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 579 | Rename this parameter "datasetParams" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |
| 603 | Rename this local variable "result_dataFrame" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/services/pdc_service.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 54 | Rename this parameter "dataResource_url" to match the regular expression ^[_a-z][a-z0-9_]*$. <sub>convention</sub> | `python:S117` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/utils/drupal_filter_converter.py` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 280 | Use the opposite operator ("not in") instead. <sub>pitfall</sub> | `python:S1940` | Maintenabilité / Basse | Code smell | 2min |

#### `backendApi/app/utils/utils.py` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 305 | Remove this redundant Exception class; it derives from another which is already caught. <sub>error-handling, bad-practice, unused</sub> | `python:S5713` | Maintenabilité / Basse | Code smell | 1min |
| 307 | Remove this redundant Exception class; it derives from another which is already caught. <sub>error-handling, bad-practice, unused</sub> | `python:S5713` | Maintenabilité / Basse | Code smell | 1min |
| 474 | Use the `isinstance()` function here. <sub>typing</sub> | `python:S6660` | Maintenabilité / Basse | Code smell | 2min |
| 477 | Use the `isinstance()` function here. <sub>typing</sub> | `python:S6660` | Maintenabilité / Basse | Code smell | 2min |

#### `frontendApp/karma.conf.js` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | The function should be named. <sub>convention, es2015</sub> | `javascript:S7726` | Maintenabilité / Basse | Code smell | 5min |

#### `frontendApp/src/app/app.module.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 25 | Remove this unused import of 'CdkAccordionModule'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components-module.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 25 | Remove this unused import of 'JsonEditorOptions'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 27 | Remove this unused import of 'DashboardsModule'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 29 | Remove this unused import of 'DataFilterComponent'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/confirm-deletion-modal/confirm-deletion-modal.component.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 2 | '@angular/material/dialog' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 3 | '@angular/material/dialog' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/connections/connections.component.spec.ts` _(test)_ — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 31 | This assertion is unnecessary since it does not change the type of the expression. <sub>type-dependent, redundant</sub> | `typescript:S4325` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/dashboards/dashboard/dashboard.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 2 | Remove this unused import of 'OnInit'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/dashboards/ptxdashboard/ptxdashboard.component.html` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 201 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 248 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-card-header> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 303 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 313 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/components/dashboards/ptxdashboard/ptxdashboard.component.ts` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 202 | This assertion is unnecessary since it does not change the type of the expression. <sub>type-dependent, redundant</sub> | `typescript:S4325` | Maintenabilité / Basse | Code smell | 1min |
| 202 | This assertion is unnecessary since it does not change the type of the expression. <sub>type-dependent, redundant</sub> | `typescript:S4325` | Maintenabilité / Basse | Code smell | 1min |
| 208 | This assertion is unnecessary since it does not change the type of the expression. <sub>type-dependent, redundant</sub> | `typescript:S4325` | Maintenabilité / Basse | Code smell | 1min |
| 248 | Use `new Array()` instead of `Array()`. <sub>convention</sub> | `typescript:S7723` | Fiabilité / Basse, Maintenabilité / Basse | Code smell | 5min |

#### `frontendApp/src/app/components/data-filter/data-filter.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'SimpleChanges'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/data-mapper/data-mapper.component.html` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 12 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <div> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/components/datasets-modal/datasets-modal.component.html` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 23 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-radio> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/components/datasets-modal/datasets-modal.component.spec.ts` _(test)_ — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 3 | Remove this unused import of 'IonModal'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/datasets-modal/datasets-modal.component.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 6 | Remove this unused import of 'OnInit'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 9 | Remove this unused import of 'ViewChildren'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 12 | Remove this unused import of 'IonRadio'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/main/datasets/datasets.component.html` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 5 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 26 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-icon> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 29 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-icon> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/components/main/datasets/datasets.component.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'output'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 4 | Remove this unused import of 'DataRenderTypes'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/main/render/render.component.html` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 33 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 57 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/components/main/render/render.component.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 2 | Remove this unused import of 'reflectComponentType'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 7 | Remove this unused import of 'NgxJsonViewerModule'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 8 | Remove this unused import of 'MatTab'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/main/transformation/transformation.component.html` — 6

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 5 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 11 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 22 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-icon> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 25 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-icon> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 31 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-icon> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 34 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-icon> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/components/nodes/input/nodes.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'NodeComponent'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/nodes/output/nodes.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'NodeComponent'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/nodes/transform/nodes.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'NodeComponent'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/user-profile/user-profile.component.html` — 13

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 5 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 90 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 143 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 208 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 224 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 227 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 256 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 265 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 312 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 319 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 324 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 361 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 367 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/components/user-profile/user-profile.component.spec.ts` _(test)_ — 5

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 2 | '@ionic/angular' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 7 | '@ionic/angular' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 8 | '@ionic/angular' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 9 | '@ionic/angular' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 10 | '@ionic/angular' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/user-profile/user-profile.component.ts` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 357 | Handle this exception or don't catch it at all. <sub>cwe, error-handling, suspicious</sub> | `typescript:S2486` | Maintenabilité / Basse | Code smell | 1h |
| 425 | This assertion is unnecessary since it does not change the type of the expression. <sub>type-dependent, redundant</sub> | `typescript:S4325` | Maintenabilité / Basse | Code smell | 1min |
| 431 | Handle this exception or don't catch it at all. <sub>cwe, error-handling, suspicious</sub> | `typescript:S2486` | Maintenabilité / Basse | Code smell | 1h |
| 487 | Handle this exception or don't catch it at all. <sub>cwe, error-handling, suspicious</sub> | `typescript:S2486` | Maintenabilité / Basse | Code smell | 1h |

#### `frontendApp/src/app/components/widgets/auto-complete-widget/input-auto-complete-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 6 | Rename interface "inputAutoCompleteControlI" to match the regular expression ^\$?[A-Z][a-zA-Z0-9]*$. <sub>convention</sub> | `typescript:S101` | Maintenabilité / Basse | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/button-widget/button-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'OnInit'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/button-widget/button.component.spec.ts` _(test)_ — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 31 | This assertion is unnecessary since it does not change the type of the expression. <sub>type-dependent, redundant</sub> | `typescript:S4325` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/checkbox-widget/checkbox-widget.component.spec.ts` _(test)_ — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 33 | This assertion is unnecessary since it does not change the type of the expression. <sub>type-dependent, redundant</sub> | `typescript:S4325` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/data-filter-widget/data-filter-widget.component.html` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/components/widgets/data-filter-widget/data-filter-widget.component.spec.ts` _(test)_ — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 34 | This assertion is unnecessary since it does not change the type of the expression. <sub>type-dependent, redundant</sub> | `typescript:S4325` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/data-mapper-widget/data-mapper-widget.component.html` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/components/widgets/data-mapper-widget/data-mapper-widget.component.spec.ts` _(test)_ — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 34 | This assertion is unnecessary since it does not change the type of the expression. <sub>type-dependent, redundant</sub> | `typescript:S4325` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/data-mapper-widget/data-mapper-widget.component.ts` — 6

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'Output'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 1 | Remove this unused import of 'OnInit'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 1 | Remove this unused import of 'EventEmitter'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 1 | Remove this unused import of 'PipeTransform'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 1 | Remove this unused import of 'Pipe'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 2 | Remove this unused import of 'Data'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/json-inputs-widget/json-inputs-widget.component.html` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 16 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-item> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 18 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 38 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-fab-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/components/widgets/json-inputs-widget/json-inputs-widget.component.spec.ts` _(test)_ — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 64 | This assertion is unnecessary since it does not change the type of the expression. <sub>type-dependent, redundant</sub> | `typescript:S4325` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/json-inputs-widget/json-inputs-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 6 | Remove this unused import of 'CdkAccordionModule'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/node-loader-widget/node-loader-widget.component.ts` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'OnInit'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 4 | Remove this unused import of 'selectControlI'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 5 | Remove this unused import of 'OnChange'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 10 | Useless constructor. <sub>es2015</sub> | `typescript:S6647` | Maintenabilité / Basse | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/select-widget/select-widget.component.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'OnInit'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 1 | Remove this unused import of 'EventEmitter'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 5 | Rename interface "selectControlI" to match the regular expression ^\$?[A-Z][a-zA-Z0-9]*$. <sub>convention</sub> | `typescript:S101` | Maintenabilité / Basse | Code smell | 5min |

#### `frontendApp/src/app/components/widgets/status-component/status-component.component.html` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 6 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/components/widgets/status-component/status-component.component.spec.ts` _(test)_ — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 5 | './status-component.component' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 6 | './status-component.component' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/status-component/status-component.component.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'NgClass'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 1 | Remove this unused import of 'NgStyle'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/components/widgets/text-display-widget/text-display-widget.component.html` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 10 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/components/widgets/text-display-widget/text-display-widget.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | Rename interface "textDisplayControlI" to match the regular expression ^\$?[A-Z][a-zA-Z0-9]*$. <sub>convention</sub> | `typescript:S101` | Maintenabilité / Basse | Code smell | 5min |

#### `frontendApp/src/app/components/workflow-update-rules-modal/workflow-update-rules-modal.component.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'signal'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/core/contextMenuDaav.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'NestedScope'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 9 | Remove this unused import of 'Node'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 61 | This assertion is unnecessary since it does not change the type of the expression. <sub>type-dependent, redundant</sub> | `typescript:S4325` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/core/presets/CustomDock/index.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 71 | Compare with `undefined` directly instead of using `typeof`. <sub>readability, style</sub> | `typescript:S7741` | Maintenabilité / Basse | Code smell | 2min |
| 74 | Compare with `undefined` directly instead of using `typeof`. <sub>readability, style</sub> | `typescript:S7741` | Maintenabilité / Basse | Code smell | 2min |
| 84 | Compare with `undefined` directly instead of using `typeof`. <sub>readability, style</sub> | `typescript:S7741` | Maintenabilité / Basse | Code smell | 2min |

#### `frontendApp/src/app/core/workflow-editor.spec.ts` _(test)_ — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 2 | Remove this unused import of 'EnvironmentInjector'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/core/workflow-editor.ts` — 6

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'Node'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 2 | Remove this unused import of 'Preset'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 27 | Remove this unused import of 'DockPresets'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 50 | Remove this unused import of 'ContextMenuPresets'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 246 | Unnecessary use of conditional expression for default assignment. | `typescript:S6644` | Maintenabilité / Basse | Code smell | 5min |
| 337 | 'node' will use Object's default stringification format ('[object Object]') when stringified. <sub>string, type-dependent, object</sub> | `typescript:S6551` | Maintenabilité / Basse | Code smell | 5min |

#### `frontendApp/src/app/core/workflow-node-editor.spec.ts` _(test)_ — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'NodeEditor'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/core/workflow-node-editor.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 2 | Remove this unused import of 'Scope'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/guards/auth.guard.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 9 | Remove this unused import of 'Observable'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/interceptors/error.interceptor.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | Remove this unused import of 'switchMap'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/main/main.module.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 15 | Remove this unused import of 'LoadingComponent'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/main/main.page.html` — 6

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 9 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 12 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 19 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 25 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 60 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 63 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/models/data-mapper-types.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'KeyValue'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/models/dataset-schema.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | 'any' overrides all other types in this union type. <sub>type-dependent, redundant</sub> | `typescript:S6571` | Maintenabilité / Basse | Code smell | 5min |

#### `frontendApp/src/app/models/dataset.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'ComponentDecorator'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 1 | Remove this unused import of 'Component'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 3 | Remove this unused import of 'PTXDashboardComponent'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/models/datasets-i.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'Component'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 6 | Remove this unused import of 'PTXDashboardComponent'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/models/interfaces/data-connector.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'DatasetType'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/input/input-data-block.spec.ts` _(test)_ — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 6 | Remove this unused import of 'HttpClient'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 9 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/input/input-data-block.ts` — 5

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 3 | Remove this unused import of 'ClassicPreset'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 5 | Remove this unused import of 'FlatObjectSocket'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 6 | Remove this unused import of 'SimpleFieldSocket'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 11 | Remove this unused import of 'Signal'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 173 | Unnecessary use of boolean literals in conditional expression. | `typescript:S6644` | Maintenabilité / Basse | Code smell | 5min |

#### `frontendApp/src/app/nodes/inputs/data-api-block.spec.ts` _(test)_ — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 6 | Remove this unused import of 'HttpClient'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 9 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/inputs/data-file-block.spec.ts` _(test)_ — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 6 | Remove this unused import of 'HttpClient'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 9 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/inputs/data-file-block.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 5 | Remove this unused import of 'SimpleFieldSocket'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 15 | Remove this unused import of 'FileContentResponse'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/inputs/data-lrs-block.spec.ts` _(test)_ — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 6 | Remove this unused import of 'HttpClient'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 9 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/inputs/data-mongo-block.spec.ts` _(test)_ — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 5 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 7 | Remove this unused import of 'HttpClient'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 10 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/inputs/data-mongo-block.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 6 | Remove this unused import of 'FlatObjectSocket'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 7 | Remove this unused import of 'SimpleFieldSocket'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 20 | Remove this unused import of 'MySQLContentResponse'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/inputs/data-mysql-block.spec.ts` _(test)_ — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 8 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 10 | Remove this unused import of 'HttpClient'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 13 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/inputs/data-mysql-block.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 17 | Remove this unused import of 'FileContentResponse'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/inputs/example-input.spec.ts` _(test)_ — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 6 | Remove this unused import of 'HttpClient'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 9 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/inputs/example-input.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 8 | Remove this unused import of 'daavBlock'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/inputs/service-chain-input.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 16 | Remove this unused import of 'InputAutoCompleteControl'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 20 | Remove this unused import of 'MatSnackBar'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 21 | Remove this unused import of 'inject'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/node-block.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 6 | Remove this unused import of 'WorkflowEditor'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/output/output-data-block.spec.ts` _(test)_ — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 6 | Remove this unused import of 'HttpClient'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 9 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/outputs/example-output.spec.ts` _(test)_ — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 6 | Remove this unused import of 'HttpClient'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 9 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/outputs/example-output.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 8 | Remove this unused import of 'daavBlock'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/outputs/file-output.spec.ts` _(test)_ — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 5 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 5 | Remove this unused import of 'inject'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 7 | Remove this unused import of 'HttpClient'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 10 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/outputs/file-output.ts` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 6 | Remove this unused import of 'SimpleFieldSocket'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 19 | Remove this unused import of 'FileContentResponse'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 21 | Remove this unused import of 'DatasetType'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 116 | Unnecessary use of conditional expression for default assignment. | `typescript:S6644` | Maintenabilité / Basse | Code smell | 5min |

#### `frontendApp/src/app/nodes/outputs/mongo-output.spec.ts` _(test)_ — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 5 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 7 | Remove this unused import of 'HttpClient'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 10 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/outputs/mongo-output.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 3 | Remove this unused import of 'FlatObjectSocket'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 15 | Remove this unused import of 'MySQLContentResponse'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/outputs/mysql-output.spec.ts` _(test)_ — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 5 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 7 | Remove this unused import of 'HttpClient'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 10 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/outputs/pdc-output.spec.ts` _(test)_ — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 9 | '@angular/core' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/outputs/pdc-output.ts` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'Input'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 1 | Remove this unused import of 'Output'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 17 | Remove this unused import of 'MatAutocompleteSelectedEvent'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 305 | Handle this exception or don't catch it at all. <sub>cwe, error-handling, suspicious</sub> | `typescript:S2486` | Maintenabilité / Basse | Code smell | 1h |

#### `frontendApp/src/app/nodes/outputs/service-chain-output.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 9 | Remove this unused import of 'inputAutoCompleteControlI'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 9 | Remove this unused import of 'InputAutoCompleteControl'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 10 | Remove this unused import of 'MatAutocompleteSelectedEvent'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/transforms/example-transform.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 6 | Remove this unused import of 'daavBlock'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/transforms/filter-transform.spec.ts` _(test)_ — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | Remove this unused import of 'Node'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/transforms/flatten-transform.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 3 | Remove this unused import of 'SimpleFieldSocket'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/nodes/transforms/merge-transform.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 12 | Remove this unused import of 'ColumnMapping'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 12 | Remove this unused import of 'DatasetMapper'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/pages/forgot-password/forgot-password.page.html` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 56 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 93 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 104 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/pages/login/login.page.html` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 64 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 94 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/pages/register/register.page.html` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 182 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/pages/reset-password/reset-password.page.html` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 17 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 25 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 129 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/pages/worflow/workflow.page.html` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 4 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 5 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |
| 6 | Add a 'onKeyPress\|onKeyDown\|onKeyUp' attribute to this <ion-button> tag. <sub>accessibility</sub> | `Web:MouseEventWithoutKeyboardEquivalentCheck` | Fiabilité / Basse | Bug | 5min |

#### `frontendApp/src/app/pages/worflow/workflow.page.ts` — 7

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 2 | Remove this unused import of 'OnInit'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 2 | Remove this unused import of 'AfterContentInit'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 2 | Remove this unused import of 'SimpleChanges'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 2 | Remove this unused import of 'AfterViewChecked'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 2 | Remove this unused import of 'OnChanges'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 2 | Remove this unused import of 'input'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 7 | Remove this unused import of 'AppUtils'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/services/auth.service.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 5 | Remove this unused import of 'map'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/services/dataset.service.ts` — 4

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 172 | Unnecessary use of conditional expression for default assignment. | `typescript:S6644` | Maintenabilité / Basse | Code smell | 5min |
| 173 | Unnecessary use of conditional expression for default assignment. | `typescript:S6644` | Maintenabilité / Basse | Code smell | 5min |
| 188 | Unnecessary use of conditional expression for default assignment. | `typescript:S6644` | Maintenabilité / Basse | Code smell | 5min |
| 189 | Unnecessary use of conditional expression for default assignment. | `typescript:S6644` | Maintenabilité / Basse | Code smell | 5min |

#### `frontendApp/src/app/services/loading.service.ts` — 2

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 2 | Remove this unused import of 'Subject'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 2 | Remove this unused import of 'BehaviorSubject'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/services/token.service.ts` — 3

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 156 | Handle this exception or don't catch it at all. <sub>cwe, error-handling, suspicious</sub> | `typescript:S2486` | Maintenabilité / Basse | Code smell | 1h |
| 173 | Handle this exception or don't catch it at all. <sub>cwe, error-handling, suspicious</sub> | `typescript:S2486` | Maintenabilité / Basse | Code smell | 1h |
| 198 | Handle this exception or don't catch it at all. <sub>cwe, error-handling, suspicious</sub> | `typescript:S2486` | Maintenabilité / Basse | Code smell | 1h |

#### `frontendApp/src/app/services/worflow.service.ts` — 5

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 1 | Remove this unused import of 'Signal'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 1 | Remove this unused import of 'computed'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 3 | Remove this unused import of 'catchError'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |
| 3 | 'rxjs' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |
| 4 | 'rxjs' imported multiple times. <sub>es2015</sub> | `typescript:S3863` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/app/tabs/tabs.module.ts` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 9 | Remove this unused import of 'ComponentsModule'. <sub>es2015, type-dependent, unused</sub> | `typescript:S1128` | Maintenabilité / Basse | Code smell | 1min |

#### `frontendApp/src/index.html` — 1

| Ligne | Message | Règle | Impacts | Type | Effort |
|---:|---|---|---|---|---|
| 23 | Make sure not using resource integrity feature is safe here. <sub>cwe, former-hotspot</sub> | `Web:S5725` | Sécurité / Basse | Vulnérabilité | 5min |

<a id="decisions"></a>
## Décisions

Aucune règle n'a encore été marquée comme ignorée dans ce rapport.
