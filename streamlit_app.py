"""Streamlit web UI for the Wumpus World simulator (advanced visualization).

This is an OPTIONAL, richer alternative to the ASCII CLI in ``main.py``. The CLI
remains fully intact for debugging/history. Both share the same core game logic
via ``utils.episode_runner.run_episode`` and the same ``WumpusWorld``/agents.

Run with:
    streamlit run streamlit_app.py

Two tabs:
    - Replay: generate a single episode and step through it turn by turn.
    - Statistics: run many episodes and view aggregate metrics + charts.
"""

from __future__ import annotations

import random

import pandas as pd
import streamlit as st

from agents import NaiveAgent, MovePlanningAgent
from utils import run_episode
from utils.streamlit_render import (
    direction_emoji,
    percept_badges,
    render_board_html,
    visited_cells_up_to,
)
from wumpus import WumpusWorld

st.set_page_config(page_title="Wumpus World", page_icon="\U0001f479", layout="wide")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _build_world(cfg: dict) -> WumpusWorld:
    """Create a WumpusWorld from a config dict."""
    return WumpusWorld(
        width=cfg["width"],
        height=cfg["height"],
        allow_climb_without_gold=cfg["allow_climb"],
        pit_probability=cfg["pit_prob"],
    )


def _make_agent(cfg: dict):
    """Instantiate the selected agent."""
    if cfg["agent"] == "move_planning":
        return MovePlanningAgent()
    return NaiveAgent()


def _generate_replay(cfg: dict) -> dict:
    """Run a single episode with history captured for step-through replay."""
    if cfg["seed"] is not None:
        random.seed(cfg["seed"])
    env = _build_world(cfg)
    agent = _make_agent(cfg)
    return run_episode(
        agent,
        env,
        visualizer=None,
        max_turns=cfg["max_turns"],
        verbose=False,
        record_history=True,
    )


def _run_batch(cfg: dict) -> list[dict]:
    """Run multiple episodes (no history) for aggregate statistics."""
    if cfg["seed"] is not None:
        random.seed(cfg["seed"])
    results = []
    for _ in range(cfg["num_episodes"]):
        env = _build_world(cfg)
        agent = _make_agent(cfg)
        results.append(
            run_episode(
                agent,
                env,
                visualizer=None,
                max_turns=cfg["max_turns"],
                verbose=False,
                record_history=False,
            )
        )
    return results


def _outcome_label(result: dict) -> str:
    if result["escaped"] and result["gold_collected"]:
        return "ESCAPED (success!)"
    if result["escaped"]:
        return "ESCAPED (no gold)"
    if result["died"]:
        return "DIED"
    return "TIMEOUT"


# --------------------------------------------------------------------------- #
# Sidebar configuration
# --------------------------------------------------------------------------- #
st.sidebar.header("\u2699\ufe0f Configuration")

agent_choice = st.sidebar.selectbox(
    "Agent",
    options=["move_planning", "naive"],
    format_func=lambda x: "MovePlanningAgent" if x == "move_planning" else "NaiveAgent",
    index=0,
)

width = st.sidebar.slider("World width", min_value=2, max_value=8, value=4)
height = st.sidebar.slider("World height", min_value=2, max_value=8, value=4)
pit_prob = st.sidebar.slider("Pit probability", min_value=0.0, max_value=0.6, value=0.2, step=0.05)
allow_climb = st.sidebar.checkbox("Allow climb without gold", value=True)
max_turns = st.sidebar.slider("Max turns", min_value=10, max_value=2000, value=1000, step=10)
num_episodes = st.sidebar.slider("Episodes (Statistics tab)", min_value=1, max_value=500, value=20)

use_seed = st.sidebar.checkbox("Use fixed random seed", value=False)
seed_value = st.sidebar.number_input("Seed", min_value=0, max_value=10_000_000, value=42, step=1)
reveal_hidden = st.sidebar.checkbox("Reveal hidden world (debug)", value=False)

config = {
    "width": width,
    "height": height,
    "pit_prob": pit_prob,
    "allow_climb": allow_climb,
    "max_turns": max_turns,
    "num_episodes": num_episodes,
    "seed": int(seed_value) if use_seed else None,
    "agent": agent_choice,
}

st.title("\U0001f479 Wumpus World \u2014 Advanced Visualization")
_agent_caption = "MovePlanningAgent (BFS escape planner)" if agent_choice == "move_planning" else "NaiveAgent (uniform random actions)"
st.caption(f"{_agent_caption}. The ASCII CLI (main.py) remains available for debugging.")

replay_tab, stats_tab = st.tabs(["\U0001f3ae Replay", "\U0001f4ca Statistics"])


