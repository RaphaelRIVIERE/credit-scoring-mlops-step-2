import pandas as pd

def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Crée les features dérivées (ratios, âge) — appeler après fusion."""
    df = df.copy()
    df['AGE_YEARS']            = -df['DAYS_BIRTH'] / 365
    df['DAYS_EMPLOYED_PERC']   = df['DAYS_EMPLOYED'] / df['DAYS_BIRTH']
    df['RATIO_ANNUITE_REVENU'] = df['AMT_ANNUITY'] / df['AMT_INCOME_TOTAL']
    df['PAYMENT_RATE']         = df['AMT_ANNUITY'] / df['AMT_CREDIT']
    df['RATIO_CREDIT_REVENU']  = df['AMT_CREDIT']  / df['AMT_INCOME_TOTAL']
    return df