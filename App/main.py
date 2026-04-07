import streamlit as st
import pandas as pd
from analysis import load_data, build_player_stats, calculate_difficult_passes
from plots import plot_pass_map
from config import DATA_PATH, MIN_PLAYER_PASSES

# --- Normalize positions ---
def normalize_position(pos):
    pos = pos.replace("Left ", "").replace("Right ", "")
    if pos in ["Back", "Center Back", "Wing Back"]:
        return "Defender"
    elif pos in ["Defensive Midfield", "Center Defensive Midfield"]:
        return "Defensive Midfielder"
    elif pos in ["Center Midfield", "Midfield"]:
        return "Midfielder"
    elif pos in ["Attacking Midfield", "Center Attacking Midfield"]:
        return "Attacking Midfielder"
    elif pos in ["Wing"]:
        return "Wing"
    elif pos in ["Forward", "Center Forward"]:
        return "Forward"
    elif pos in ["Goalkeeper"]:
        return "Goalkeeper"
    else:
        return pos

# --- Position order ---
POSITION_ORDER = [
    "Goalkeeper",
    "Defender",
    "Defensive Midfielder",
    "Midfielder",
    "Attacking Midfielder",
    "Wing",
    "Forward"
]

# --- Load data ---
df = load_data(DATA_PATH)
df["position_group"] = df["position"].apply(normalize_position)

# --- Precompute team to positions and players ---
team_to_positions = {}
team_pos_to_players = {}
teams = ["ALL"] + sorted(df["team"].unique())
for team in teams:
    if team == "ALL":
        team_df = df
    else:
        team_df = df[df["team"] == team]
    positions = sorted(team_df["position_group"].unique(), key=lambda x: POSITION_ORDER.index(x) if x in POSITION_ORDER else 999)
    team_to_positions[team] = positions
    for pos in positions:
        key = (team, pos)
        players = sorted(team_df[team_df["position_group"] == pos]["player"].unique())
        team_pos_to_players[key] = players

# --- Page config ---
st.set_page_config(page_title="xPass Dashboard", layout="wide")

# --- Main title ---
st.markdown(
    "<h1 style='text-align: center; color: #2E86AB;'>xPass Dashboard</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align: center;'>Compare player passing stats and xPass maps side by side</p>",
    unsafe_allow_html=True
)

# --- Columns for 3 players ---
col1, col2, col3 = st.columns(3)

# Optional: default players
default_players = ["Romelu Lukaku Menama", "John Stones", "Eden Hazard"]

# Cache the plot to speed up repeated calls
@st.cache_data
def cached_plot(player_name, df, frac, seed):
    return plot_pass_map(player_name, df, frac=frac, seed=seed)

for col, idx in zip([col1, col2, col3], range(1,4)):
    with col:
        st.subheader(f"Player {idx}")

        # Team select
        selected_team = st.selectbox(f"Select Team {idx}", teams, key=f"team_{idx}")

        # Position select
        positions = ["ALL"] + team_to_positions[selected_team]
        selected_position = st.selectbox(f"Select Position {idx}", positions, key=f"pos_{idx}")

        # Player select
        if selected_position == "ALL":
            players = sorted(df["player"].unique())
        else:
            key = (selected_team, selected_position)
            players = team_pos_to_players.get(key, [])

        default_player = default_players[idx-1] if idx-1 < len(default_players) else None
        selected_player = st.selectbox(
            f"Select Player {idx}",
            players,
            index=players.index(default_player) if default_player in players else 0,
            key=f"player_{idx}"
        )

        # Fraction slider
        frac = st.slider(
            "Percentage of passes to show",
            min_value=0,
            max_value=100,
            value=30,  # default 30%
            step=1,
            key=f"frac_{idx}"
        ) / 100.0

        # Only recompute plot if player or slider changed
        state_player_key = f"state_player_{idx}"
        state_frac_key = f"state_frac_{idx}"

        if state_player_key not in st.session_state:
            st.session_state[state_player_key] = None
        if state_frac_key not in st.session_state:
            st.session_state[state_frac_key] = None

        if (st.session_state[state_player_key] != selected_player or
            st.session_state[state_frac_key] != frac):

            st.session_state[state_player_key] = selected_player
            st.session_state[state_frac_key] = frac

            # Display stats
            if selected_player:
                st.markdown(f"**{selected_player} Stats & xPass**")
                player_stats = build_player_stats(df, selected_player, MIN_PLAYER_PASSES)
                st.json({
                    "total_passes": int(player_stats["total_passes"]),
                    "avg_xP": float(player_stats["avg_xP"]),
                    "successful_passes": int(player_stats["successful_passes"])
                })

                player_df = calculate_difficult_passes(df, selected_player)

                # Generate and show plot
                fig = cached_plot(selected_player, df, frac, seed=14)
                st.pyplot(fig)