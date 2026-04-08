# App/analysis.py

import pandas as pd
from config import DATA_PATH, DIFFICULT_PASS_QUANTILE


def load_data(path):
    """Load dataset from given path."""
    return pd.read_parquet(path)


def build_player_stats(df, player_name, min_passes=None):
    """
    Build passing statistics for a player.

    Note:
    We do NOT block players with few passes anymore.
    The dashboard handles cases where there is not enough data
    for deeper analysis.
    """

    player_df = df[df["player"] == player_name]

    total_passes = len(player_df)

    successful_passes = (player_df["Outcome"] == 1).sum()

    avg_xP = player_df["xP"].mean() if total_passes > 0 else 0

    return {
        "total_passes": total_passes,
        "successful_passes": successful_passes,
        "avg_xP": avg_xP
    }


def calculate_difficult_passes(df, player_name):
    """
    Returns the difficult passes for a player using the same
    definition as in main.py (bottom quantile xP).
    """

    player_df = df[df["player"] == player_name].copy()

    if player_df.empty:
        return pd.DataFrame()

    # Ensure xP is numeric
    player_df["xP"] = pd.to_numeric(player_df["xP"], errors="coerce")
    player_df = player_df.dropna(subset=["xP"])

    # Same threshold used in main.py
    HARD_PASS_THRESHOLD = df["xP"].quantile(DIFFICULT_PASS_QUANTILE)

    difficult_passes = player_df[player_df["xP"] <= HARD_PASS_THRESHOLD]

    return difficult_passes