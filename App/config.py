# App/config.py

from pathlib import Path

# Relative path to dataset folder - parquet instead of csv as it's small enough to be pushed to GitHub and faster to load
DATA_PATH = Path(__file__).resolve().parent.parent / "Datasets" / "premierleague_1516_passes_df.parquet"

# Minimum passes threshold for filtering
MIN_PLAYER_PASSES = 100

# Pitch dimensions for mplsoccer
PITCH_LENGTH = 120
PITCH_WIDTH = 80

# Fraction of passes to plot
SAMPLE_PLOT_FRAC = 0.3

# Difficult pass threshold (bottom 20% xP) - and other difficulty thresholds
DIFFICULT_PASS_QUANTILE = 0.20
EASY_PASS_QUANTILE = 0.50
VERY_EASY_PASS_QUANTILE = 0.80