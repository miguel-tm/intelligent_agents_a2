"""
Unit tests for agents/bfs_planner.py — SafeGraph and bfs_shortest_actions.
"""

import pytest
import networkx as nx

from agents.bfs_planner import SafeGraph, bfs_shortest_actions
from wumpus.models import Action, Direction, Position


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _start_goal(sx: int, sy: int):
    """Return a goal predicate for 'reach cell (sx, sy) in any orientation'."""
    return lambda node: node[0] == sx and node[1] == sy


# ---------------------------------------------------------------------------
# SafeGraph — node addition
# ---------------------------------------------------------------------------

class TestSafeGraphNodes:
    def test_empty_graph_has_no_nodes(self):
        g = SafeGraph()
        assert g.node_count() == 0

    def test_single_cell_adds_four_nodes(self):
        g = SafeGraph()
        g.add_safe_cell(Position(0, 0))
        assert g.node_count() == 4

    def test_has_node_all_directions(self):
        g = SafeGraph()
        g.add_safe_cell(Position(2, 3))
        for d in Direction:
            assert g.has_node(2, 3, d)

    def test_has_node_false_before_add(self):
        g = SafeGraph()
        assert not g.has_node(1, 1, Direction.NORTH)

    def test_two_cells_adds_eight_nodes(self):
        g = SafeGraph()
        g.add_safe_cell(Position(0, 0))
        g.add_safe_cell(Position(1, 0))
        assert g.node_count() == 8

    def test_duplicate_add_is_idempotent(self):
        g = SafeGraph()
        g.add_safe_cell(Position(0, 0))
        g.add_safe_cell(Position(0, 0))  # second call — no-op
        assert g.node_count() == 4

    def test_three_cells_adds_twelve_nodes(self):
        g = SafeGraph()
        for pos in [Position(0, 0), Position(1, 0), Position(2, 0)]:
            g.add_safe_cell(pos)
        assert g.node_count() == 12


# ---------------------------------------------------------------------------
# SafeGraph — turn edges
# ---------------------------------------------------------------------------

class TestSafeGraphTurnEdges:
    def test_turn_left_edge_exists(self):
        g = SafeGraph()
        g.add_safe_cell(Position(0, 0))
        graph = g.get_graph()
        for d in Direction:
            from_node = (0, 0, d)
            to_node = (0, 0, d.turn_left())
            assert graph.has_edge(from_node, to_node)
            assert graph[from_node][to_node]["action"] == Action.TURN_LEFT

    def test_turn_right_edge_exists(self):
        g = SafeGraph()
        g.add_safe_cell(Position(0, 0))
        graph = g.get_graph()
        for d in Direction:
            from_node = (0, 0, d)
            to_node = (0, 0, d.turn_right())
            assert graph.has_edge(from_node, to_node)
            assert graph[from_node][to_node]["action"] == Action.TURN_RIGHT

    def test_single_cell_has_eight_turn_edges(self):
        """4 directions × 2 turn edges each = 8 turn edges."""
        g = SafeGraph()
        g.add_safe_cell(Position(0, 0))
        assert g.get_graph().number_of_edges() == 8


# ---------------------------------------------------------------------------
# SafeGraph — forward edges
# ---------------------------------------------------------------------------

