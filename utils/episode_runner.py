"""Episode runner utility for Wumpus World simulator.

Shared logic for running a single episode of the Wumpus World game.
Used by both CLI (main.py) and web UI (streamlit_app.py) visualizations.
"""

from wumpus import WumpusWorld, Visualizer
from wumpus.models import Action, Percept, AgentState, Position


def run_episode(
    agent,
    environment: WumpusWorld,
    visualizer: Visualizer | None = None,
    max_turns: int = 1000,
    verbose: bool = True,
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
        
    Returns:
        Dictionary with episode statistics:
        - total_reward: Cumulative reward across all turns
        - turns_taken: Number of turns executed
        - gold_collected: Whether agent found and grabbed gold
        - escaped: Whether agent escaped (with or without gold)
        - died: Whether agent died (pit or wumpus)
        
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
        
        # Render turn state if visualization enabled
        if verbose and visualizer is not None:
            current_state = AgentState(
                position=environment.get_agent_position(),
                direction=environment.get_agent_direction(),
                has_gold=gold_collected,
                is_alive=environment.is_agent_alive(),
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
            death_cause = None if environment.is_agent_alive() else environment.get_death_cause()
            visualizer.render(
                display_state,
                percept,
                turn=turns,
                alive=environment.is_agent_alive(),
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
            # Episode ended naturally (non-terminal action)
            if percept.reward > 0:
                escaped = True
            elif percept.reward < -100:  # Death penalty
                died = True
            break
    
    return {
        "total_reward": total_reward,
        "turns_taken": turns,
        "gold_collected": gold_collected,
        "escaped": escaped,
        "died": died,
    }
