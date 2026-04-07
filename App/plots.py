# plots.py
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgb
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.axes_grid1 import make_axes_locatable
from adjustText import adjust_text

from mplsoccer import Pitch
from config import PITCH_LENGTH, PITCH_WIDTH, SAMPLE_PLOT_FRAC

def plot_pass_map(player_name, df, team_name="Everton"):
    """Plot pass map for a single player using xPass."""
    passes = df[df["player"] == player_name].dropna(subset=["start_x","start_y","end_x","end_y","xP","Outcome"])
    passes = passes.sample(frac=SAMPLE_PLOT_FRAC, random_state=42)

    # Colour gradient: dark = low xP (hard pass), light = high xP (easy pass)
    base_color = "orangered"
    rgb = to_rgb(base_color)
    light_rgb = tuple(c*1.2 if c*1.2<=1 else 1 for c in rgb)  # lighter version
    dark_rgb = tuple(c*0.5 for c in rgb)                      # darker version
    cmap = LinearSegmentedColormap.from_list("forward_gradient", [dark_rgb, light_rgb])
    norm = Normalize(vmin=0, vmax=1)  # xP is between 0-1

    # Create pitch
    pitch = Pitch(pitch_type="statsbomb", pitch_length=PITCH_LENGTH, pitch_width=PITCH_WIDTH, line_color="black")
    fig, ax = pitch.draw(figsize=(10,7))

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

    ax.set_title(f"{player_name} ({team_name}) - Pass Map ({SAMPLE_PLOT_FRAC*100:.0f}% of passes)", fontsize=16)

    # Do NOT call plt.show() — just return the figure
    return fig