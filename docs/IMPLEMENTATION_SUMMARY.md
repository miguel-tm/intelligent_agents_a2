# Wumpus World — Implementation Summary

**Status:** ✅ Assignment 1 COMPLETE (99/99 tests) | ✅ Assignment 2 COMPLETE (176/176 tests)

---

## Assignment 2 — MovePlanningAgent

### New Modules

| Module | Responsibility |
|--------|----------------|
| `agents/move_planning_agent.py` | `MovePlanningAgent` — stateful BFS-planning agent |
| `agents/bfs_planner.py` | `SafeGraph` (NetworkX DiGraph wrapper) + `bfs_shortest_actions` (custom BFS) |
| `docs/assignment2_requirements.md` | Assignment 2 specification |
| `tests/test_bfs_planner.py` | 28 unit tests for `SafeGraph` and `bfs_shortest_actions` |
| `tests/test_move_planning_agent.py` | 33 unit tests for `MovePlanningAgent` state/behaviour |
| `tests/test_move_planning_integration.py` | 16 integration tests (full episodes, legality, escape rate) |

### MovePlanningAgent Architecture

**Internal state:**

| Field | Type | Description |
|-------|------|-------------|
| `_position` | `Position` | Dead-reckoned current position (0-based) |
| `_direction` | `Direction` | Dead-reckoned facing direction |
| `_has_gold` | `bool` | Whether gold has been picked up |
| `_has_arrow` | `bool` | Whether the arrow is still available to fire |
| `_visited_safe` | `set[Position]` | All cells successfully entered |
| `_safe_graph` | `SafeGraph` | NetworkX DiGraph of safe navigable states |
| `_last_action` | `Action \| None` | Previous action (needed for dead reckoning) |
| `_plan` | `deque[Action]` | Queued BFS escape actions |

**`get_action()` priority order:**
1. Has gold + at start → `CLIMB`
2. Has gold + plan queued → pop next planned action
3. Has gold + plan empty → run BFS; pop first action (or continue exploring if unreachable)
4. Glitter sensed → `GRAB` (sets `_has_gold = True`)
5. Otherwise → random choice from `[FORWARD, TURN_LEFT, TURN_RIGHT, SHOOT]` while arrow is available, or `[FORWARD, TURN_LEFT, TURN_RIGHT]` once the arrow has been fired

**Dead reckoning:**
- `FORWARD` + no bump → advance `_position` one step in `_direction`
- `FORWARD` + bump → `_position` unchanged
- `TURN_LEFT/TURN_RIGHT` → update `_direction`
- Other actions → no change

**Safe Graph (NetworkX DiGraph):**
- Nodes: `(x, y, Direction)` — 4 nodes per visited cell
- Turn edges: `TURN_LEFT`, `TURN_RIGHT` intra-cell (8 per cell)
- Forward edges: `FORWARD` bidirectional between adjacent safe cells (2 per adjacent pair)
- Incremental update: forward edges to already-known neighbours added when a new cell is registered

**BFS Planner (`bfs_shortest_actions`):**
- Custom BFS using `collections.deque` (no NetworkX path algorithms)
- Returns `list[Action]` — empty if already at goal, `None` if unreachable
- Goal: any `(x, y, Direction)` node where `(x, y) == start_position`
- Accepts a predicate so multi-goal search is a first-class concern

### Entry Point Changes

**`main.py`:** add `--agent {move_planning,naive}` CLI flag, default `move_planning`
```bash
python main.py                          # MovePlanningAgent (default)
python main.py --agent naive            # NaiveAgent baseline
python main.py --agent move_planning --verbose
```

**`streamlit_app.py`:** sidebar "Agent" dropdown (`move_planning` default, `naive` option)

### Test Coverage (77 New Tests)

- `test_bfs_planner.py` (28): node/edge structure, corridor/L-shape BFS paths, multi-goal
- `test_move_planning_agent.py` (33): pool constraints, glitter→GRAB, dead reckoning, visited cells, graph node count, CLIMB safety, reset
- `test_move_planning_integration.py` (16): action legality, escape-with-gold rate, state consistency, performance vs NaiveAgent

### Design Decisions

1. **Safe cell = any visited cell.** No probabilistic stench/breeze inference. Keeps the graph construction simple and semantically precise.
2. **Separate `bfs_planner.py` module.** BFS and `SafeGraph` are independently unit-testable without instantiating an agent.
3. **`has_gold` set at decision time.** When `percept.glitter` causes the agent to choose `GRAB`, `_has_gold` is set immediately in the same call — no need to wait for the next percept.
4. **Re-plan on every turn while has_gold and plan is empty.** Handles the (rare) case where BFS returns `None` initially — retried each turn as more safe cells are discovered.
5. **Optional injected `random.Random`.** Agent accepts an `rng` kwarg so tests are reproducible without disturbing world RNG.
6. **No changes to `WumpusWorld` or `episode_runner.py`.** The agent works purely from percepts; the environment and game loop are untouched.

---

## Assignment 1 — Foundation Implementation

**Status:** ✅ COMPLETE - 99/99 tests passing

## Quick Reference

