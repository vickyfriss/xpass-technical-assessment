# App/config.py

from pathlib import Path

# Relative path to dataset folder
DATA_PATH = Path(__file__).resolve().parent.parent / "Datasets" / "premierleague_1516_passes_df.csv"

# Minimum passes threshold for filtering
MIN_PLAYER_PASSES = 10

# Pitch dimensions for mplsoccer
PITCH_LENGTH = 120
PITCH_WIDTH = 80

# Fraction of passes to plot
SAMPLE_PLOT_FRAC = 0.3