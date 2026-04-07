# plots.py
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgb
from matplotlib.patches import FancyArrowPatch
from mplsoccer import Pitch
from config import PITCH_LENGTH, PITCH_WIDTH

def plot_pass_map(player_name, df, frac=0.1, seed=14):
    """
    Plot pass map for a single player using xPass.

    Parameters:
        player_name: str
        df: DataFrame with pass data
        frac: float, fraction of passes to display (0-1)
        seed: int, random seed for sampling
    """
    # Filter player passes and drop NAs
    passes = df[df["player"] == player_name].dropna(subset=["start_x","start_y","end_x","end_y","xP","Outcome"])
    
    # If no passes, return empty figure
    if passes.empty:
        fig, ax = plt.subplots(figsize=(10,7))
        ax.set_title(f"No pass data for {player_name}")
        return fig

    # Ensure xP is float
    passes["xP"] = passes["xP"].astype(float)

    # Sample fraction of passes
    if frac < 1.0:
        passes = passes.sample(frac=frac, random_state=seed)

    # Get actual team and position for the title
    actual_team = passes["team"].iloc[0]
    actual_position = passes["position_group"].iloc[0] if "position_group" in passes.columns else passes["position"].iloc[0]

    # Colour gradient: dark = low xP (hard pass), light = high xP (easy pass)
    base_color = "orangered"
    rgb = to_rgb(base_color)
    light_rgb = to_rgb("#ffb3a1")    # lighter version
    dark_rgb = tuple(c * 0.5 for c in rgb)  # darker version
    cmap = LinearSegmentedColormap.from_list("forward_gradient", [dark_rgb, light_rgb])
    norm = Normalize(vmin=0, vmax=1)  # xP is between 0-1

    # Create pitch
    pitch = Pitch(pitch_type="statsbomb", pitch_length=PITCH_LENGTH, pitch_width=PITCH_WIDTH, line_color="black")
    fig, ax = pitch.draw(figsize=(10,7))

    # Plot passes
    for _, p in passes.iterrows():
        x, y = p["start_x"], p["start_y"]
        dx, dy = p["end_x"]-x, p["end_y"]-y
        col = cmap(norm(p["xP"]))
        style = "-" if p["Outcome"]==1 else "--"
        ax.add_patch(plt.Circle((x,y), 1.5, color=col, alpha=0.7, zorder=1))
        ax.add_patch(FancyArrowPatch(
            (x,y), (x+dx,y+dy),
            color=col, arrowstyle='-|>', linewidth=2.5,
            linestyle=style, mutation_scale=20, alpha=0.9, zorder=2
        ))

    # Colourbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax)
    cbar.set_label("xP of Pass (lower = harder)")

    # Title with actual team and position
    ax.set_title(f"{player_name} ({actual_team} - {actual_position}) - Pass Map ({frac*100:.0f}% of passes)", fontsize=16)

    return fig