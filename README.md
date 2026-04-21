---
title: Credit Scoring API
emoji: 💳
colorFrom: blue
colorTo: green
sdk: docker
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

### Build de l'image

```bash
docker build -t credit-scoring-api .
```

### Lancer le conteneur

```bash
docker run -p 8000:8000 -e API_KEY=ta-clé-secrète credit-scoring-api
```

L'API est alors disponible sur [http://localhost:8000](http://localhost:8000).

> **Note** : L'image est basée sur `python:3.11-slim`. `libgomp1` est installé automatiquement (requis par LightGBM).

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
├── app/ # Code source de l'API
├── src/ # Modules métier (preprocessing, utils…)
├── tests/ # Tests unitaires et d'intégration
├── model/ # Artefacts MLflow (modèle versionné)
├── .github/
│   └── workflows/
│       └── ci-cd.yml  # Pipeline CI/CD (GitHub Actions)
├── Dockerfile # Conteneurisation de l'API
├── requirements.txt
└── README.md
```
