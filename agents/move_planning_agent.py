"""
MovePlanningAgent — a planning-capable Wumpus World agent.

This agent improves on the NaiveAgent by:
1. Maintaining internal dead-reckoning state (estimated position and direction).
2. Tracking all visited safe cells and storing them in a NetworkX-backed safe graph.
3. Using a custom BFS planner to find the shortest safe escape route once gold
   has been collected.
4. Applying rule-based action overrides (GRAB on glitter, CLIMB when home with gold)
   while falling back to filtered random exploration otherwise.

The agent NEVER accesses WumpusWorld state directly. It operates solely from
the Percept objects it receives through the Agent interface.
"""

from __future__ import annotations

import collections
import random as _random_module
from random import Random
from typing import Optional

from agents.base_agent import Agent
from agents.bfs_planner import SafeGraph, bfs_shortest_actions
from wumpus.models import Action, Direction, Percept, Position

# Exploration pool: GRAB and CLIMB are excluded (they are only taken via rule-based
# overrides when the appropriate conditions are met).
_EXPLORATION_POOL: list[Action] = [
    Action.FORWARD,
    Action.TURN_LEFT,
    Action.TURN_RIGHT,
    Action.SHOOT,
]


class MovePlanningAgent(Agent):
    """
    A Wumpus World agent with internal state tracking and BFS-based escape planning.

    Behaviour summary:
    - Maintains estimated position and direction via dead reckoning.
    - Registers every successfully entered cell as safe in an internal graph.
    - On sensing glitter: grabs gold, plans shortest safe route back to start,
      then executes the plan and climbs out.
    - Explores randomly otherwise, choosing only from [FORWARD, TURN_LEFT,
      TURN_RIGHT, SHOOT] — never GRAB or CLIMB during exploration.

    Args:
        start_position: Internal (0-based) start position. Defaults to (0, 0).
        start_direction: Initial facing direction. Defaults to EAST.
        rng: Optional seeded Random instance for deterministic tests. If None,
             the module-level random state is used.
    """

    def __init__(
        self,
        start_position: Position = Position(0, 0),
        start_direction: Direction = Direction.EAST,
        rng: Optional[Random] = None,
    ) -> None:
        self._start_position = start_position
        self._start_direction = start_direction
        self._rng: Random = rng if rng is not None else _random_module  # type: ignore[assignment]

        # Mutable episode state (also reset by reset())
        self._position: Position = start_position
        self._direction: Direction = start_direction
        self._has_gold: bool = False
        self._visited_safe: set[Position] = set()
        self._safe_graph: SafeGraph = SafeGraph()
        self._last_action: Optional[Action] = None
        self._plan: collections.deque[Action] = collections.deque()
        self._plan_exhausted_once: bool = False  # True after first failed BFS

    # ------------------------------------------------------------------
    # Agent interface
    # ------------------------------------------------------------------

    def get_action(self, percept: Percept) -> Action:
        """
        Select the next action based on the current percept.

        Processing order:
        1. Update estimated position/direction from the previous action + percept.
        2. Register the current cell as safe.
        3. Apply rule-based overrides (CLIMB, plan execution, GRAB).
        4. Fallback: filtered random exploration.

        Args:
            percept: Sensory information from the environment.

        Returns:
            The chosen Action.
        """
        # Step 1: Dead reckoning — update position/direction from last action
        self._update_position(percept)

        # Step 2: Register current cell as safe (agent is alive = survived this cell)
        self._mark_safe(self._position)

        # Step 3: Rule-based overrides

        # 3a. If we have gold and are back at start → CLIMB
        if self._has_gold and self._position == self._start_position:
            action = Action.CLIMB
            self._last_action = action
            return action

        # 3b. If we have gold and there is a queued plan → execute it
        if self._has_gold and self._plan:
            action = self._plan.popleft()
            self._last_action = action
            return action

        # 3c. If we have gold but the plan is empty → compute or re-compute BFS
        if self._has_gold:
            self._compute_escape_plan()
            if self._plan:
                action = self._plan.popleft()
                self._last_action = action
                return action
            # BFS returned None — safe path not yet known; fall through to exploration

        # 3d. If glitter is sensed → GRAB (and mark gold as held)
        if percept.glitter:
            self._has_gold = True
            action = Action.GRAB
            self._last_action = action
            return action

        # Step 4: Filtered random exploration
        action = self._rng.choice(_EXPLORATION_POOL)
        self._last_action = action
        return action

    def reset(self) -> None:
        """Reset all episode state for a new episode."""
        self._position = self._start_position
        self._direction = self._start_direction
        self._has_gold = False
        self._visited_safe = set()
        self._safe_graph = SafeGraph()
        self._last_action = None
        self._plan = collections.deque()
        self._plan_exhausted_once = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_position(self, percept: Percept) -> None:
        """
        Apply dead reckoning: update estimated position and direction based on
        the previous action and the current percept.

        This is called at the start of get_action() *before* the agent acts,
        so it reflects the outcome of the *last* chosen action.
        """
        if self._last_action is None:
            # First call — no previous action; agent is at the start position
            return

        if self._last_action == Action.FORWARD:
            if not percept.bump:
                # Successfully moved one step forward
                new_pos = self._direction.get_forward_position(self._position)
                self._position = new_pos
            # If bumped, position is unchanged

        elif self._last_action == Action.TURN_LEFT:
            self._direction = self._direction.turn_left()

        elif self._last_action == Action.TURN_RIGHT:
            self._direction = self._direction.turn_right()

        # SHOOT, GRAB, CLIMB — no change to position or direction

    def _mark_safe(self, pos: Position) -> None:
        """Register pos as a visited safe cell and update the safe graph."""
        if pos not in self._visited_safe:
            self._visited_safe.add(pos)
            self._safe_graph.add_safe_cell(pos)

    def _compute_escape_plan(self) -> None:
        """
        Run BFS to find the shortest action sequence from the current state
        to any orientation at the start position.

        Populates self._plan if a path is found; leaves it empty otherwise.
        """
        start_node = (self._position.x, self._position.y, self._direction)
        sx, sy = self._start_position.x, self._start_position.y

        def goal(node: tuple) -> bool:
            return node[0] == sx and node[1] == sy

        result = bfs_shortest_actions(self._safe_graph.get_graph(), start_node, goal)
        if result is not None:
            self._plan = collections.deque(result)

    # ------------------------------------------------------------------
    # Accessors (for testing / debugging)
    # ------------------------------------------------------------------

    @property
    def position(self) -> Position:
        """Current estimated position (0-based internal coordinates)."""
        return self._position

    @property
    def direction(self) -> Direction:
        """Current estimated facing direction."""
        return self._direction

    @property
    def has_gold(self) -> bool:
        """Whether the agent currently holds the gold."""
        return self._has_gold

    @property
    def visited_safe(self) -> set[Position]:
        """Read-only view of the visited safe cells set."""
        return set(self._visited_safe)

    @property
    def safe_graph(self) -> SafeGraph:
        """The agent's internal SafeGraph instance."""
        return self._safe_graph
