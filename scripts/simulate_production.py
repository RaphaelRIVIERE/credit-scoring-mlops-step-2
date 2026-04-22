#!/usr/bin/env python3
"""
Simulate production traffic to the credit scoring API.

Usage:
  # Simulation normale (100 requêtes)
  python scripts/simulate_production.py

  # Avec drift activé (300 requêtes, drift ON)
  python scripts/simulate_production.py --n 300 --drift

  # Cibler un environnement distant
  python scripts/simulate_production.py --n 200 --api-url https://mon-api.hf.space --api-key my-key
"""

import argparse
import os
import time
from pathlib import Path

import httpx
import numpy as np
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def generate_client(rng: np.random.Generator, drift: bool = False) -> dict:
    """
    Génère des features synthétiques d'un client.

    Avec drift=True, les distributions sont décalées pour simuler une dérive :
    - Clients plus âgés
    - Revenus plus faibles
    - Ratios crédit/revenu plus élevés (profil plus risqué)
    - Scores externes (EXT_SOURCE) plus bas
    """
    # Âge : sans drift 28-60 ans, avec drift 40-72 ans
    age_years = rng.uniform(28, 60) if not drift else rng.uniform(40, 72)
    days_birth = -(age_years * 365)

    # Ancienneté emploi
    employed_years = rng.uniform(0.5, min(age_years - 20, 18))
    days_employed = -(employed_years * 365)

    # Revenu : log-normal centré ~180k; drift → revenu réduit de 20-40 %
    amt_income = max(27_000, rng.lognormal(mean=12.1, sigma=0.5))
    if drift:
        amt_income *= rng.uniform(0.60, 0.80)

    # Crédit : multiple du revenu mensuel
    credit_months = rng.uniform(12, 72) if not drift else rng.uniform(36, 96)
    monthly_income = amt_income / 12
    amt_credit = float(np.clip(monthly_income * credit_months, 45_000, 4_050_000))

    # Annuité : taux appliqué au crédit; drift → taux plus élevé (charge plus lourde)
    annuity_rate = rng.uniform(0.025, 0.055) if not drift else rng.uniform(0.050, 0.085)
    amt_annuity = max(2_250, amt_credit * annuity_rate)

    # Scores externes : drift → scores plus bas (clients plus risqués)
    ext_shift = 0.0 if not drift else -0.18
    ext1 = float(np.clip(rng.normal(0.50, 0.18) + ext_shift, 0.01, 0.99)) if rng.random() > 0.30 else None
    ext2 = float(np.clip(rng.normal(0.55, 0.20) + ext_shift, 0.01, 0.99))
    ext3 = float(np.clip(rng.normal(0.52, 0.20) + ext_shift, 0.01, 0.99)) if rng.random() > 0.20 else None

    return {
        # Champs obligatoires
        "DAYS_BIRTH": round(days_birth, 1),
        "DAYS_EMPLOYED": round(days_employed, 1),
        "AMT_INCOME_TOTAL": round(amt_income, 2),
        "AMT_CREDIT": round(amt_credit, 2),
        "AMT_ANNUITY": round(amt_annuity, 2),
        # Champs optionnels influents
        "EXT_SOURCE_1": round(ext1, 4) if ext1 is not None else None,
        "EXT_SOURCE_2": round(ext2, 4),
        "EXT_SOURCE_3": round(ext3, 4) if ext3 is not None else None,
        "CODE_GENDER": str(rng.choice(["M", "F"])),
        "CNT_CHILDREN": int(rng.choice([0, 1, 2, 3], p=[0.45, 0.30, 0.18, 0.07])),
        "FLAG_OWN_CAR": str(rng.choice(["Y", "N"])),
        "FLAG_OWN_REALTY": str(rng.choice(["Y", "N"])),
        "AMT_GOODS_PRICE": round(float(amt_credit * rng.uniform(0.85, 1.0)), 2) if rng.random() > 0.10 else None,
        "DAYS_REGISTRATION": round(float(rng.uniform(-15_000, -500)), 1),
        "DAYS_ID_PUBLISH": round(float(rng.uniform(-4_000, -100)), 1),
        "DAYS_LAST_PHONE_CHANGE": round(float(rng.uniform(-1_500, -1)), 1),
        "REGION_RATING_CLIENT": int(rng.choice([1, 2, 3], p=[0.10, 0.65, 0.25])),
        "REGION_RATING_CLIENT_W_CITY": int(rng.choice([1, 2, 3], p=[0.10, 0.65, 0.25])),
    }


def run_simulation(n: int, drift: bool, api_url: str, api_key: str, delay: float, seed: int) -> None:
    rng = np.random.default_rng(seed)

    predict_url = f"{api_url.rstrip('/')}/predict"
    headers = {"X-API-Key": api_key}

    ok = errors = approved = rejected = 0
    latencies: list[float] = []

    print(f"{'='*60}")
    print(f"Simulation {'AVEC drift' if drift else 'sans drift'}")
    print(f"Cible      : {predict_url}")
    print(f"Requêtes   : {n}  |  seed={seed}")
    print(f"{'='*60}")

    with httpx.Client(timeout=15) as client:
        for i in range(1, n + 1):
            payload = generate_client(rng, drift=drift)
            try:
                t0 = time.perf_counter()
                resp = client.post(predict_url, json=payload, headers=headers)
                latency_ms = (time.perf_counter() - t0) * 1000

                if resp.status_code == 200:
                    data = resp.json()
                    ok += 1
                    latencies.append(latency_ms)
                    if data["decision"] == "approved":
                        approved += 1
                    else:
                        rejected += 1

                    if i % 25 == 0 or i == n:
                        print(
                            f"  [{i:4d}/{n}]  score={data['score']:.3f}"
                            f"  {data['decision']:8s}  {latency_ms:.0f}ms"
                        )
                else:
                    errors += 1
                    print(f"  [{i:4d}/{n}]  ERREUR {resp.status_code}: {resp.text[:100]}")

            except httpx.RequestError as exc:
                errors += 1
                print(f"  [{i:4d}/{n}]  EXCEPTION: {exc}")

            if delay > 0:
                time.sleep(delay)

    print(f"{'='*60}")
    print(f"Terminé  →  OK={ok}  Erreurs={errors}")
    if latencies:
        lat_sorted = sorted(latencies)
        p95_idx = int(len(lat_sorted) * 0.95)
        print(f"Taux approbation : {approved / ok:.1%}")
        print(f"Latence moyenne  : {sum(latencies)/len(latencies):.1f} ms")
        print(f"Latence p95      : {lat_sorted[p95_idx]:.1f} ms")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simule du trafic de production vers l'API de scoring crédit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--n", type=int, default=100, help="Nombre de requêtes (défaut: 100)")
    parser.add_argument(
        "--drift",
        action="store_true",
        help="Active le décalage de distribution pour simuler un data drift",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("API_URL", "http://localhost:8000"),
        help="URL de base de l'API (défaut: http://localhost:8000 ou $API_URL)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("API_KEY", ""),
        help="Clé API brute pour le header X-API-Key (défaut: $API_KEY du .env)",
    )
    parser.add_argument("--delay", type=float, default=0.0, help="Délai en secondes entre requêtes (défaut: 0)")
    parser.add_argument("--seed", type=int, default=42, help="Graine aléatoire pour la reproductibilité (défaut: 42)")

    args = parser.parse_args()

    if not args.api_key:
        parser.error("--api-key est requis (ou définissez API_KEY dans .env)")

    run_simulation(args.n, args.drift, args.api_url, args.api_key, args.delay, args.seed)


if __name__ == "__main__":
    main()
