# App/analysis.py

import pandas as pd
from config import DATA_PATH, MIN_PLAYER_PASSES

def load_data(path):
    """Load dataset from given path."""
    return pd.read_csv(path)

# analysis.py
def build_player_stats(df, player_name, min_passes=5):
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

def calculate_difficult_passes(df, player_name, threshold=0.7):
    """
    Returns passes for a player with xP above a given threshold.
    """
    player_df = df[df["player"] == player_name].copy()
    
    # Convert xP column to numeric
    player_df["xP"] = pd.to_numeric(player_df["xP"], errors="coerce")
    
    # Drop rows where xP couldn't be converted
    player_df = player_df.dropna(subset=["xP"])
    
    return player_df[player_df["xP"] > threshold]