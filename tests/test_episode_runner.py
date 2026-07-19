"""
Tests for utils.episode_runner.run_episode().

These tests verify the flag assignment logic in run_episode() — specifically
the three episode termination paths:

1. Climb without gold  → escaped=True,  died=False, gold_collected=False
2. Death (pit/wumpus) → escaped=False, died=True,  gold_collected=False
3. Escape with gold   → escaped=True,  died=False, gold_collected=True

Each test uses a ScriptedAgent that replays a fixed sequence of actions so
results are deterministic without relying on random seeds.

Why these tests exist:
    A bug caused climb-without-gold episodes to report escaped=False and
    died=False (showing as TIMEOUT) because the reward of -1 didn't satisfy
    either branch of the old `if ended:` block in run_episode(). This suite
    locks in the correct behaviour for all three termination paths.
"""

import pytest
from agents.base_agent import Agent
from utils.episode_runner import run_episode
from wumpus import WumpusWorld
from wumpus.models import Action, Percept


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
class ScriptedAgent(Agent):
    """Agent that replays a fixed list of actions then falls back to CLIMB."""

    def __init__(self, actions: list[Action]):
        self._script = list(actions)
        self._index = 0

    def get_action(self, percept: Percept) -> Action:
        if self._index < len(self._script):
            action = self._script[self._index]
            self._index += 1
            return action
        return Action.CLIMB  # safe fallback

    def reset(self) -> None:
        self._index = 0


def _safe_world(**kwargs) -> WumpusWorld:
    """4×4 world with no pits so the agent can't accidentally die."""
    return WumpusWorld(width=4, height=4, pit_probability=0.0, **kwargs)


# --------------------------------------------------------------------------- #
# Termination: climb without gold
# --------------------------------------------------------------------------- #
class TestClimbWithoutGold:
    """CLIMB at [1,1] without gold ends the episode with escaped=True, not TIMEOUT."""

    def test_escaped_is_true(self):
        """Agent that immediately CLIMBs should have escaped=True."""
        env = _safe_world(allow_climb_without_gold=True)
        agent = ScriptedAgent([Action.CLIMB])
        result = run_episode(agent, env, verbose=False)
        assert result["escaped"] is True

    def test_died_is_false(self):
        """Agent that CLIMBs without gold should not be marked as died."""
        env = _safe_world(allow_climb_without_gold=True)
        agent = ScriptedAgent([Action.CLIMB])
        result = run_episode(agent, env, verbose=False)
        assert result["died"] is False

    def test_gold_collected_is_false(self):
        """Agent that CLIMBs without gold should not be marked as gold_collected."""
        env = _safe_world(allow_climb_without_gold=True)
        agent = ScriptedAgent([Action.CLIMB])
        result = run_episode(agent, env, verbose=False)
        assert result["gold_collected"] is False

    def test_turns_taken_is_one(self):
        """Episode ends on turn 1 (the CLIMB action)."""
        env = _safe_world(allow_climb_without_gold=True)
        agent = ScriptedAgent([Action.CLIMB])
        result = run_episode(agent, env, verbose=False)
        assert result["turns_taken"] == 1

    def test_reward_is_negative_one(self):
        """Climb without gold costs only the time penalty (-1)."""
        env = _safe_world(allow_climb_without_gold=True)
        agent = ScriptedAgent([Action.CLIMB])
        result = run_episode(agent, env, verbose=False)
        assert result["total_reward"] == -1

    def test_climb_disallowed_does_not_end_episode(self):
        """When allow_climb_without_gold=False, CLIMB at [1,1] has no effect and
        the episode continues (episode runner does not mark it as ended)."""
        env = _safe_world(allow_climb_without_gold=False)
        # CLIMB (no effect) then CLIMB again (also no effect) — stays alive after 2 turns
        agent = ScriptedAgent([Action.CLIMB, Action.CLIMB])
        result = run_episode(agent, env, verbose=False, max_turns=2)
        # Episode ends by max_turns, not by the CLIMB actions
        assert result["escaped"] is False
        assert result["died"] is False
        assert result["turns_taken"] == 2


