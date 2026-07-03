from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).parent / "DATA"


def clean_columns(df):
    df.columns = df.columns.str.strip().str.lower()
    return df


def load_transactions():
    path = DATA_DIR / "transactions.csv"
    df = pd.read_csv(path)
    df = clean_columns(df)

    required_columns = {
        "date",
        "description",
        "category",
        "type",
        "amount",
        "payment_method",
        "notes",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise KeyError(f"Missing columns: {missing_columns}")

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["type"] = df["type"].astype(str).str.strip().str.lower()
    df["category"] = df["category"].fillna("").astype(str).str.strip()
    df["payment_method"] = df["payment_method"].fillna("Unknown")
    df["notes"] = df["notes"].fillna("")

    df = df.dropna(subset=["amount"])

    return df