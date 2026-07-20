"""
Unit tests for agents/move_planning_agent.py — MovePlanningAgent.
"""

from __future__ import annotations

import collections
import random
from unittest.mock import patch

import pytest

from agents.move_planning_agent import MovePlanningAgent, _EXPLORATION_POOL
from wumpus.models import Action, Direction, Percept, Position


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_percept(**kwargs) -> Percept:
    """Create a Percept with all defaults False/0.0, overriding with kwargs."""
    return Percept(
        stench=kwargs.get("stench", False),
        breeze=kwargs.get("breeze", False),
        glitter=kwargs.get("glitter", False),
        bump=kwargs.get("bump", False),
        scream=kwargs.get("scream", False),
        reward=kwargs.get("reward", -1.0),
    )


def _empty_percept() -> Percept:
    return _make_percept()


def _bump_percept() -> Percept:
    return _make_percept(bump=True)


def _glitter_percept() -> Percept:
    return _make_percept(glitter=True)


# ---------------------------------------------------------------------------
# Exploration pool constraints
# ---------------------------------------------------------------------------

class TestExplorationPool:
    def test_grab_not_in_pool(self):
        assert Action.GRAB not in _EXPLORATION_POOL

    def test_climb_not_in_pool(self):
        assert Action.CLIMB not in _EXPLORATION_POOL

    def test_forward_in_pool(self):
        assert Action.FORWARD in _EXPLORATION_POOL

    def test_turn_left_in_pool(self):
        assert Action.TURN_LEFT in _EXPLORATION_POOL

    def test_turn_right_in_pool(self):
        assert Action.TURN_RIGHT in _EXPLORATION_POOL

    def test_shoot_in_pool(self):
        assert Action.SHOOT in _EXPLORATION_POOL

    def test_agent_never_returns_grab_without_glitter(self):
        """Over many random calls (seeded), GRAB never appears without glitter."""
        agent = MovePlanningAgent(rng=random.Random(0))
        for _ in range(500):
            action = agent.get_action(_empty_percept())
            assert action != Action.GRAB

    def test_agent_never_returns_climb_during_exploration(self):
        """Over many random calls (seeded), CLIMB never appears during random exploration."""
        agent = MovePlanningAgent(rng=random.Random(0))
        for _ in range(500):
            action = agent.get_action(_empty_percept())
            # CLIMB is only allowed at start with gold; agent has no gold here
            assert action != Action.CLIMB


# ---------------------------------------------------------------------------
# Glitter → GRAB behaviour
# ---------------------------------------------------------------------------

class TestGlitterGrab:
    def test_returns_grab_on_glitter(self):
        agent = MovePlanningAgent()
        action = agent.get_action(_glitter_percept())
        assert action == Action.GRAB

    def test_has_gold_set_after_grab(self):
        agent = MovePlanningAgent()
        agent.get_action(_glitter_percept())
        assert agent.has_gold is True

    def test_has_gold_false_before_grab(self):
        agent = MovePlanningAgent()
        assert agent.has_gold is False
        agent.get_action(_empty_percept())
        assert agent.has_gold is False

    def test_grab_not_returned_again_after_gold_collected(self):
        """After grabbing gold, GRAB must not be returned again (no second gold)."""
        # Build a 2-cell safe graph so BFS can plan a trivial escape
        agent = MovePlanningAgent(rng=random.Random(42))
        # First call: glitter → GRAB
        action = agent.get_action(_glitter_percept())
        assert action == Action.GRAB
        # Subsequent calls should not produce GRAB (no glitter)
        for _ in range(20):
            action = agent.get_action(_empty_percept())
            assert action != Action.GRAB


# ---------------------------------------------------------------------------
# Dead reckoning — position tracking
# ---------------------------------------------------------------------------