# --------------------------------------------------------------------------- #
# Replay tab
# --------------------------------------------------------------------------- #
with replay_tab:
    ctrl_col, _ = st.columns([1, 3])
    with ctrl_col:
        if st.button("\U0001f3b2 Generate episode", use_container_width=True):
            st.session_state["replay"] = _generate_replay(config)
            st.session_state["turn_index"] = 0

    replay = st.session_state.get("replay")

    if replay is None:
        st.info("Click **Generate episode** to create a playthrough you can step through.")
    else:
        history = replay["history"]
        world_layout = replay["world_layout"]
        last_index = len(history) - 1

        if "turn_index" not in st.session_state:
            st.session_state["turn_index"] = 0

        # Playback controls
        c1, c2, c3, c4, c5 = st.columns(5)
        if c1.button("\u23ee\ufe0f First", use_container_width=True):
            st.session_state["turn_index"] = 0
        if c2.button("\u25c0\ufe0f Prev", use_container_width=True):
            st.session_state["turn_index"] = max(0, st.session_state["turn_index"] - 1)
        if c3.button("\u25b6\ufe0f Next", use_container_width=True):
            st.session_state["turn_index"] = min(last_index, st.session_state["turn_index"] + 1)
        if c4.button("\u23ed\ufe0f Last", use_container_width=True):
            st.session_state["turn_index"] = last_index
        if c5.button("\U0001f504 Reset", use_container_width=True):
            st.session_state["turn_index"] = 0

        if last_index > 0:
            st.session_state["turn_index"] = st.slider(
                "Turn", min_value=0, max_value=last_index,
                value=st.session_state["turn_index"],
            )

        index = st.session_state["turn_index"]
        snapshot = history[index]
        visited = visited_cells_up_to(history, index)

        board_col, info_col = st.columns([3, 2])
        with board_col:
            st.markdown(
                render_board_html(snapshot, world_layout, reveal_hidden, visited),
                unsafe_allow_html=True,
            )
            if not reveal_hidden:
                st.caption("Tip: enable **Reveal hidden world** in the sidebar to see wumpus/gold/pits.")

        with info_col:
            action = snapshot["action"]
            st.subheader(f"Turn {snapshot['turn']} of {last_index}")
            if action:
                st.write(f"**Action:** {action}")
            else:
                st.write("**Action:** _(initial state)_")
            st.write(
                f"**Position:** {snapshot['position']}  "
                f"{direction_emoji(snapshot['direction'])} {snapshot['direction']}"
            )
            st.write(f"**Percepts:** {percept_badges(snapshot['percept'])}")

            m1, m2 = st.columns(2)
            m1.metric("Turn reward", f"{snapshot['reward']:.0f}")
            m2.metric("Total reward", f"{snapshot['total_reward']:.0f}")

            status = "Alive \U0001f7e2" if snapshot["alive"] else f"Dead \U0001f534 ({snapshot['death_cause']})"
            st.write(f"**Status:** {status}")
            st.write(
                f"**Inventory:** Gold={'\u2705' if snapshot['has_gold'] else '\u274c'}  "
                f"Arrow={'\u2705' if snapshot['has_arrow'] else '\u274c'}"
            )

        # Episode summary
        st.divider()
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Outcome", _outcome_label(replay))
        s2.metric("Steps", replay["turns_taken"])
        s3.metric("Final reward", f"{replay['total_reward']:.0f}")
        s4.metric("Gold collected", "Yes" if replay["gold_collected"] else "No")


# --------------------------------------------------------------------------- #
# Statistics tab
# --------------------------------------------------------------------------- #
with stats_tab:
    if st.button("\u25b6\ufe0f Run batch", use_container_width=False):
        st.session_state["batch"] = _run_batch(config)

    batch = st.session_state.get("batch")

    if batch is None:
        st.info("Click **Run batch** to simulate multiple episodes and view aggregate statistics.")
    else:
        n = len(batch)
        escapes = sum(1 for r in batch if r["escaped"])
        deaths = sum(1 for r in batch if r["died"])
        golds = sum(1 for r in batch if r["gold_collected"])
        total_reward = sum(r["total_reward"] for r in batch)
        total_steps = sum(r["turns_taken"] for r in batch)

        c1, c2, c3 = st.columns(3)
        c1.metric("Escape rate", f"{100 * escapes / n:.1f}%")
        c2.metric("Death rate", f"{100 * deaths / n:.1f}%")
        c3.metric("Gold rate", f"{100 * golds / n:.1f}%")

        c4, c5, c6 = st.columns(3)
        c4.metric("Avg reward", f"{total_reward / n:.1f}")
        c5.metric("Avg steps", f"{total_steps / n:.1f}")
        c6.metric("Episodes", n)

        df = pd.DataFrame(
            {
                "episode": range(1, n + 1),
                "reward": [r["total_reward"] for r in batch],
                "steps": [r["turns_taken"] for r in batch],
                "outcome": [_outcome_label(r) for r in batch],
            }
        )

        st.subheader("Reward per episode")
        st.bar_chart(df.set_index("episode")["reward"])

        st.subheader("Outcome distribution")
        st.bar_chart(df["outcome"].value_counts())

        with st.expander("Per-episode table"):
            st.dataframe(df, use_container_width=True, hide_index=True)
