# Assignment 2 Requirements — Wumpus World: Move Planning Agent

**University of Toronto — Intelligent Agents Course**

---

## Objective

Extend the Assignment 1 Wumpus World simulator with a new **MovePlanningAgent** that:

- Tracks its own internal state (position, direction, gold status, visited safe cells).
- Builds a knowledge graph of safe navigable states using **NetworkX**.
- Plans shortest-path escape routes using a **custom BFS** implementation.
- Executes a rational grab-and-escape sequence when gold is sensed.

---

## Retained Architecture Constraints (from Assignment 1)

- Agents inherit from the abstract `Agent` base class.
- The environment (`WumpusWorld`) and agent are intentionally separated.
- Agents **only receive `Percept` objects**; they cannot inspect `WumpusWorld` state directly.
- The game loop remains in `episode_runner.py` and is shared by the CLI and web UI.
- The `NaiveAgent` is preserved as a baseline comparison agent.

---

## Coordinate System

Unchanged from Assignment 1:

- **Internal (agent) coordinates:** `Position(0, 0)` = bottom-left corner (start cell), `x` increases right, `y` increases up.
- The agent must use **0-based internal coordinates** for all position estimates and graph nodes.
- **User/display coordinates:** offset by +1 from internal; used only in the visualizer and Streamlit UI.

---

## Functional Requirements

### 1. New Agent — `MovePlanningAgent`

Create `agents/move_planning_agent.py` implementing the `Agent` interface.

#### 1.1 Improved Exploration

- **Remove `GRAB` and `CLIMB` from the random action pool.**
- The random exploration pool is: `[FORWARD, TURN_LEFT, TURN_RIGHT, SHOOT]`.
- `GRAB` is only emitted when `percept.glitter` is `True`.
- `CLIMB` is only emitted when the agent is at the start position **and** has the gold.

#### 1.2 Internal Agent State

The agent must maintain:

| Field | Type | Description |
|-------|------|-------------|
| `_position` | `Position` | Agent's estimated current position (0-based) |
| `_direction` | `Direction` | Agent's estimated current facing direction |
| `_has_gold` | `bool` | Whether the agent has picked up the gold |
| `_visited_safe` | `set[Position]` | All cells the agent has successfully entered |
| `_safe_graph` | `SafeGraph` | NetworkX-backed graph of safe navigable states |
| `_last_action` | `Action \| None` | Most recent action chosen (for dead reckoning) |
| `_plan` | `deque[Action]` | Queued escape actions |

#### 1.3 Position Tracking (Dead Reckoning)

The environment **does not expose** agent position. The agent must infer it:

- `FORWARD` + `percept.bump == False` → advance `_position` one step in `_direction`.
- `FORWARD` + `percept.bump == True` → `_position` unchanged (hit wall).
- `TURN_LEFT` → `_direction = _direction.turn_left()`.
- `TURN_RIGHT` → `_direction = _direction.turn_right()`.
- `SHOOT`, `GRAB`, `CLIMB` → no change to `_position` or `_direction`.
- First call (`_last_action is None`) → skip dead reckoning.

#### 1.4 Safe Cell Definition

A cell is **safe** if the agent successfully entered it (survived after moving into it). No probabilistic inference from stench or breeze is required. The start cell is always added to the safe set on the first call.

---

### 2. Safe Graph

#### 2.1 Library

Use **NetworkX** (`networkx>=3.0`) for graph storage. The graph is a `networkx.DiGraph`.

#### 2.2 Node Schema

Graph nodes are 3-tuples: `(x, y, direction)` where:

- `x`, `y` are `int` values (0-based internal coordinates).
- `direction` is a `Direction` enum value.

Each visited safe cell contributes **four orientation nodes**: one per `Direction` value.

Example — cell `(1, 0)` produces nodes:
```
(1, 0, Direction.NORTH)
(1, 0, Direction.EAST)
(1, 0, Direction.SOUTH)
(1, 0, Direction.WEST)
```