class TestPositionTracking:
    def test_initial_position_is_start(self):
        agent = MovePlanningAgent()
        assert agent.position == Position(0, 0)

    def test_initial_direction_is_east(self):
        agent = MovePlanningAgent()
        assert agent.direction == Direction.EAST

    def test_forward_advances_position(self):
        """
        Manually drive the agent: first call returns some action; we then
        simulate FORWARD was chosen by checking the next call with no bump.
        We bypass randomness by injecting a fixed sequence.
        """
        agent = MovePlanningAgent(rng=random.Random(0))
        # Force first action to be FORWARD by patching
        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.FORWARD
            agent.get_action(_empty_percept())  # turn 0: _last_action = FORWARD

        # Turn 1: percept with no bump → position should advance
        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.FORWARD
            agent.get_action(_empty_percept())  # applies FORWARD, no bump

        # Facing EAST from (0,0), FORWARD without bump → (1, 0)
        assert agent.position == Position(1, 0)

    def test_forward_with_bump_does_not_advance(self):
        agent = MovePlanningAgent(rng=random.Random(0))
        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.FORWARD
            agent.get_action(_empty_percept())  # turn 0: last_action = FORWARD

        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.FORWARD
            agent.get_action(_bump_percept())  # bumped — no move

        assert agent.position == Position(0, 0)

    def test_turn_left_updates_direction(self):
        agent = MovePlanningAgent(rng=random.Random(0))
        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.TURN_LEFT
            agent.get_action(_empty_percept())  # last_action = TURN_LEFT

        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.TURN_LEFT
            agent.get_action(_empty_percept())  # applies TURN_LEFT

        # EAST.turn_left() = NORTH
        assert agent.direction == Direction.NORTH

    def test_turn_right_updates_direction(self):
        agent = MovePlanningAgent(rng=random.Random(0))
        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.TURN_RIGHT
            agent.get_action(_empty_percept())  # last_action = TURN_RIGHT

        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.TURN_RIGHT
            agent.get_action(_empty_percept())  # applies TURN_RIGHT

        # EAST.turn_right() = SOUTH
        assert agent.direction == Direction.SOUTH

    def test_four_turns_right_returns_to_original_direction(self):
        agent = MovePlanningAgent(rng=random.Random(0))
        for _ in range(5):  # 4 + 1 (first call sets last_action)
            with patch.object(agent, "_rng") as mock_rng:
                mock_rng.choice.return_value = Action.TURN_RIGHT
                agent.get_action(_empty_percept())
        assert agent.direction == Direction.EAST  # 4 right turns = full circle

    def test_shoot_does_not_change_position_or_direction(self):
        agent = MovePlanningAgent(rng=random.Random(0))
        pos_before = agent.position
        dir_before = agent.direction
        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.SHOOT
            agent.get_action(_empty_percept())  # last_action = SHOOT

        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.SHOOT
            agent.get_action(_empty_percept())  # applies SHOOT effect (none)

        assert agent.position == pos_before
        assert agent.direction == dir_before


# ---------------------------------------------------------------------------
# Visited safe cells
# ---------------------------------------------------------------------------

class TestVisitedSafeCells:
    def test_start_cell_added_on_first_call(self):
        agent = MovePlanningAgent()
        agent.get_action(_empty_percept())
        assert Position(0, 0) in agent.visited_safe

    def test_new_cell_added_after_successful_forward(self):
        agent = MovePlanningAgent(rng=random.Random(0))
        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.FORWARD
            agent.get_action(_empty_percept())  # last=FORWARD

        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.FORWARD
            agent.get_action(_empty_percept())  # moves to (1,0)

        assert Position(1, 0) in agent.visited_safe

    def test_bumped_cell_not_added(self):
        """After a FORWARD+bump, position stays at (0,0); only (0,0) is in visited."""
        agent = MovePlanningAgent(rng=random.Random(0))
        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.FORWARD
            agent.get_action(_empty_percept())  # last=FORWARD

        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.FORWARD
            agent.get_action(_bump_percept())  # bumped, stays at (0,0)

        # Only the start cell should be visited; position (−1,0) or (1,0) not added
        assert len(agent.visited_safe) == 1
        assert Position(0, 0) in agent.visited_safe


