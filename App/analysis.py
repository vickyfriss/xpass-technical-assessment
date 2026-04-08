# App/analysis.py

import pandas as pd
from config import DATA_PATH, MIN_PLAYER_PASSES, DIFFICULT_PASS_QUANTILE

def load_data(path):
    """Load dataset from given path."""
    return pd.read_parquet(path)

# analysis.py
def build_player_stats(df, player_name, min_passes=50):
    """
    Build player-level statistics filtered by minimum passes.
    """
    player_df = df[df['player'] == player_name]
    if len(player_df) < min_passes:
        return None  # or handle low-pass players
    # compute stats here...
    stats = {
        "total_passes": len(player_df),
        "avg_xP": player_df["xP"].mean(),
        "successful_passes": player_df["Outcome"].sum()
    }
    return stats

def calculate_difficult_passes(df, player_name):
    """
    Returns the difficult passes for a player using the same
    definition as in main.py (bottom 20% xP).
    """

    player_df = df[df["player"] == player_name].copy()

    # Ensure xP is numeric
    player_df["xP"] = pd.to_numeric(player_df["xP"], errors="coerce")
    player_df = player_df.dropna(subset=["xP"])

    # Same threshold used in main.py
    HARD_PASS_THRESHOLD = df["xP"].quantile(DIFFICULT_PASS_QUANTILE)

    difficult_passes = player_df[player_df["xP"] <= HARD_PASS_THRESHOLD]

    return difficult_passes