# --------------------------------------------------------------------------- #
# Termination: death
# --------------------------------------------------------------------------- #
class TestDeath:
    """Moving onto the wumpus ends the episode with died=True."""

    def _seed_for_wumpus_east(self) -> int:
        """Return seed S such that:
            random.seed(S) -> WumpusWorld() [first _initialize_world] ->
            env.reset() [second _initialize_world, i.e. what run_episode does]
        places the wumpus at internal (1,0) == user (2,1).
        WumpusWorld.__init__ calls _initialize_world() itself, so both the
        constructor call AND run_episode's reset() consume random state."""
        import random
        for seed in range(10_000):
            random.seed(seed)
            env = WumpusWorld(width=4, height=4, pit_probability=0.0,
                              allow_climb_without_gold=True)
            env.reset()  # mirrors what run_episode will do
            if env.get_wumpus_position().x == 1 and env.get_wumpus_position().y == 0:
                return seed
        pytest.skip("Could not find a seed placing wumpus at (2,1) within 10 000 tries")

    def test_died_is_true_on_wumpus(self):
        import random
        seed = self._seed_for_wumpus_east()
        random.seed(seed)
        env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        agent = ScriptedAgent([Action.FORWARD])  # walk into wumpus at (2,1)
        result = run_episode(agent, env, verbose=False)
        assert result["died"] is True

    def test_escaped_is_false_on_death(self):
        import random
        seed = self._seed_for_wumpus_east()
        random.seed(seed)
        env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        agent = ScriptedAgent([Action.FORWARD])
        result = run_episode(agent, env, verbose=False)
        assert result["escaped"] is False

    def test_reward_is_death_penalty(self):
        import random
        seed = self._seed_for_wumpus_east()
        random.seed(seed)
        env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        agent = ScriptedAgent([Action.FORWARD])
        result = run_episode(agent, env, verbose=False)
        # Environment returns exactly -1000 for death (time cost absorbed into penalty)
        assert result["total_reward"] == -1000


# --------------------------------------------------------------------------- #
# Termination: escape with gold
# --------------------------------------------------------------------------- #
class TestEscapeWithGold:
    """Navigate to gold, grab it, return to [1,1] and CLIMB -> +1000 reward."""

    # Gold is never placed at the start square [1,1] (assignment rule), so find
    # a seed where it lands at internal (1,0) == user (2,1): one step east.
    # Navigate: FORWARD (to 2,1), GRAB, TURN_LEFT, TURN_LEFT (face WEST), FORWARD (back to 1,1), CLIMB.
    _GOLD_EAST_ROUTE = [
        Action.FORWARD,    # move east to (2,1) where gold is
        Action.GRAB,       # pick up gold
        Action.TURN_LEFT,  # EAST -> NORTH
        Action.TURN_LEFT,  # NORTH -> WEST
        Action.FORWARD,    # move west back to (1,1)
        Action.CLIMB,      # exit with gold -> +1000
    ]

    def _seed_for_gold_east(self) -> int:
        """Return seed S such that:
            random.seed(S) -> WumpusWorld() [first _initialize_world] ->
            env.reset() [second _initialize_world, i.e. what run_episode does]
        places gold at internal (1,0) == user (2,1) with no wumpus blocking.
        WumpusWorld.__init__ calls _initialize_world() itself, so both calls
        consume random state and must be mirrored exactly in the test."""
        import random
        for seed in range(10_000):
            random.seed(seed)
            env = WumpusWorld(width=4, height=4, pit_probability=0.0,
                              allow_climb_without_gold=True)
            env.reset()  # mirrors what run_episode will do
            gold = env.get_gold_position()
            wumpus = env.get_wumpus_position()
            if gold is not None and gold.x == 1 and gold.y == 0:
                # Also ensure the wumpus isn't at (1,0) so GRAB doesn't kill the agent
                if wumpus is None or not (wumpus.x == 1 and wumpus.y == 0):
                    return seed
        pytest.skip("Could not find a seed placing gold at (2,1) within 10 000 tries")

    def test_escaped_is_true_with_gold(self):
        import random
        seed = self._seed_for_gold_east()
        random.seed(seed)
        env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        agent = ScriptedAgent(self._GOLD_EAST_ROUTE)
        result = run_episode(agent, env, verbose=False)
        assert result["escaped"] is True

    def test_gold_collected_is_true(self):
        import random
        seed = self._seed_for_gold_east()
        random.seed(seed)
        env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        agent = ScriptedAgent(self._GOLD_EAST_ROUTE)
        result = run_episode(agent, env, verbose=False)
        assert result["gold_collected"] is True

    def test_died_is_false_with_gold_escape(self):
        import random
        seed = self._seed_for_gold_east()
        random.seed(seed)
        env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        agent = ScriptedAgent(self._GOLD_EAST_ROUTE)
        result = run_episode(agent, env, verbose=False)
        assert result["died"] is False

    def test_reward_is_positive_on_gold_escape(self):
        import random
        seed = self._seed_for_gold_east()
        random.seed(seed)
        env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
        agent = ScriptedAgent(self._GOLD_EAST_ROUTE)
        result = run_episode(agent, env, verbose=False)
        # +1000 (escape) -1 (forward) -1 (grab) -1 (turn) -1 (turn) -1 (forward) = 995
        assert result["total_reward"] == 995