# ---------------------------------------------------------------------------
# Safe graph — node count proportional to visited cells
# ---------------------------------------------------------------------------

class TestSafeGraphNodes:
    def test_graph_has_four_nodes_per_visited_cell(self):
        agent = MovePlanningAgent(rng=random.Random(0))
        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.FORWARD
            agent.get_action(_empty_percept())  # last=FORWARD

        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.FORWARD
            agent.get_action(_empty_percept())  # moves to (1,0)

        n_visited = len(agent.visited_safe)
        assert agent.safe_graph.node_count() == 4 * n_visited


# ---------------------------------------------------------------------------
# Climb when at start with gold
# ---------------------------------------------------------------------------

class TestClimbBehavior:
    def test_climb_when_at_start_with_gold(self):
        """Simulate agent grabbing gold at start (unusual but valid edge case)."""
        agent = MovePlanningAgent()
        # First call: glitter at start → GRAB, sets has_gold
        agent.get_action(_glitter_percept())
        assert agent.has_gold
        # Second call: still at start (0,0), has gold → CLIMB
        action = agent.get_action(_empty_percept())
        assert action == Action.CLIMB

    def test_no_climb_without_gold(self):
        """Agent must never return CLIMB if it does not have gold."""
        agent = MovePlanningAgent(rng=random.Random(123))
        for _ in range(200):
            action = agent.get_action(_empty_percept())
            assert action != Action.CLIMB


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_restores_position(self):
        agent = MovePlanningAgent(rng=random.Random(0))
        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.FORWARD
            agent.get_action(_empty_percept())  # last=FORWARD

        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.FORWARD
            agent.get_action(_empty_percept())  # moves

        agent.reset()
        assert agent.position == Position(0, 0)

    def test_reset_restores_direction(self):
        agent = MovePlanningAgent(rng=random.Random(0))
        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.TURN_RIGHT
            agent.get_action(_empty_percept())  # last=TURN_RIGHT

        with patch.object(agent, "_rng") as mock_rng:
            mock_rng.choice.return_value = Action.TURN_RIGHT
            agent.get_action(_empty_percept())  # changes direction

        agent.reset()
        assert agent.direction == Direction.EAST

    def test_reset_clears_gold(self):
        agent = MovePlanningAgent()
        agent.get_action(_glitter_percept())
        assert agent.has_gold
        agent.reset()
        assert not agent.has_gold

    def test_reset_clears_visited_safe(self):
        agent = MovePlanningAgent(rng=random.Random(0))
        agent.get_action(_empty_percept())
        assert len(agent.visited_safe) > 0
        agent.reset()
        assert len(agent.visited_safe) == 0

    def test_reset_clears_safe_graph(self):
        agent = MovePlanningAgent(rng=random.Random(0))
        agent.get_action(_empty_percept())
        assert agent.safe_graph.node_count() > 0
        agent.reset()
        assert agent.safe_graph.node_count() == 0

    def test_reset_clears_last_action(self):
        agent = MovePlanningAgent(rng=random.Random(0))
        agent.get_action(_empty_percept())
        agent.reset()
        # After reset, first call skips dead reckoning (_last_action is None)
        # and should not raise
        action = agent.get_action(_empty_percept())
        assert isinstance(action, Action)


# ---------------------------------------------------------------------------
# Plan execution — smoke tests
# ---------------------------------------------------------------------------

class TestPlanExecution:
    def test_plan_actions_are_from_action_enum(self):
        """Once we have gold, every action emitted must be a valid Action."""
        agent = MovePlanningAgent(rng=random.Random(0))
        # Grab gold
        agent.get_action(_glitter_percept())
        # Execute next 20 actions (plan + exploration if plan is None)
        for _ in range(20):
            action = agent.get_action(_empty_percept())
            assert isinstance(action, Action)
