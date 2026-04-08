import streamlit as st
import pandas as pd
from analysis import load_data, build_player_stats, calculate_difficult_passes
from plots import plot_pass_map
from config import DATA_PATH, MIN_PLAYER_PASSES

# --- Page config ---
st.set_page_config(page_title="xPass Dashboard", layout="wide")

# --- Style ---
st.markdown("""
<style>

/* Reduce default metric padding if used elsewhere */
[data-testid="stMetric"] {
    padding: 2px 2px;
}

</style>
""", unsafe_allow_html=True)

# --- Pitch dimensions ---
PITCH_LENGTH = 120
PITCH_WIDTH = 80

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
df = df.dropna(subset=["start_x", "start_y", "end_x", "end_y"])
df["position_group"] = df["position"].apply(normalize_position)

# --- Precompute team to positions and players ---
team_to_positions = {}
team_pos_to_players = {}

teams = ["ALL"] + sorted(df["team"].unique())

for team in teams:

    team_df = df if team == "ALL" else df[df["team"] == team]

    positions = sorted(
        team_df["position_group"].unique(),
        key=lambda x: POSITION_ORDER.index(x) if x in POSITION_ORDER else 999
    )

    team_to_positions[team] = positions

    for pos in positions:

        key = (team, pos)

        players = sorted(team_df[team_df["position_group"] == pos]["player"].unique())

        team_pos_to_players[key] = players

# --- Cache expensive operations ---
@st.cache_data
def cached_player_stats(df, player_name):
    return build_player_stats(df, player_name, MIN_PLAYER_PASSES)

@st.cache_data
def cached_difficult_passes(df, player_name):
    return calculate_difficult_passes(df, player_name)

@st.cache_data
def cached_plot(player_name, df, frac, seed=14):
    return plot_pass_map(player_name, df, frac=frac, seed=seed)

# --- Title ---
st.markdown("""
<div style="text-align: center; background: linear-gradient(90deg, #FF7F50, #2E86AB); 
            padding: 20px; border-radius: 15px; color: white;">
    <h1 style="margin: 0; font-family: 'Arial Black', sans-serif;">
        xPass Dashboard - Premier League 2015/16
    </h1>
    <p style="margin: 0; font-size: 18px;">Compare player passing stats and xPass maps side by side</p>
</div>
""", unsafe_allow_html=True)

# --- Columns for players ---
col1, spacer1, col2, spacer2, col3 = st.columns([1,0.04,1,0.04,1])

default_players = [
    "Romelu Lukaku Menama",
    "John Stones",
    "Eden Hazard"
]

for col, idx in zip([col1, col2, col3], range(1,4)):

    with col:

        st.subheader(f"Player {idx}")

        selected_team = st.selectbox(f"Select Team {idx}", teams, key=f"team_{idx}")

        positions = ["ALL"] + team_to_positions[selected_team]

        selected_position = st.selectbox(f"Select Position {idx}", positions, key=f"pos_{idx}")

        if selected_position == "ALL":
            players = sorted(df["player"].unique())
        else:
            key = (selected_team, selected_position)
            players = team_pos_to_players.get(key, [])

        default_player = default_players[idx-1]

        selected_player = st.selectbox(
            f"Select Player {idx}",
            players,
            index=players.index(default_player) if default_player in players else 0,
            key=f"player_{idx}"
        )

        if selected_player:

            player_stats = cached_player_stats(df, selected_player)
            player_df = cached_difficult_passes(df, selected_player)

            total_passes = player_stats["total_passes"]
            successful_passes = player_stats["successful_passes"]
            avg_xP = player_stats["avg_xP"]

            completion_pct = (successful_passes / total_passes * 100) if total_passes > 0 else 0
            completion_xP = ((successful_passes - player_df["xP"].sum()) / total_passes) if total_passes > 0 else 0

            col_a, col_b, col_c, col_d, col_e = st.columns(5, gap="small")

            # --- Custom metric card ---
            def custom_metric(label, value):

                value_str = str(value)

                if len(value_str) > 6:
                    value_size = 16
                elif len(value_str) > 4:
                    value_size = 18
                else:
                    value_size = 20

                st.markdown(
                    f"""
                    <div style="
                        background:#f8f9fb;
                        padding:8px;
                        border-radius:10px;
                        text-align:center;
                        height:66px;
                        display:flex;
                        flex-direction:column;
                        justify-content:center;
                        margin:2px;
                    ">
                        <div style="font-size:11px; line-height:1.1;">
                            {label}
                        </div>
                        <div style="font-size:{value_size}px; font-weight:600;">
                            {value}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col_a:
                custom_metric("Total<br>Passes", f"{total_passes:,.0f}")

            with col_b:
                custom_metric("Successful<br>Passes", f"{successful_passes:,.0f}")

            with col_c:
                custom_metric("Completion<br>%", f"{completion_pct:.1f}%")

            with col_d:
                custom_metric("Average<br>xP", f"{avg_xP:.3f}")

            with col_e:
                custom_metric("Completion-xP<br>(avg)", f"{completion_xP:.3f}")

            frac = st.slider(
                "Percentage of passes to show",
                min_value=0,
                max_value=100,
                value=30,
                step=1,
                key=f"frac_{idx}"
            ) / 100

            fig = cached_plot(selected_player, df, frac=frac)

            st.pyplot(fig)

# --- About panel ---
st.markdown("""
<div style="background: #ffffff; padding:30px 25px; border-radius:15px; 
            max-width:800px; margin:auto; text-align:center; font-size:16px; line-height:1.6; 
            margin-top:50px; margin-bottom:60px; box-shadow:0 4px 12px rgba(0,0,0,0.1);">

<h2 style="background: linear-gradient(90deg, #FF7F50, #2E86AB); 
           -webkit-background-clip: text; color: transparent; 
           font-size:28px; margin-bottom:16px; font-family: 'Arial Black', sans-serif;">
About the Creator
</h2>

<p>Hi, I’m <b>Victoria Friss de Kereki</b>, a Data Scientist specialising in <b>sports analytics</b>.</p>

<p>This xPass Dashboard visualises player passing behaviour using expected pass models.</p>

</div>
""", unsafe_allow_html=True)