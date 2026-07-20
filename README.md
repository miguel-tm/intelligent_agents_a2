# Wumpus World Simulator - Assignment 2

**University of Toronto - Intelligent Agents Course**  
**Student:** Miguel Morales (@miguelmog10)

---

## Project Details

This project implements a **Wumpus World environment simulator** in Python using object-oriented design principles.

This is **Assignment 2**, extending the Assignment 1 foundation with a new **MovePlanningAgent** that tracks its own position, builds a safe-cell knowledge graph, and uses a custom BFS planner to escape with gold.

### Core Components
- **Configurable environment** with random pit, wumpus, and gold placement
- **Percept-based sensing** (stench, breeze, glitter, bump, scream, reward)
- **Action-based agent interface** enforcing separation of concerns
- **NaiveAgent baseline** for comparison
- **MovePlanningAgent** with dead-reckoning, safe graph (NetworkX), and BFS escape planner

---

## 📁 Repository Structure

```
intelligent_agents_a2/
│
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── main.py                        # CLI entry point (ASCII visualization)
├── streamlit_app.py               # Web entry point (advanced visualization)
│
├── docs/
│   ├── assignment1_requirements.md  # Assignment 1 specification (historical)
│   └── assignment2_requirements.md  # Assignment 2 specification
│
├── wumpus/                        # Core environment package
│   ├── __init__.py               # Package exports
│   ├── models.py                 # Data models (Direction, Action, Position, Percept, AgentState)
│   ├── environment.py            # WumpusWorld class managing hidden state
│   ├── visualization.py          # Visualizer for rendering game state
│   └── utils.py                  # Helper utilities
│
├── agents/                        # Agent package
│   ├── __init__.py               # Package exports
│   ├── base_agent.py             # Abstract Agent class (enforces percept-only interface)
│   ├── naive_agent.py            # NaiveAgent (random action selection, A1 baseline)
│   ├── move_planning_agent.py    # MovePlanningAgent (BFS escape planner, A2)
│   └── bfs_planner.py            # SafeGraph + bfs_shortest_actions (A2)
│
├── utils/                         # Shared utilities
│   ├── __init__.py               # Package exports
│   ├── episode_runner.py         # Shared episode loop (CLI + web)
│   └── streamlit_render.py       # HTML/CSS board rendering for the web UI
│
└── tests/                         # Test suite
    ├── test_models.py             # Tests for Direction, Action, Position, Percept, AgentState
    ├── test_environment.py        # Tests for WumpusWorld mechanics and actions
    ├── test_percepts.py           # Tests for percept generation and rewards
    ├── test_episode_runner.py     # Tests for run_episode() termination paths
    ├── test_actions.py            # Placeholder for action execution tests
    ├── test_bfs_planner.py        # Tests for SafeGraph and bfs_shortest_actions (A2)
    ├── test_move_planning_agent.py # Tests for MovePlanningAgent state/behaviour (A2)
    └── test_move_planning_integration.py  # Full-episode integration tests (A2)
```

### Module Responsibilities

| Module | Responsibility |
|--------|-----------------|
| **models.py** | Enums and dataclasses: `Direction`, `Action`, `Position`, `Percept`, `AgentState` |
| **environment.py** | `WumpusWorld` class—manages hidden state, executes actions, generates percepts |
| **visualization.py** | `Visualizer` class—renders game state (grid, agent, percepts) |
| **base_agent.py** | Abstract `Agent` class—interface ensuring agents only see percepts |
| **naive_agent.py** | `NaiveAgent` implementation—uniform random action selection (A1 baseline) |
| **move_planning_agent.py** | `MovePlanningAgent`—dead-reckoning, safe graph, BFS escape planner (A2) |
| **bfs_planner.py** | `SafeGraph` (NetworkX DiGraph) + `bfs_shortest_actions` (custom BFS) (A2) |
| **episode_runner.py** | `run_episode()`—shared game loop used by both the CLI and web UI |
| **streamlit_render.py** | HTML/CSS grid rendering helpers for the Streamlit UI |
| **main.py** | CLI entry point—agent selection (`--agent`), episode management, ASCII visualization |
| **streamlit_app.py** | Web entry point—interactive replay and statistics dashboard with agent selector |

---

## Design Philosophy

### Object-Oriented Design
- **Classes** model entities: `WumpusWorld`, `Agent`, `Percept`, `Position`, etc.
- **Enums** provide type-safe action and direction representations
- **Dataclasses** ensure immutability and clarity for data structures

### Separation of Concerns
- **Environment** (`WumpusWorld`) maintains hidden state exclusively
- **Agent** (`Agent` subclasses) operates only on percepts and internal beliefs
- **Agent cannot cheat** by accessing `WumpusWorld` directly
- **Visualizer** displays only known/observable information, not hidden state

