# App/utils.py
import pandas as pd

def assign_y_zone(row, pitch_width=80):
    """Categorize pass start location by pitch thirds."""
    if row["start_y"] <= pitch_width/3:
        return "Left"
    elif row["start_y"] <= 2*pitch_width/3:
        return "Center"
    else:
        return "Right"

def normalize_position(pos):
    """Normalize detailed positions into broader groups."""
    if pd.isna(pos):
        return pos
    pos = pos.replace("Left ","").replace("Right ","")
    mapping = {
        "Back": "Back", "Center Back": "Back", "Wing Back": "Back",
        "Defensive Midfield": "Defensive Midfield", "Center Defensive Midfield": "Defensive Midfield",
        "Center Midfield": "Midfield", "Midfield": "Midfield",
        "Attacking Midfield": "Attacking Midfield", "Center Attacking Midfield": "Attacking Midfield",
        "Wing": "Wing",
        "Forward": "Forward", "Center Forward": "Forward"
    }
    return mapping.get(pos, pos)