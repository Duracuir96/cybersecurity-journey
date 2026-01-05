# src/data/ml_preprocessor.py
from __future__ import annotations

from typing import Tuple
import numpy as np
import pandas as pd


def clean_numeric(df: pd.DataFrame, col: str = "quantity") -> pd.DataFrame:
    """
    Ensure quantity is numeric and non-negative.
    """
    df = df.copy()

    df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=[col])
    df = df[df[col] >= 0]

    return df


def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    - ENSURE one row per date (aggregate first)
    - Fill missing dates with quantity = 0
    """

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # 🔥 CRITICAL FIX — aggregate by date to avoid duplicate index
    df = (
        df.groupby("date", as_index=False)["quantity"]
        .sum()
        .sort_values("date")
        .reset_index(drop=True)
    )

    # Build full continuous date index
    full_index = pd.date_range(
        start=df["date"].min(),
        end=df["date"].max(),
        freq="D",
    )

    df = (
        df.set_index("date")
        .reindex(full_index, fill_value=0)
        .rename_axis("date")
        .reset_index()
    )

    return df


def prepare_regression_features(
    df: pd.DataFrame,
) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Prepare X, y and processed df for Linear Regression.

    Input df columns:
      - date
      - quantity

    Output:
      - X: day_index (2D)
      - y: quantity
      - df: date, quantity, day_index
    """

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Linear time index (robust, no date math needed)
    df["day_index"] = np.arange(len(df))

    X = df[["day_index"]].values
    y = df["quantity"].astype(float).values

    return X, y, df
