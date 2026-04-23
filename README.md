---
title: Credit Scoring API
emoji: 💳
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
pinned: false
---

# Credit Scoring MLOps — Déploiement & Monitoring

Suite du projet [credit-scoring-mlops](../credit-scoring-mlops), qui portait sur le développement et le versionnage du modèle. Ce projet couvre la mise en production : API, conteneurisation, CI/CD et monitoring.

## Contexte

Modèle de scoring crédit développé pour "Prêt à Dépenser". Il prédit la probabilité de défaut de remboursement d'un client et retourne un score permettant d'accepter ou refuser une demande de crédit. Le modèle a été entraîné et versionné avec MLflow (LightGBM, optimisé via Optuna).


## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancer l'API

Copie le fichier `.env.example` et remplis ta clé :

```bash
cp .env.example .env
```

Pour générer une clé sécurisée :

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Lance l'API :

```bash
uvicorn app.main:app --reload
```

La doc interactive Swagger est disponible sur [http://localhost:8000/docs](http://localhost:8000/docs).

## Endpoints

### `GET /health`

Vérifie que l'API est opérationnelle. Aucune authentification requise.

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### `POST /predict`

Retourne le score de défaut et la décision crédit pour un client.

**Authentification requise** : header `X-API-Key` (voir section Sécurité).

**Corps de la requête** (champs obligatoires) :

| Champ | Type | Description |
|---|---|---|
| `DAYS_BIRTH` | float | Jours depuis la naissance (valeur négative) |
| `DAYS_EMPLOYED` | float | Jours depuis l'embauche (négatif si employé) |
| `AMT_INCOME_TOTAL` | float | Revenu annuel total (> 0) |
| `AMT_CREDIT` | float | Montant du crédit demandé (> 0) |
| `AMT_ANNUITY` | float | Annuité du crédit (> 0) |

De nombreux champs optionnels sont également acceptés (données bureau, historique crédit, etc.). Voir la doc Swagger pour la liste complète.

**Réponse** :

```json
{
  "score": 0.23,
  "decision": "approved"
}
```

- `score` : probabilité de défaut entre 0 et 1 (0 = bon payeur, 1 = défaut certain)
- `decision` : `"approved"` si score < 0.5, `"rejected"` sinon

**Exemple** :

```bash
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: ta-clé-secrète" \
  -H "Content-Type: application/json" \
  -d '{"DAYS_BIRTH": -10000, "DAYS_EMPLOYED": -2000, "AMT_INCOME_TOTAL": 50000, "AMT_CREDIT": 200000, "AMT_ANNUITY": 15000}'
```

## Docker

Image seule :

```bash
docker build -t credit-scoring-api .
docker run -p 8000:8000 -e API_KEY=ta-clé-secrète credit-scoring-api
```

Avec Postgres (recommandé) :

```bash
cp .env.example .env  # remplir API_KEY et DATABASE_URL
docker-compose up --build
```

L'API est disponible sur [http://localhost:8000](http://localhost:8000), Postgres sur le port `5432`.

## Stockage des données de production

Chaque appel à `/predict` est automatiquement enregistré dans une base **PostgreSQL** via SQLAlchemy. Deux tables sont créées au démarrage :

- `predictions` : stocke les features du client, le score, la décision et le temps d'inférence. Les champs optionnels sont `NULL` si non fournis.
- `logs` : trace chaque requête HTTP (endpoint, méthode, status code, temps de réponse) avec une FK vers `predictions`.

Le schéma complet est défini dans [app/models.py](app/models.py).

### Configuration

La variable d'environnement `DATABASE_URL` contrôle la connexion :

```
DATABASE_URL=postgresql://user:password@host/predictions_db
```

Les tables sont créées automatiquement au démarrage de l'API (`init_db()`).

## Simulation de production

Le script `scripts/simulate_production.py` envoie N requêtes synthétiques à l'API pour peupler la base de données — utile pour tester le monitoring sans trafic réel.

```bash
# 100 requêtes avec distributions normales
python scripts/simulate_production.py

# 300 requêtes avec drift activé (distributions décalées)
python scripts/simulate_production.py --n 300 --drift

# Cibler un environnement distant
python scripts/simulate_production.py --n 200 --drift \
  --api-url https://mon-api.hf.space \
  --api-key ma-clé-secrète
```

| Option | Défaut | Description |
|---|---|---|
| `--n` | 100 | Nombre de requêtes |
| `--drift` | off | Décale les distributions (âge, revenu, EXT_SOURCE) pour simuler un data drift |
| `--api-url` | localhost:8000 | URL cible |
| `--api-key` | `$API_KEY` du `.env` | Clé API |

## Analyse du Data Drift

Le notebook `monitoring/drift_report.ipynb` compare deux fenêtres de données de production pour détecter une dérive des distributions :

- **Référence** : trafic enregistré sans drift (batch initial)
- **Courant** : trafic enregistré avec drift (batch récent)

Les deux jeux de données sont chargés directement depuis PostgreSQL — aucun fichier CSV n'est nécessaire.

### Générer le rapport

```bash
# Exécuter le notebook et exporter le rapport HTML
jupyter nbconvert --to notebook --execute monitoring/drift_report.ipynb --output monitoring/drift_report.ipynb

# Ouvrir le rapport interactif dans un navigateur
open monitoring/reports/drift_report.html   # macOS
xdg-open monitoring/reports/drift_report.html  # Linux
```

Le rapport Evidently analyse les features clés : `DAYS_BIRTH`, `AMT_INCOME_TOTAL`, `AMT_CREDIT`, `AMT_ANNUITY`, `EXT_SOURCE_1/2/3`, `score`.

### Interprétation

Le notebook inclut une cellule d'interprétation détaillant :
- quelles features driftent et dans quel sens
- les risques pour la fiabilité du modèle en production
- les seuils d'alerte et actions recommandées (surveillance hebdomadaire, déclenchement d'un ré-entraînement)

