import streamlit as st
import pandas as pd
from analysis import load_data, build_player_stats, calculate_difficult_passes
from plots import plot_pass_map
from config import DATA_PATH, MIN_PLAYER_PASSES

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

# --- Coach insights helper ---
def generate_coach_insights(player_name, player_pos, diff_pct, easy_share, df):
    peers = df[df["position_group"] == player_pos]

    # --- Difficult pass performance ---
    HARD_PASS_THRESHOLD = df["xP"].quantile(0.20)
    player_difficult = df[(df["player"] == player_name) & (df["xP"] <= HARD_PASS_THRESHOLD)]
    peer_difficult = peers[peers["xP"] <= HARD_PASS_THRESHOLD]

    if len(player_difficult) > 0:
        player_completed = player_difficult["Outcome"].sum()
        player_expected = player_difficult["xP"].sum()
        diff = player_completed - player_expected

        peer_stats = peer_difficult.groupby("player")["Outcome"].sum() - peer_difficult.groupby("player")["xP"].sum()
        percentile = (peer_stats < diff).mean() * 100

        if percentile < 30:
            difficult_insight = "Struggles with difficult passes"
        elif percentile > 70:
            difficult_insight = "Excels at difficult passes"
        else:
            difficult_insight = "Average performance on difficult passes"
    else:
        difficult_insight = "Not enough difficult passes to evaluate"

    # --- Easy pass share vs peers (safe vs risky) ---
    peer_easy_share = peers.groupby("player").apply(lambda x: (x["xP"] >= df["xP"].quantile(0.50)).mean())
    easy_share_percentile = (peer_easy_share < easy_share).mean() * 100

    if easy_share_percentile > 70:
        safe_insight = "Tends to play it too safe compared to peers"
    elif easy_share_percentile < 30:
        safe_insight = "Tends to attempt riskier passes than peers"
    else:
        safe_insight = "Balanced approach between safe and difficult passes"

    return [difficult_insight, safe_insight]

# --- Page config ---
st.set_page_config(page_title="xPass Dashboard", layout="wide")
st.markdown("<h1 style='text-align: center; color: #2E86AB;'>xPass Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Compare player passing stats and xPass maps side by side</p>", unsafe_allow_html=True)

# --- Columns for 3 players ---
col1, col2, col3 = st.columns(3)
default_players = ["Romelu Lukaku Menama", "John Stones", "Eden Hazard"]

for col, idx in zip([col1, col2, col3], range(1, 4)):
    with col:
        st.subheader(f"Player {idx}")
        selected_team = st.selectbox(f"Select Team {idx}", teams, key=f"team_{idx}")
        positions = ["ALL"] + team_to_positions[selected_team]
        selected_position = st.selectbox(f"Select Position {idx}", positions, key=f"pos_{idx}")
        
        # Determine available players
        if selected_position == "ALL":
            players = sorted(df["player"].unique())
        else:
            key = (selected_team, selected_position)
            players = team_pos_to_players.get(key, [])
        default_player = default_players[idx - 1] if idx - 1 < len(default_players) else None
        selected_player = st.selectbox(
            f"Select Player {idx}",
            players,
            index=players.index(default_player) if default_player in players else 0,
            key=f"player_{idx}"
        )

        if selected_player:
            # --- Compute stats ---
            player_stats = cached_player_stats(df, selected_player)
            player_df = cached_difficult_passes(df, selected_player)

            total_passes = player_stats["total_passes"]
            successful_passes = player_stats["successful_passes"]
            avg_xP = player_stats["avg_xP"]
            completion_pct = (successful_passes / total_passes * 100) if total_passes > 0 else 0
            completion_xP = ((successful_passes - player_df["xP"].sum()) / total_passes) if total_passes > 0 else 0

            col_a, col_b, col_c, col_d, col_e = st.columns(5)
            col_a.metric("Total Passes", f"{int(total_passes):,}")
            col_b.metric("Successful Passes", f"{int(successful_passes):,}")
            col_c.metric("Completion %", f"{completion_pct:.1f}%")
            col_d.metric("Average xP", f"{avg_xP:.3f}")
            col_e.metric("Completion-xP (avg)", f"{completion_xP:.3f}")

            # --- Fraction of passes ---
            frac = st.slider("Percentage of passes to show", min_value=0, max_value=100, value=30, step=1, key=f"frac_{idx}") / 100.0
            fig = cached_plot(selected_player, df, frac=frac)
            st.pyplot(fig)

            # --- Player Insights ---
            st.subheader("Player Insights")
            HARD_PASS_THRESHOLD = df["xP"].quantile(0.20)
            EASY_PASS_THRESHOLD = df["xP"].quantile(0.50)
            VERY_EASY_PASS_THRESHOLD = df["xP"].quantile(0.80)
            MIN_DIFFICULT_PASSES = 10

            player_passes = df[df["player"] == selected_player].copy()
            difficult_passes = player_passes[player_passes["xP"] <= HARD_PASS_THRESHOLD]
            num_difficult = len(difficult_passes)

            if num_difficult >= MIN_DIFFICULT_PASSES:
                completed = difficult_passes["Outcome"].sum()
                expected_completed = difficult_passes["xP"].sum()
                diff_perf = completed - expected_completed
                diff_pct = completed / num_difficult
                expected_pct = expected_completed / num_difficult
                st.markdown(f"**Difficult Passes:** {num_difficult} attempts, "
                            f"{completed} completed vs {expected_completed:.2f} expected "
                            f"({diff_perf:+.2f}), completion {diff_pct:.0%} vs expected {expected_pct:.0%}")
            else:
                diff_pct = 0
                st.markdown("**Difficult Passes:** Not enough difficult passes to evaluate")

            easy_share = len(player_passes[player_passes["xP"] >= EASY_PASS_THRESHOLD]) / len(player_passes)
            very_easy_share = len(player_passes[player_passes["xP"] >= VERY_EASY_PASS_THRESHOLD]) / len(player_passes)
            st.markdown(f"**Easy Pass Share (top 50% xP):** {easy_share:.0%} | "
                        f"**Very Easy Pass Share (top 20% xP):** {very_easy_share:.0%}")

            # --- Coach Insights ---
            player_position = normalize_position(df[df["player"] == selected_player]["position"].iloc[0])
            insights = generate_coach_insights(
                selected_player,
                player_position,
                diff_pct,
                easy_share,
                df
            )

            st.subheader("Coach Insights")
            for insight in insights:
                st.markdown(f"- {insight}")