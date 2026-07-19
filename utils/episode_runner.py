"""Episode runner utility for Wumpus World simulator.

Shared logic for running a single episode of the Wumpus World game.
Used by both CLI (main.py) and web UI (streamlit_app.py) visualizations.
"""

from wumpus import WumpusWorld, Visualizer
from wumpus.models import Action, Percept, AgentState, Position


def _percept_to_dict(percept: Percept) -> dict:
    """Convert a Percept into a plain dict (for history snapshots / serialization)."""
    return {
        "stench": percept.stench,
        "breeze": percept.breeze,
        "glitter": percept.glitter,
        "bump": percept.bump,
        "scream": percept.scream,
        "reward": percept.reward,
    }


def _make_snapshot(
    turn: int,
    action_name: str | None,
    user_position: tuple[int, int],
    direction_name: str,
    percept: Percept,
    total_reward: float,
    alive: bool,
    death_cause: str | None,
    has_gold: bool,
    has_arrow: bool,
) -> dict:
    """Build a single per-turn snapshot dict for the episode history."""
    return {
        "turn": turn,
        "action": action_name,
        "position": user_position,  # user coordinates [1,1]..[width,height]
        "direction": direction_name,
        "percept": _percept_to_dict(percept),
        "reward": percept.reward,
        "total_reward": total_reward,
        "alive": alive,
        "death_cause": death_cause,
        "has_gold": has_gold,
        "has_arrow": has_arrow,
    }


def _capture_world_layout(environment: WumpusWorld) -> dict:
    """Capture the true (hidden) world layout in user coordinates.

    For visualization/debugging overlays only; agents never receive this.
    """
    wumpus = environment.get_wumpus_position()
    gold = environment.get_gold_position()
    pits = environment.get_pit_positions()
    return {
        "width": environment.width,
        "height": environment.height,
        "wumpus": (wumpus.x + 1, wumpus.y + 1) if wumpus is not None else None,
        "gold": (gold.x + 1, gold.y + 1) if gold is not None else None,
        "pits": sorted((p.x + 1, p.y + 1) for p in pits),
    }