## CI/CD

Le pipeline GitHub Actions (`.github/workflows/ci-cd.yml`) se déclenche à chaque push ou pull request sur `main` et enchaîne trois jobs :

| Job | Déclencheur | Action |
|---|---|---|
| `test` | push + PR | Lance pytest avec seuil de couverture à 70% |
| `docker-build` | push sur `main` uniquement | Construit l'image Docker |
| `deploy` | push sur `main` uniquement | Déploie sur Hugging Face Spaces |

### Déploiement sur Hugging Face Spaces

Le job `deploy` pousse le code sur le Space HF via git. Il nécessite le secret `HF_TOKEN` configuré dans les settings du dépôt GitHub.

L'API est accessible publiquement à l'adresse :
[https://huggingface.co/spaces/rriviere/credit-scoring-api](https://huggingface.co/spaces/rriviere/credit-scoring-api)

## Tests

Les tests utilisent [pytest](https://pytest.org) et un client de test FastAPI. Le modèle MLflow est mocké — pas besoin qu'il soit chargé en mémoire.

Lancer tous les tests :

```bash
pytest tests/ -v
```

Lancer avec le rapport de couverture :

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

Le pipeline CI impose un seuil minimum de **70% de couverture** sur le dossier `app/`. En dessous, le build échoue.

Lancer un test précis :

```bash
pytest tests/test_api.py::test_predict_valid -v
```

## Sécurité

L'endpoint `/predict` est protégé par une clé API. La clé doit être envoyée dans le header HTTP `X-API-Key` à chaque requête.

```
X-API-Key: ta-clé-secrète
```

Côté serveur, la clé est hashée en SHA-256 avant comparaison — elle n'est jamais stockée en clair en mémoire. Le fichier `.env` contenant la clé ne doit jamais être commité (il est dans le `.gitignore`).

Toute requête sans clé ou avec une clé incorrecte reçoit une réponse `403 Non autorisé`, sans indication sur la nature de l'erreur.

## Structure du projet

```
credit-scoring-mlops-step-2/
├── app/  # Code source de l'API
│   ├── main.py             # Point d'entrée FastAPI + middleware logging
│   ├── routes.py           # Endpoint /predict
│   ├── schemas.py          # Modèles Pydantic (ClientFeatures, PredictionResponse)
│   ├── models.py           # Modèles SQLAlchemy (Prediction, Log)
│   ├── logger.py           # Fonctions log_prediction() et log_request()
│   └── database.py         # Connexion et initialisation Postgres
├── src/ # Modules métier
│   └── preprocessing.py    # Feature engineering
├── scripts/
│   └── simulate_production.py  # Simulation de trafic avec drift optionnel
├── tests/  # Tests unitaires et d'intégration
├── data/
│   └── reference/   # Données de référence pour l'analyse de drift
│       └── train_sample.csv  # À placer manuellement (non versionné)
├── model/                  # Artefacts MLflow (modèle versionné)
├── .github/
│   └── workflows/
│       └── ci-cd.yml  # Pipeline CI/CD (GitHub Actions)
├── docker-compose.yml # API + Postgres en local
├── Dockerfile # Conteneurisation de l'API
├── requirements.txt
└── README.md
```
