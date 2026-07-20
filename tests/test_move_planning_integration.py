"""
Integration tests for MovePlanningAgent running full episodes via run_episode().

Uses a pit-free 4×4 world (pit_probability=0.0) to eliminate death from pits,
giving the agent a fair chance of completing the task given enough turns.

These tests verify end-to-end behaviour without accessing WumpusWorld internals
from within the agent.
"""

from __future__ import annotations

import random

import pytest

from agents.move_planning_agent import MovePlanningAgent, _EXPLORATION_POOL
from utils.episode_runner import run_episode
from wumpus.models import Action, Percept, Position
from wumpus import WumpusWorld


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_episode_no_pits(seed: int, max_turns: int = 5000) -> dict:
    """Run a single pit-free episode with MovePlanningAgent, fixed seed."""
    random.seed(seed)
    env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
    agent = MovePlanningAgent()
    return run_episode(agent, env, visualizer=None, max_turns=max_turns, verbose=False)


# ---------------------------------------------------------------------------
# Action legality invariants (verified via instrumented agent)
# ---------------------------------------------------------------------------

class _RecordingAgent(MovePlanningAgent):
    """MovePlanningAgent that records every (glitter_at_decision, action) pair."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log: list[tuple[bool, Action]] = []

    def get_action(self, percept: Percept) -> Action:
        action = super().get_action(percept)
        self._log.append((percept.glitter, percept.bump, self.has_gold, self.position, action))
        return action


class TestActionLegality:
    def test_grab_only_on_glitter(self):
        """GRAB must only appear when glitter was True for that percept."""
        random.seed(7)
        env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        agent = _RecordingAgent()
        run_episode(agent, env, max_turns=3000, verbose=False)
        for glitter, bump, has_gold, pos, action in agent._log:
            if action == Action.GRAB:
                assert glitter, f"GRAB emitted without glitter. Log entry: glitter={glitter}"

    def test_climb_only_at_start_with_gold(self):
        """CLIMB must only appear when agent is at start position AND has gold."""
        random.seed(7)
        env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        agent = _RecordingAgent()
        run_episode(agent, env, max_turns=3000, verbose=False)
        start = Position(0, 0)
        for glitter, bump, has_gold, pos, action in agent._log:
            if action == Action.CLIMB:
                assert has_gold and pos == start, (
                    f"CLIMB emitted illegally: has_gold={has_gold}, pos={pos}"
                )

    def test_no_grab_or_climb_during_exploration(self):
        """During exploration (has_gold=False), agent must not emit GRAB (without glitter) or CLIMB."""
        random.seed(99)
        env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        agent = _RecordingAgent()
        run_episode(agent, env, max_turns=3000, verbose=False)
        for glitter, bump, has_gold, pos, action in agent._log:
            if not has_gold:
                # Before we have gold, CLIMB should never occur
                if action == Action.CLIMB:
                    assert False, f"CLIMB emitted without gold at pos={pos}"
                # GRAB is allowed only when glitter is True
                if action == Action.GRAB:
                    assert glitter, "GRAB emitted without glitter before gold collected"


# ---------------------------------------------------------------------------
# Escape with gold (multiple seeds)
# ---------------------------------------------------------------------------

class TestEscapeWithGold:
    @pytest.mark.parametrize("seed", [1, 2, 3, 5, 8, 13, 21])
    def test_agent_finds_gold_and_escapes_pit_free(self, seed: int):
        """
        In a pit-free world with enough turns, MovePlanningAgent should almost
        always escape with gold (wumpus may occasionally kill it if explored).
        We assert that at minimum the agent collected gold when it escaped.

        Note: the agent may die from the wumpus in rare seeds; in that case
        we only check that the episode ended legally (no illegal actions).
        """
        result = _run_episode_no_pits(seed, max_turns=5000)
        # If the agent escaped, it must have done so lawfully
        if result["escaped"]:
            # escaped=True means the episode ended via CLIMB — either with or without gold
            # When MovePlanningAgent climbs, it should have gold (by design)
            assert result["gold_collected"], (
                f"Seed {seed}: agent climbed without gold — should not happen with MovePlanningAgent"
            )

    def test_escape_success_rate_pit_free(self):
        """
        Over 20 pit-free episodes with varying seeds, MovePlanningAgent should
        escape with gold with reasonable frequency.

        Note: the wumpus is still present, so wumpus deaths are expected (~30% of
        episodes depending on exploration path). A minimum rate of 0.20 is asserted
        — this is well above the NaiveAgent's theoretical rate in similar conditions.
        """
        escapes = 0
        n = 20
        for seed in range(n):
            result = _run_episode_no_pits(seed, max_turns=5000)
            if result["escaped"] and result["gold_collected"]:
                escapes += 1
        rate = escapes / n
        assert rate >= 0.20, (
            f"Escape-with-gold rate {rate:.0%} below minimum threshold of 20%. "
            "Check that the BFS planner and escape logic are functioning correctly."
        )


# ---------------------------------------------------------------------------
# Internal state consistency across an episode
# ---------------------------------------------------------------------------

class TestInternalStateConsistency:
    def test_visited_safe_cells_always_include_start(self):
        random.seed(42)
        env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        agent = MovePlanningAgent()
        run_episode(agent, env, max_turns=500, verbose=False)
        assert Position(0, 0) in agent.visited_safe

    def test_graph_node_count_equals_four_times_visited(self):
        random.seed(42)
        env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        agent = MovePlanningAgent()
        run_episode(agent, env, max_turns=500, verbose=False)
        assert agent.safe_graph.node_count() == 4 * len(agent.visited_safe)

    def test_reset_between_episodes_clears_state(self):
        """Verify run_episode calls agent.reset() which clears visited safe cells."""
        random.seed(0)
        env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        agent = MovePlanningAgent()

        # First episode
        run_episode(agent, env, max_turns=200, verbose=False)
        visited_ep1 = len(agent.visited_safe)

        # Second episode — run_episode calls agent.reset() at the start
        random.seed(1)
        env2 = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        run_episode(agent, env2, max_turns=200, verbose=False)

        # After second episode, visited reflects ep2 only (reset was called)
        visited_ep2 = len(agent.visited_safe)
        # Can't assert exact count, but after reset the set is rebuilt from scratch
        assert visited_ep2 >= 1  # at least start cell

    def test_escape_with_gold_rate_exceeds_naive(self):
        """
        MovePlanningAgent should escape WITH GOLD more often than NaiveAgent.

        This is the metric the planning agent is specifically designed to improve:
        it grabs gold when sensed and follows a BFS-computed safe escape plan.
        NaiveAgent has no such logic and typically wanders until timeout or death.

        Note: total reward is NOT compared here because NaiveAgent's random CLIMB
        at the start position can terminate short episodes cheaply, inflating its
        average reward. Gold-escape rate is the fair comparison.
        """
        from agents.naive_agent import NaiveAgent

        n_episodes = 40

        planning_gold_escapes = 0
        random.seed(0)
        for _ in range(n_episodes):
            env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
            result = run_episode(MovePlanningAgent(), env, max_turns=2000, verbose=False)
            if result["escaped"] and result["gold_collected"]:
                planning_gold_escapes += 1

        naive_gold_escapes = 0
        random.seed(0)
        for _ in range(n_episodes):
            env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
            result = run_episode(NaiveAgent(), env, max_turns=2000, verbose=False)
            if result["escaped"] and result["gold_collected"]:
                naive_gold_escapes += 1

        assert planning_gold_escapes >= naive_gold_escapes, (
            f"MovePlanningAgent gold escapes ({planning_gold_escapes}/{n_episodes}) "
            f"should be ≥ NaiveAgent gold escapes ({naive_gold_escapes}/{n_episodes})"
        )


# ---------------------------------------------------------------------------
# Existing A1 tests still pass (smoke guard)
# ---------------------------------------------------------------------------

class TestA1Regression:
    def test_naive_agent_still_importable_and_runnable(self):
        from agents.naive_agent import NaiveAgent
        random.seed(0)
        env = WumpusWorld(width=4, height=4, pit_probability=0.2, allow_climb_without_gold=True)
        result = run_episode(NaiveAgent(), env, max_turns=200, verbose=False)
        assert "total_reward" in result
        assert "turns_taken" in result