#### 2.3 Edges

Every edge carries an `action` attribute of type `Action`.

**Intra-cell turn edges** (added when the cell is first added to the graph):

| From | To | Action |
|------|----|--------|
| `(x, y, d)` | `(x, y, d.turn_left())` | `TURN_LEFT` |
| `(x, y, d)` | `(x, y, d.turn_right())` | `TURN_RIGHT` |

**Inter-cell move edges** (added when a new safe cell is discovered and its neighbor is already in the graph):

| From | To | Action |
|------|----|--------|
| `(x, y, d)` | `(nx, ny, d)` | `FORWARD` |
| `(nx, ny, d)` | `(x, y, reverse_d)` | `FORWARD` |

Where `(nx, ny)` is the cell one step in direction `d` from `(x, y)`, and `reverse_d` is the opposite direction.

> Forward edges between two safe cells are added **bidirectionally** when the second of the two is first added to the graph.

#### 2.4 `SafeGraph` API

```python
class SafeGraph:
    def add_safe_cell(self, pos: Position) -> None: ...
    def has_node(self, x: int, y: int, direction: Direction) -> bool: ...
    def node_count(self) -> int: ...
    def get_graph(self) -> nx.DiGraph: ...  # for tests / introspection
```

---

### 3. Planner

#### 3.1 Location

`agents/bfs_planner.py` — a standalone module importable independently of any agent.

#### 3.2 Custom BFS

Use a **custom Breadth-First Search** implementation using `collections.deque`. Do **not** use `networkx.shortest_path`, `networkx.astar_path`, or similar NetworkX path algorithms.

```python
def bfs_shortest_actions(
    graph: nx.DiGraph,
    start_node: tuple,
    goal_predicate: Callable[[tuple], bool],
) -> list[Action] | None:
    ...
```

- Returns a `list[Action]` (possibly empty if already at goal).
- Returns `None` if the goal is unreachable.
- Uses a back-pointer dict `{node: (parent_node, action)}` to reconstruct the path.

#### 3.3 Goal Condition

The BFS goal for escape is: any node `(x, y, direction)` where `(x, y) == start_position`. Orientation at the start does not matter.

---

### 4. Escape Behavior

When `percept.glitter` is sensed:

1. **Return `GRAB`** (sets `_has_gold = True` internally).
2. On the next call, `_has_gold` is `True` and `_plan` is empty:
   - Call `bfs_shortest_actions` from the current state `(x, y, direction)` to any start-position goal.
   - Queue the resulting actions into `_plan`.
3. **Execute the plan** action-by-action on subsequent turns.
4. When the plan is exhausted and the agent is at the start: **return `CLIMB`**.

If BFS returns `None` (safe path to start not yet known), continue random exploration until more cells are discovered, then re-attempt BFS.

---

## Non-Functional Requirements

- Python 3.10+
- Object-oriented design; `MovePlanningAgent` must inherit from `Agent`.
- No access to `WumpusWorld` state from within the agent.
- `SafeGraph` and `bfs_shortest_actions` must be independently unit-testable.
- All existing Assignment 1 tests (99 tests) must remain passing.
- The `NaiveAgent` must still be usable (importable, runnable, selectable in entry points).

---

## Entry Point Changes

### CLI (`main.py`)

Add `--agent {move_planning,naive}` flag. Default: `move_planning`.

```bash
python main.py                         # MovePlanningAgent, 5 episodes
python main.py --agent naive           # NaiveAgent baseline
python main.py --agent move_planning --verbose
```

### Web UI (`streamlit_app.py`)

Add an "Agent" sidebar dropdown with options `move_planning` (default) and `naive`. Both replay and statistics tabs respect the selection.

---

## Out of Scope for Assignment 2

- Probabilistic hazard inference (wumpus/pit location estimation from stench/breeze).
- Optimal arrow usage strategy.
- Learning algorithms.
- Changes to `WumpusWorld` environment behavior.
- Changes to `episode_runner.py` game loop.
