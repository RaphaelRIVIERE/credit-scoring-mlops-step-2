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

## Structure du projet

```
credit-scoring-mlops-step-2/
├── app/ # Code source de l'API
├── src/ # Modules métier (preprocessing, utils…)
├── tests/ # Tests unitaires et d'intégration
├── model/ # Artefacts MLflow (modèle versionné)
├── .github/
│   └── workflows/
│       └── ci.yml  # Pipeline CI/CD (GitHub Actions)
├── Dockerfile # Conteneurisation de l'API
├── requirements.txt
└── README.md
```