# App/analysis.py

import pandas as pd
from config import DATA_PATH, DIFFICULT_PASS_QUANTILE


def load_data(path=DATA_PATH):
    """Load dataset from the given path (Parquet)."""
    try:
        df = pd.read_parquet(path)
        # Ensure all essential columns exist
        required_cols = ["player", "team", "position", "start_x", "start_y", "end_x", "end_y", "Outcome", "xP"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = pd.NA
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data from {path}: {e}")


def build_player_stats(df, player_name, min_passes=None):
    """
    Build passing statistics for a player.
    Always returns a dict with keys, even if the player has no passes.
    """

    player_df = df[df["player"] == player_name]

    total_passes = len(player_df)
    successful_passes = int((player_df["Outcome"] == 1).sum()) if total_passes > 0 else 0
    avg_xP = float(player_df["xP"].mean()) if total_passes > 0 else 0.0

    return {
        "total_passes": total_passes,
        "successful_passes": successful_passes,
        "avg_xP": avg_xP
    }


def calculate_difficult_passes(df, player_name):
    """
    Returns the difficult passes for a player using the bottom quantile of xP.
    Always returns a DataFrame (even empty if no passes).
    """

    player_df = df[df["player"] == player_name].copy()

    if player_df.empty:
        return pd.DataFrame({"xP": []})

    # Ensure xP is numeric and drop missing
    player_df["xP"] = pd.to_numeric(player_df["xP"], errors="coerce")
    player_df = player_df.dropna(subset=["xP"])

    if player_df.empty:
        return pd.DataFrame({"xP": []})

    # Threshold for difficult passes
    HARD_PASS_THRESHOLD = df["xP"].quantile(DIFFICULT_PASS_QUANTILE)

    difficult_passes = player_df[player_df["xP"] <= HARD_PASS_THRESHOLD]

    # Ensure xP column exists
    if "xP" not in difficult_passes.columns:
        difficult_passes["xP"] = pd.Series(dtype=float)

    return difficult_passes.reset_index(drop=True)