### Extensibility
- Clean agent interface (`Agent` base class) allows easy addition of new agents
- No logic dependencies between environment and specific agents
- Structure supports adding belief tracking, planning, and learning in future assignments
- Test framework ready for validation of new agent behaviors

---

## How to Run

### Prerequisites
Ensure Python 3.8+ and dependencies are installed:
```bash
pip install -r requirements.txt
```

### Run with summary statistics only (default)
```bash
python main.py
```

This runs a standard game:
- 4×4 grid world
- Random wumpus and gold placement
- Pit probability of 0.2
- **MovePlanningAgent** making planned moves (default)
- Visualization (ASCII grid) suppressed, only episode summaries printed

### Run with the NaiveAgent baseline
```bash
python main.py --agent naive
```

### Run with per-turn visualization (grid display for each turn)
```bash
python main.py --verbose
python main.py --agent naive --verbose
```
- Visualization (ASCII grid) displayed for each turn

### Run the advanced web visualization (Streamlit)
The ASCII CLI above remains available for debugging and history. For a richer,
interactive experience, launch the Streamlit app:
```bash
streamlit run streamlit_app.py
```
Features:
- **Agent selector:** choose between `MovePlanningAgent` (default) and `NaiveAgent` from the sidebar.
- **Replay tab:** generate a single episode and step through it turn by turn
  (First / Prev / Next / Last, slider scrub) on a graphical emoji grid.
- **Statistics tab:** run many episodes and view aggregate metrics
  (escape/death/gold rates, average reward/steps) plus charts and a per-episode table.
- **Sidebar controls:** world size, pit probability, allow-climb, episode count,
  max turns, random seed, and a **Reveal hidden world** debug toggle that overlays
  the true wumpus/gold/pit locations.

> The web UI reuses the exact same `WumpusWorld`, agents, and `run_episode()`
> logic as the CLI, so both stay in sync. The "reveal hidden world" overlay is for
> debugging/teaching only—agents still receive information solely through percepts.

### Run Tests
```bash
pytest tests/
```

Run all unit tests with verbose output:
```bash
pytest tests/ -v
```

Run a specific test file:
```bash
pytest tests/test_environment.py -v
```

## Game Output

### Summary Mode (Default)
Prints one-line summary per episode:
```
Episode  1: Steps=  8 | Reward=     -8 | Gold=False | TIMEOUT
Episode  2: Steps= 21 | Reward=   -1063 | Gold=True  | DIED
Episode  3: Steps= 15 | Reward=    -15 | Gold=False | TIMEOUT
```

### Verbose Mode (`--verbose`)
Displays turn-by-turn grid and state:
```
  Turn 0 (initial state)

Turn 0 | Status: Alive | Position: Position(x=1, y=1)
+---------+
| . . . . |
| . . . . |
| . . . . |
| > . . . |
+---------+
Percepts: None
Reward: 0, Total Reward: 0
Inventory: Gold=False, Arrow=True

  Turn 0 --> Turn 1: Agent takes FORWARD

Turn 1 | Status: Alive | Position: Position(x=2, y=1)
+---------+
| . . . . |
| . . . . |
| . . . . |
| . > . . |
+---------+
Percepts: Breeze
Reward: -1, Total Reward: -1
Inventory: Gold=False, Arrow=True
```

### Aggregate Statistics
After all episodes:
```
Total Episodes: 5
Successful Escapes: 1/5 (20.0%)
Deaths: 2/5 (40.0%)
Gold Collected: 2/5 (40.0%)
Total Reward: -547
Average Reward per Episode: -109.4
Average Steps per Episode: 12.2
```

---
- **Grid:** 4×4
- **Start position:** [1,1] facing right (EAST)
- **Pit probability:** 0.2 per non-start cell
- **Allow climb without gold:** True
- **Wumpus, gold, pits:** Placed randomly, may overlap

### Agent Actions
| Action | Effect |
|--------|--------|
| **FORWARD** | Move one step in facing direction (blocked by walls) |
| **TURN_LEFT** | Rotate 90° counter-clockwise |
| **TURN_RIGHT** | Rotate 90° clockwise |
| **SHOOT** | Fire arrow in facing direction (kills wumpus) |
| **GRAB** | Pick up gold at current location |
| **CLIMB** | Exit environment (only at [1,1]) |

### Agent Percepts
| Percept | Triggered By |
|---------|--------------|
| **Stench** | Wumpus in adjacent cell |
| **Breeze** | Pit in adjacent cell |
| **Glitter** | Gold at current location |
| **Bump** | Attempted move outside grid |
| **Scream** | Wumpus killed by arrow |
| **Reward** | Immediate reward/penalty for action |