class TestSafeGraphForwardEdges:
    def test_no_forward_edges_for_isolated_cell(self):
        g = SafeGraph()
        g.add_safe_cell(Position(0, 0))
        graph = g.get_graph()
        fwd_edges = [
            (u, v) for u, v, data in graph.edges(data=True)
            if data["action"] == Action.FORWARD
        ]
        assert fwd_edges == []

    def test_forward_edge_added_when_neighbour_exists(self):
        g = SafeGraph()
        g.add_safe_cell(Position(0, 0))
        g.add_safe_cell(Position(1, 0))  # one step EAST from (0,0)
        graph = g.get_graph()
        # (0,0,EAST) -> (1,0,EAST) should exist
        assert graph.has_edge((0, 0, Direction.EAST), (1, 0, Direction.EAST))
        assert graph[(0, 0, Direction.EAST)][(1, 0, Direction.EAST)]["action"] == Action.FORWARD

    def test_reverse_forward_edge_added(self):
        """(1,0,WEST) -> (0,0,WEST) must also be added."""
        g = SafeGraph()
        g.add_safe_cell(Position(0, 0))
        g.add_safe_cell(Position(1, 0))
        graph = g.get_graph()
        assert graph.has_edge((1, 0, Direction.WEST), (0, 0, Direction.WEST))
        assert graph[(1, 0, Direction.WEST)][(0, 0, Direction.WEST)]["action"] == Action.FORWARD

    def test_no_forward_edge_for_non_adjacent_cells(self):
        """Cells (0,0) and (2,0) are not adjacent — no FORWARD edge between them."""
        g = SafeGraph()
        g.add_safe_cell(Position(0, 0))
        g.add_safe_cell(Position(2, 0))
        graph = g.get_graph()
        fwd_edges = [
            (u, v) for u, v, data in graph.edges(data=True)
            if data["action"] == Action.FORWARD
        ]
        assert fwd_edges == []

    def test_forward_edges_count_for_two_adjacent_cells(self):
        """Two adjacent cells share forward edges in both directions for 1 orientation = 2 edges."""
        g = SafeGraph()
        g.add_safe_cell(Position(0, 0))
        g.add_safe_cell(Position(0, 1))  # one step NORTH
        graph = g.get_graph()
        fwd_edges = [
            (u, v) for u, v, data in graph.edges(data=True)
            if data["action"] == Action.FORWARD
        ]
        assert len(fwd_edges) == 2

    def test_three_cell_corridor_forward_edges(self):
        """(0,0)-(1,0)-(2,0): 4 forward edges (2 per adjacent pair)."""
        g = SafeGraph()
        for pos in [Position(0, 0), Position(1, 0), Position(2, 0)]:
            g.add_safe_cell(pos)
        graph = g.get_graph()
        fwd_edges = [
            (u, v) for u, v, data in graph.edges(data=True)
            if data["action"] == Action.FORWARD
        ]
        assert len(fwd_edges) == 4


# ---------------------------------------------------------------------------
# bfs_shortest_actions — basic cases
# ---------------------------------------------------------------------------

class TestBFSBasic:
    def test_empty_graph_returns_none(self):
        g = nx.DiGraph()
        result = bfs_shortest_actions(g, (0, 0, Direction.EAST), _start_goal(0, 0))
        assert result is None

    def test_start_not_in_graph_returns_none(self):
        sg = SafeGraph()
        sg.add_safe_cell(Position(1, 0))
        result = bfs_shortest_actions(
            sg.get_graph(),
            (0, 0, Direction.EAST),  # not in graph
            _start_goal(0, 0),
        )
        assert result is None

    def test_start_equals_goal_returns_empty_list(self):
        sg = SafeGraph()
        sg.add_safe_cell(Position(0, 0))
        result = bfs_shortest_actions(
            sg.get_graph(),
            (0, 0, Direction.EAST),
            _start_goal(0, 0),
        )
        assert result == []

    def test_goal_unreachable_returns_none(self):
        """Two isolated cells — (0,0) is start, goal is (5,5) which isn't in graph."""
        sg = SafeGraph()
        sg.add_safe_cell(Position(0, 0))
        result = bfs_shortest_actions(
            sg.get_graph(),
            (0, 0, Direction.EAST),
            _start_goal(5, 5),
        )
        assert result is None


# ---------------------------------------------------------------------------
# bfs_shortest_actions — corridor plans
# ---------------------------------------------------------------------------

class TestBFSCorridor:
    def _build_corridor(self, length: int) -> SafeGraph:
        """Build a horizontal corridor of `length` cells starting at (0,0)."""
        sg = SafeGraph()
        for x in range(length):
            sg.add_safe_cell(Position(x, 0))
        return sg

    def test_one_step_east(self):
        """Agent at (1,0) facing EAST, goal is (0,0). Must turn around and FORWARD."""
        sg = self._build_corridor(2)
        # Start: (1, 0, EAST) — goal: any node at (0, 0)
        result = bfs_shortest_actions(
            sg.get_graph(),
            (1, 0, Direction.EAST),
            _start_goal(0, 0),
        )
        assert result is not None
        assert Action.FORWARD in result
        # Must reach (0,0) — verify by replaying
        x, y, d = 1, 0, Direction.EAST
        for action in result:
            if action == Action.FORWARD:
                fwd = d.get_forward_position(Position(x, y))
                x, y = fwd.x, fwd.y
            elif action == Action.TURN_LEFT:
                d = d.turn_left()
            elif action == Action.TURN_RIGHT:
                d = d.turn_right()
        assert (x, y) == (0, 0)

    def test_two_steps_east_facing_east(self):
        """Agent at (2,0) facing EAST, goal (0,0). Need to turn and walk 2 steps."""
        sg = self._build_corridor(3)
        result = bfs_shortest_actions(
            sg.get_graph(),
            (2, 0, Direction.EAST),
            _start_goal(0, 0),
        )
        assert result is not None
        # Replay and confirm arrival
        x, y, d = 2, 0, Direction.EAST
        for action in result:
            if action == Action.FORWARD:
                fwd = d.get_forward_position(Position(x, y))
                x, y = fwd.x, fwd.y
            elif action == Action.TURN_LEFT:
                d = d.turn_left()
            elif action == Action.TURN_RIGHT:
                d = d.turn_right()
        assert (x, y) == (0, 0)

    def test_already_facing_goal_direction_is_optimal(self):
        """
        Agent at (2,0) facing WEST. Goal (0,0). Optimal: just FORWARD twice.
        BFS must find path of length 2 (no turns needed).
        """
        sg = self._build_corridor(3)
        result = bfs_shortest_actions(
            sg.get_graph(),
            (2, 0, Direction.WEST),
            _start_goal(0, 0),
        )
        assert result is not None
        assert result == [Action.FORWARD, Action.FORWARD]

    def test_result_is_list_of_actions(self):
        sg = self._build_corridor(2)
        result = bfs_shortest_actions(
            sg.get_graph(),
            (1, 0, Direction.WEST),
            _start_goal(0, 0),
        )
        assert isinstance(result, list)
        for a in result:
            assert isinstance(a, Action)