def run_episode(
    agent,
    environment: WumpusWorld,
    visualizer: Visualizer | None = None,
    max_turns: int = 1000,
    verbose: bool = True,
    record_history: bool = False,
) -> dict:
    """
    Run a single episode of the Wumpus World game.
    
    This function handles the core game loop: agent decision, environment
    execution, state tracking, and optional visualization. It's designed to be
    reusable by both CLI and web UI implementations.
    
    Args:
        agent: The agent to control (must implement Agent interface)
        environment: The WumpusWorld environment
        visualizer: Optional Visualizer for rendering (None = no visualization)
        max_turns: Maximum number of turns before forcing episode end
        verbose: If True, print turn information and enable visualization
        record_history: If True, capture a per-turn snapshot trace and the true
            world layout for later replay (e.g., the Streamlit web UI). Adds
            "history" and "world_layout" keys to the returned dict. Defaults to
            False so existing CLI behavior is unchanged.
        
    Returns:
        Dictionary with episode statistics:
        - total_reward: Cumulative reward across all turns
        - turns_taken: Number of turns executed
        - gold_collected: Whether agent found and grabbed gold
        - escaped: Whether agent escaped (with or without gold)
        - died: Whether agent died (pit or wumpus)
        When record_history is True, also includes:
        - history: List of per-turn snapshot dicts (turn 0 = initial state)
        - world_layout: Hidden world layout in user coordinates (debug/overlay)
        
    Episode Termination Conditions:
        - Reward == 1000: Escaped with gold at [1,1]
        - Reward == -1000: Died (pit or wumpus)
        - turns >= max_turns: Timeout
    """
    # Initialize episode
    environment.reset()
    agent.reset()
    percept = Percept()  # Initial empty percept
    
    # Episode tracking
    total_reward = 0
    turns = 0
    gold_collected = False
    escaped = False
    died = False
    has_arrow = True  # Agent starts with arrow

    # Optional history capture (for Streamlit replay / debugging)
    history: list[dict] = []
    world_layout: dict | None = None
    if record_history:
        world_layout = _capture_world_layout(environment)
        # Turn 0: initial state (agent at [1,1] facing EAST, empty percept)
        history.append(
            _make_snapshot(
                turn=0,
                action_name=None,
                user_position=(1, 1),
                direction_name=environment.get_agent_direction().name,
                percept=percept,
                total_reward=0,
                alive=True,
                death_cause=None,
                has_gold=False,
                has_arrow=True,
            )
        )
    
    # Display initial state (Turn 0) if verbose
    if verbose and visualizer is not None:
        initial_state = AgentState(
            position=Position(1, 1),  # Always starts at [1,1] in user coordinates
            direction=environment.get_agent_direction(),
            has_gold=False,
            is_alive=True,
            has_arrow=True,
        )
        print(f"\n{'-' * 60}")
        print("INITIAL STATE")
        visualizer.render(
            initial_state,
            percept,
            turn=0,
            alive=True,
            total_reward=0,
            death_cause=None,
        )
    
    # Main episode loop
    while turns < max_turns:
        # Agent decides action based on current percept
        action = agent.get_action(percept)
        
        # Environment executes action and returns new percept
        percept, ended = environment.step(action)
        total_reward += percept.reward
        turns += 1
        
        # Track agent inventory changes
        if action == Action.SHOOT:
            has_arrow = False
        if percept.glitter and not gold_collected:
            gold_collected = True

        # Resolve current alive/death state once for reuse below
        alive = environment.is_agent_alive()
        death_cause = None if alive else environment.get_death_cause()

        # Capture per-turn snapshot if recording history
        if record_history:
            current_pos = environment.get_agent_position()
            history.append(
                _make_snapshot(
                    turn=turns,
                    action_name=action.name,
                    user_position=(current_pos.x + 1, current_pos.y + 1),
                    direction_name=environment.get_agent_direction().name,
                    percept=percept,
                    total_reward=total_reward,
                    alive=alive,
                    death_cause=death_cause,
                    has_gold=gold_collected,
                    has_arrow=has_arrow,
                )
            )
        
        # Render turn state if visualization enabled
        if verbose and visualizer is not None:
            current_state = AgentState(
                position=environment.get_agent_position(),
                direction=environment.get_agent_direction(),
                has_gold=gold_collected,
                is_alive=alive,
                has_arrow=has_arrow,
            )
            # Convert internal coordinates [0,0] to user coordinates [1,1]
            display_state = AgentState(
                position=Position(
                    current_state.position.x + 1,
                    current_state.position.y + 1,
                ),
                direction=current_state.direction,
                has_gold=current_state.has_gold,
                is_alive=current_state.is_alive,
                has_arrow=current_state.has_arrow,
            )
            print(f"\n\n{'-' * 60}")
            print(f"TURN {turns - 1} --> TURN {turns}: Agent takes {action.name.upper()}")
            visualizer.render(
                display_state,
                percept,
                turn=turns,
                alive=alive,
                total_reward=total_reward,
                death_cause=death_cause,
            )
        
        # Check episode termination conditions
        if percept.reward == 1000:  # Escaped with gold
            escaped = True
            gold_collected = True
            break
        elif percept.reward == -1000:  # Died (pit or wumpus)
            died = True
            break
        
        if ended:
            # The death (-1000) and gold-escape (1000) cases are already handled
            # above, so reaching here with ended=True means the agent climbed
            # out without gold (reward=-1). Treat as escaped (alive, no gold).
            escaped = True
            break
    
    result = {
        "total_reward": total_reward,
        "turns_taken": turns,
        "gold_collected": gold_collected,
        "escaped": escaped,
        "died": died,
    }
    if record_history:
        result["history"] = history
        result["world_layout"] = world_layout
    return result
