import streamlit as st
import pandas as pd
from analysis import load_data, build_player_stats, calculate_difficult_passes
from plots import plot_pass_map
from config import DATA_PATH, MIN_PLAYER_PASSES

# Load data
df = load_data(DATA_PATH)

# --- Page config for full width ---
st.set_page_config(page_title="xPass Dashboard", layout="wide")

# --- Main Page Title ---
st.markdown(
    "<h1 style='text-align: center; color: #2E86AB;'>⚽ xPass Football Analytics Dashboard</h1>", 
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align: center;'>Compare player passing stats and xPass maps side by side</p>", 
    unsafe_allow_html=True
)

# --- Columns for comparing up to 3 players ---
col1, col2, col3 = st.columns(3)

for col, idx in zip([col1, col2, col3], range(1,4)):
    with col:
        st.subheader(f"Player {idx}")

        # Team filter
        teams = ["ALL"] + sorted(df["team"].unique())
        selected_team = st.selectbox(f"Select Team {idx}", teams, key=f"team_{idx}")

        # Position filter
        positions = ["ALL"] + sorted(df["position"].unique())
        selected_position = st.selectbox(f"Select Position {idx}", positions, key=f"pos_{idx}")

        # Player filter
        players_filtered = df.copy()
        if selected_team != "ALL":
            players_filtered = players_filtered[players_filtered["team"] == selected_team]
        if selected_position != "ALL":
            players_filtered = players_filtered[players_filtered["position"] == selected_position]

        player_list = sorted(players_filtered["player"].unique())
        selected_player = st.selectbox(f"Select Player {idx}", player_list, key=f"player_{idx}")

        # Display stats and pass map
        if selected_player:
            st.markdown(f"**{selected_player} Stats & xPass**")
            player_stats = build_player_stats(df, selected_player, MIN_PLAYER_PASSES)
            st.json({
                "total_passes": int(player_stats["total_passes"]),
                "avg_xP": float(player_stats["avg_xP"]),
                "successful_passes": int(player_stats["successful_passes"])
            })

            player_df = calculate_difficult_passes(df, selected_player)
            fig = plot_pass_map(selected_player, player_df)
            st.pyplot(fig, use_container_width=True)