### Project Structure
```
wumpus/
  ├── models.py          (Direction, Action, Position, Percept, AgentState)
  ├── environment.py     (WumpusWorld - main environment)
  ├── visualization.py   (Visualizer - ASCII grid display)
  └── __init__.py

agents/
  ├── base_agent.py      (Abstract Agent interface)
  ├── naive_agent.py     (Random baseline agent)
  └── __init__.py

utils/
  ├── episode_runner.py  (Shared game loop - CLI + web)
  ├── streamlit_render.py(HTML/CSS board rendering helpers)
  └── __init__.py

main.py              (CLI entry point: python main.py / --verbose)
streamlit_app.py     (Web UI entry point: streamlit run streamlit_app.py)
pytest.ini           (Test configuration)
```

### Critical Coordinates
- **User Coords:** [1,1] to [4,4], origin bottom-left (mathematical)
- **Internal Coords:** [0,0] to [3,3], origin bottom-left (array indexing)
- **Conversion:** user = internal + 1

### Reward System (Verified)
- `-1` per action (time cost)
- `-11` for shooting arrow (-1 time + -10 arrow)
- `-1` for grabbing gold (NO bonus!)
- `-1` for climbing without gold when allowed → episode ends (ESCAPED no gold)
- `0` for climbing without gold when NOT allowed → no effect, episode continues
- `-1000` for death (pit or wumpus) → episode ends
- `+1000` for escaping with gold at [1,1] → episode ends

### Actions (6 Total)
- `FORWARD` - Move in facing direction
- `TURN_LEFT` - Rotate 90° counter-clockwise: (value-1)%4
- `TURN_RIGHT` - Rotate 90° clockwise: (value+1)%4
- `SHOOT` - Fire arrow (kills wumpus if hit)
- `GRAB` - Pick up gold at current location
- `CLIMB` - Exit at [1,1]

### Direction Enum Pattern
```python
class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def turn_left(self): return Direction((self.value - 1) % 4)
    def turn_right(self): return Direction((self.value + 1) % 4)
    def get_forward_position(self, pos): ...  # returns new Position
```

## Key Implementation Details

### WumpusWorld.step() Execution
1. Parse action
2. Update agent state (move, turn, grab, etc.)
3. Check death condition (pit or wumpus at position)
4. Generate percept at current position
5. Compute reward
6. Return (percept, episode_ended)

### Percept Generation
- **Stench:** Wumpus in adjacent cell (Manhattan distance = 1)
- **Breeze:** Pit in adjacent cell
- **Glitter:** Gold at current location
- **Bump:** Hit wall (move rejected)
- **Scream:** Wumpus killed by arrow

### Episode Termination (4 outcomes)
- `reward == 1000` → **ESCAPED (success!)** — agent climbed out with gold ✓
- `ended == True, reward == -1` → **ESCAPED (no gold)** — agent climbed out without gold
- `reward == -1000` → **DIED** — pit or wumpus ✗
- `turns >= max_turns` → **TIMEOUT**

> ⚠️ Bug fixed: climb-without-gold previously reported as TIMEOUT. Now correctly
> reports ESCAPED (no gold). Covered by `test_episode_runner.py`.

### ⚠️ WumpusWorld.__init__ calls _initialize_world()
The constructor immediately generates a random world. This means:
- Creating `WumpusWorld(...)` consumes random state
- `run_episode()` calls `env.reset()` → `_initialize_world()` again (second init)
- For deterministic tests: seed → `WumpusWorld(...)` → `env.reset()` must all be
  simulated together when finding reproducible seeds (see `test_episode_runner.py`)

### Test Coverage (99 Total)
- **test_models.py:** 55 tests (Direction, Action, Position, Percept, AgentState)
- **test_environment.py:** 22 tests (Movement, percepts, actions, termination)
- **test_percepts.py:** 9 tests (Sensing accuracy, reward values)
- **test_episode_runner.py:** 13 tests (climb-without-gold, death, escape-with-gold)

### NaiveAgent
```python
def get_action(self, percept: Percept) -> Action:
    return random.choice(list(Action))  # Uniform distribution
```

### run_episode() Signature
```python
run_episode(
    agent,
    environment: WumpusWorld,
    visualizer=None,
    max_turns=1000,
    verbose=False,
    record_history=False,  # True → adds "history" + "world_layout" to returned dict
) -> dict  # keys: total_reward, turns_taken, gold_collected, escaped, died
```

### Visualization Output Format (ASCII CLI)
```
Turn N | Status: [Alive|Dead (killed by X)] | Position: Position(x=Y, z=Z)
Grid display with direction symbols (>, <, ^, v)
Percepts: [Stench | Breeze | Glitter | Bump | Scream] or None
Reward: -1, Total Reward: -5
Inventory: Gold=False, Arrow=True
```

### Streamlit Web UI Features
- **Replay tab:** generate episode → step through turns (First/Prev/Next/Last + slider)
- **Statistics tab:** run N episodes → escape/death/gold rates, avg reward/steps, charts
- **Sidebar:** world size, pit prob, allow-climb, episodes, max turns, seed, auto-play speed
- **Reveal hidden world toggle:** overlays true wumpus/gold/pit positions (debug/teaching)

## Design Patterns

1. **Immutability:** Dataclasses frozen=True, Enum for type-safe actions/directions
2. **Separation:** Agent sees ONLY percepts, never accesses WumpusWorld directly
3. **Type Hints:** 100% coverage throughout
4. **Private Methods:** `_` prefix for internal implementation details
5. **Single Source of Truth:** `run_episode()` shared by CLI and web UI
6. **Test-Driven:** 99 tests verify all critical paths including termination edge cases

