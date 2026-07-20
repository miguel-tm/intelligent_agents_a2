"""
BFS-based planner and safe-cell graph for the MovePlanningAgent.

This module provides:
- SafeGraph: A NetworkX DiGraph wrapper representing the agent's knowledge
  of safe navigable states in the Wumpus World.
- bfs_shortest_actions: A custom BFS that finds the shortest action sequence
  from a start node to any node matching a goal predicate.

Graph nodes are 3-tuples: (x: int, y: int, direction: Direction)
Each edge carries an 'action' attribute of type Action.

This module has no dependency on WumpusWorld and is independently unit-testable.
"""

from __future__ import annotations

import collections
from typing import Callable

import networkx as nx

from wumpus.models import Action, Direction, Position


# Mapping from each Direction to the Direction directly opposite (for reverse FORWARD edges)
_OPPOSITE: dict[Direction, Direction] = {
    Direction.NORTH: Direction.SOUTH,
    Direction.SOUTH: Direction.NORTH,
    Direction.EAST: Direction.WEST,
    Direction.WEST: Direction.EAST,
}


def _node(x: int, y: int, direction: Direction) -> tuple[int, int, Direction]:
    """Build a graph node tuple from coordinates and direction."""
    return (x, y, direction)


class SafeGraph:
    """
    NetworkX DiGraph representing the agent's knowledge of safe navigable states.

    Nodes: (x, y, direction) — one node per cell per orientation.
    Edges: directed, each carrying action=Action.<TURN_LEFT|TURN_RIGHT|FORWARD>.

    The graph is built incrementally as the agent discovers new safe cells.
    It reflects the agent's beliefs, not the true world state.
    """

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_safe_cell(self, pos: Position) -> None:
        """
        Register a cell as safe and update the graph.

        For a new cell this:
        1. Adds the four orientation nodes for (pos.x, pos.y).
        2. Adds all eight intra-cell turn edges (TURN_LEFT and TURN_RIGHT for
           each orientation).
        3. For each of the four cardinal directions, if the neighbouring cell
           in that direction is already in the graph, adds bidirectional
           FORWARD edges between the two cells at that orientation.

        Calling this method on an already-known cell is a no-op.
        """
        x, y = pos.x, pos.y

        # Already registered — nothing to do
        if self._graph.has_node(_node(x, y, Direction.NORTH)):
            return

        # Step 1 & 2: add nodes and intra-cell turn edges
        for direction in Direction:
            node = _node(x, y, direction)
            self._graph.add_node(node)
            left_node = _node(x, y, direction.turn_left())
            right_node = _node(x, y, direction.turn_right())
            self._graph.add_edge(node, left_node, action=Action.TURN_LEFT)
            self._graph.add_edge(node, right_node, action=Action.TURN_RIGHT)

        # Step 3: inter-cell FORWARD edges to/from already-known neighbours
        for direction in Direction:
            neighbour = direction.get_forward_position(pos)
            nx_, ny = neighbour.x, neighbour.y

            # Check if the neighbour cell is already in the graph
            if not self._graph.has_node(_node(nx_, ny, Direction.NORTH)):
                continue

            # Add FORWARD edge from current cell (facing 'direction') to neighbour
            from_node = _node(x, y, direction)
            to_node = _node(nx_, ny, direction)
            if not self._graph.has_edge(from_node, to_node):
                self._graph.add_edge(from_node, to_node, action=Action.FORWARD)

            # Add FORWARD edge from neighbour (facing opposite, toward current cell)
            rev = _OPPOSITE[direction]
            from_rev = _node(nx_, ny, rev)
            to_rev = _node(x, y, rev)
            if not self._graph.has_edge(from_rev, to_rev):
                self._graph.add_edge(from_rev, to_rev, action=Action.FORWARD)

    def has_node(self, x: int, y: int, direction: Direction) -> bool:
        """Return True if the given state (x, y, direction) is in the graph."""
        return self._graph.has_node(_node(x, y, direction))

    def node_count(self) -> int:
        """Return the total number of nodes in the graph."""
        return self._graph.number_of_nodes()

    def get_graph(self) -> nx.DiGraph:
        """Return the underlying NetworkX DiGraph (for tests and introspection)."""
        return self._graph


# --------------------------------------------------------------------------- #
# BFS planner
# --------------------------------------------------------------------------- #

def bfs_shortest_actions(
    graph: nx.DiGraph,
    start_node: tuple[int, int, Direction],
    goal_predicate: Callable[[tuple[int, int, Direction]], bool],
) -> list[Action] | None:
    """
    Find the shortest action sequence from start_node to any node matching
    goal_predicate using a custom Breadth-First Search.

    This function does NOT use NetworkX path algorithms; it traverses the graph
    manually with a deque, following directed edges.

    Args:
        graph: The SafeGraph's underlying DiGraph (or any DiGraph with 'action'
               edge attributes).
        start_node: The BFS origin — (x, y, direction) tuple.
        goal_predicate: A callable that returns True for any acceptable goal node.

    Returns:
        A list of Actions representing the shortest path (possibly empty if
        start_node already satisfies the goal).
        Returns None if no path to a goal node exists.
    """
    if start_node not in graph:
        return None

    if goal_predicate(start_node):
        return []

    # Back-pointer dict: node -> (parent_node, action_taken_to_reach_node)
    came_from: dict[tuple, tuple | None] = {start_node: None}
    queue: collections.deque[tuple] = collections.deque([start_node])

    while queue:
        current = queue.popleft()

        for neighbour, edge_data in graph[current].items():
            if neighbour in came_from:
                continue  # already visited

            came_from[neighbour] = (current, edge_data["action"])
            queue.append(neighbour)

            if goal_predicate(neighbour):
                # Reconstruct the action sequence
                actions: list[Action] = []
                node = neighbour
                while came_from[node] is not None:
                    parent, action = came_from[node]
                    actions.append(action)
                    node = parent
                actions.reverse()
                return actions

    # Goal not reachable
    return None