### Episode Termination
Episodes end when:
- **Agent climbs out at [1,1] with gold:** `ESCAPED (success!)` — +1000 reward
- **Agent climbs out at [1,1] without gold:** `ESCAPED (no gold)` — -1 reward (time cost only)
- **Agent falls in pit:** `DIED` — -1000 penalty
- **Agent meets wumpus:** `DIED` — -1000 penalty
- **Agent shoots wumpus:** Wumpus eliminated, episode continues
- **Max turns exceeded:** `TIMEOUT` (configurable, default 1000)

### Rewards (Per Assignment Specification)
- `-1` per action (time penalty)
- `-1` for grabbing gold (no bonus, only time cost)
- `-11` for shooting arrow (-1 time cost + -10 arrow penalty)
- `-1` for climbing without gold (when allowed)
- `-1000` for death (pit or wumpus)
- `+1000` for escaping with gold at [1,1]
- `0` for climbing without gold at [1,1] when not allowed (no effect)

---

## 📋 Implementation Status

### ✅ Assignment 2 Complete
- [x] **move_planning_agent.py:** Dead-reckoning, filtered action pool, GRAB/CLIMB overrides, BFS escape execution ✅
- [x] **bfs_planner.py:** `SafeGraph` (NetworkX DiGraph, 4 nodes per cell, turn + forward edges) + custom `bfs_shortest_actions` ✅
- [x] **main.py:** `--agent {move_planning,naive}` flag, `MovePlanningAgent` default ✅
- [x] **streamlit_app.py:** Agent sidebar dropdown, `MovePlanningAgent` default ✅
- [x] **docs/assignment2_requirements.md:** Full A2 specification ✅
- [x] **tests/test_bfs_planner.py:** 28 tests for `SafeGraph` and `bfs_shortest_actions` ✅
- [x] **tests/test_move_planning_agent.py:** 33 unit tests for agent state and behaviour ✅
- [x] **tests/test_move_planning_integration.py:** 16 full-episode integration tests ✅

**Total: 176/176 tests passing**

### ✅ Assignment 1 Complete (foundation)
- [x] **models.py:** Direction turn logic, Position validation ✅
- [x] **environment.py:** World initialization, action execution, percept generation ✅
- [x] **naive_agent.py:** Random action selection ✅
- [x] **visualization.py:** Grid rendering with ASCII art ✅
- [x] **episode_runner.py:** Shared game loop (CLI + web) ✅
- [x] **main.py:** Game loop, episode management, visualization integration ✅
- [x] **streamlit_app.py:** Interactive web visualization — Replay + Statistics tabs ✅
- [x] **streamlit_render.py:** HTML/CSS emoji board renderer ✅

---

## Testing Strategy

All tests follow this pattern:
1. **Setup:** Create environment and agent
2. **Execute:** Run actions or scenarios
3. **Verify:** Assert expected state changes and percepts

**Test Coverage:** 176 comprehensive tests covering:
- **test_models.py** (55 tests): Direction logic, Position validation, Action enum, Percept structure
- **test_environment.py** (22 tests): Environment initialization, movement, percept generation, episode termination
- **test_percepts.py** (9 tests): Sensing accuracy, reward computation
- **test_episode_runner.py** (13 tests): `run_episode()` termination paths
- **test_actions.py** (0 tests): Placeholder
- **test_bfs_planner.py** (28 tests): `SafeGraph` node/edge structure, corridor/L-shape BFS paths, multi-goal BFS
- **test_move_planning_agent.py** (33 tests): Action pool constraints, glitter→GRAB, dead reckoning, visited cells, graph nodes, CLIMB safety, reset
- **test_move_planning_integration.py** (16 tests): Action legality invariants, escape-with-gold rate, state consistency, comparative performance vs NaiveAgent

**Run tests:** `pytest tests/ -v` or `pytest tests/ -q`

---

## Key Files to Review

**Start here:**
- [wumpus/models.py](wumpus/models.py) — Data structure definitions
- [wumpus/environment.py](wumpus/environment.py) — Core environment logic
- [agents/base_agent.py](agents/base_agent.py) — Agent interface

**Assignment 2 (new):**
- [agents/move_planning_agent.py](agents/move_planning_agent.py) — MovePlanningAgent implementation
- [agents/bfs_planner.py](agents/bfs_planner.py) — SafeGraph + BFS planner

**Reference:**
- [agents/naive_agent.py](agents/naive_agent.py) — Baseline agent (A1)
- [main.py](main.py) — CLI entry point with `--agent` flag
- [docs/assignment2_requirements.md](docs/assignment2_requirements.md) — A2 specification
- [docs/assignment1_requirements.md](docs/assignment1_requirements.md) — A1 specification (historical)

---

##  Author
**Miguel Morales** (@miguelmog10)  
University of Toronto - Intelligent Agents Course