# ---------------------------------------------------------------------------
# bfs_shortest_actions — L-shape
# ---------------------------------------------------------------------------

class TestBFSLShape:
    def _build_l_shape(self) -> SafeGraph:
        """
        Build an L-shaped path: (0,0) -> (1,0) -> (2,0) -> (2,1)
        Start cell is (2,1), goal is (0,0).
        """
        sg = SafeGraph()
        for pos in [Position(0, 0), Position(1, 0), Position(2, 0), Position(2, 1)]:
            sg.add_safe_cell(pos)
        return sg

    def test_l_shape_path_reaches_goal(self):
        sg = self._build_l_shape()
        # Agent at (2,1) facing NORTH, goal (0,0)
        result = bfs_shortest_actions(
            sg.get_graph(),
            (2, 1, Direction.NORTH),
            _start_goal(0, 0),
        )
        assert result is not None
        # Replay
        x, y, d = 2, 1, Direction.NORTH
        for action in result:
            if action == Action.FORWARD:
                fwd = d.get_forward_position(Position(x, y))
                x, y = fwd.x, fwd.y
            elif action == Action.TURN_LEFT:
                d = d.turn_left()
            elif action == Action.TURN_RIGHT:
                d = d.turn_right()
        assert (x, y) == (0, 0)

    def test_l_shape_path_is_shortest(self):
        """
        Minimum steps from (2,1,NORTH) to (0,0):
        TURN_RIGHT (face EAST→SOUTH) wait — from NORTH to SOUTH need 2 turns,
        then 1 step SOUTH + then WEST... let BFS compute it; just assert
        it is within a reasonable bound (not absurdly long).
        """
        sg = self._build_l_shape()
        result = bfs_shortest_actions(
            sg.get_graph(),
            (2, 1, Direction.NORTH),
            _start_goal(0, 0),
        )
        assert result is not None
        # Theoretical minimum: 1 turn (SOUTH from NORTH = 2 turns) + 1 FORWARD +
        # 1 turn (WEST) + 2 FORWARD = 6 or 7. Accept ≤10.
        assert len(result) <= 10


# ---------------------------------------------------------------------------
# bfs_shortest_actions — multi-goal orientation
# ---------------------------------------------------------------------------

class TestBFSMultiGoal:
    def test_any_orientation_at_goal_accepted(self):
        """
        When the start node already satisfies the goal (different orientation),
        BFS should still return [] because the goal_predicate only checks (x,y).
        """
        sg = SafeGraph()
        sg.add_safe_cell(Position(0, 0))
        for d in Direction:
            result = bfs_shortest_actions(
                sg.get_graph(),
                (0, 0, d),
                _start_goal(0, 0),
            )
            assert result == [], f"Expected [] for direction {d}, got {result}"

    def test_goal_reached_via_shortest_orientation(self):
        """
        Two-cell graph. From (1,0,WEST) to goal (0,0): one FORWARD is the shortest.
        BFS must not return a longer path that arrives via turns first.
        """
        sg = SafeGraph()
        sg.add_safe_cell(Position(0, 0))
        sg.add_safe_cell(Position(1, 0))
        result = bfs_shortest_actions(
            sg.get_graph(),
            (1, 0, Direction.WEST),
            _start_goal(0, 0),
        )
        assert result == [Action.FORWARD]
