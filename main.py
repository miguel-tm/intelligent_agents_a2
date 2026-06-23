"""
Main entry point for the Wumpus World simulator.

This script demonstrates running a single episode of the Wumpus World with
a NaiveAgent. It serves as a template for running experiments or testing.

Usage:
    python main.py

Output:
    - Agent decisions and percepts for each turn
    - Final score and episode summary
    - Statistics about the episode (turns taken, actions performed, etc.)

TODO: Implement game loop
TODO: Integrate visualization
TODO: Add command-line arguments for configuration
"""

from wumpus import WumpusWorld, Visualizer
from agents import NaiveAgent
from wumpus.models import Action, Percept, AgentState, Position
import sys


def run_episode(
    agent,
    environment: WumpusWorld,
    visualizer: Visualizer | None = None,
    max_turns: int = 1000,
    verbose: bool = True,
) -> dict:
    """
    Run a single episode of the Wumpus World game.
    
    Args:
        agent: The agent to control
        environment: The WumpusWorld environment
        visualizer: Optional Visualizer for rendering (None = no visualization)
        max_turns: Maximum number of turns before forcing episode end
        verbose: If True, print turn information
        
    Returns:
        Dictionary with episode statistics:
        - total_reward: Cumulative reward
        - turns_taken: Number of turns
        - gold_collected: Whether agent found gold
        - escaped: Whether agent escaped with/without gold
        - died: Whether agent died
        
    TODO: Implement episode loop
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
    
    # Main episode loop
    while turns < max_turns:
        # Agent decides action
        action = agent.get_action(percept)
        
        # Environment executes action
        percept, ended = environment.step(action)
        total_reward += percept.reward
        turns += 1
        
        # Track agent inventory changes
        if action == Action.SHOOT:
            has_arrow = False
        if percept.glitter and not gold_collected:
            gold_collected = True
        
        # Get current agent state from environment for visualization
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
            print(f"\n  Turn {turns}: Agent takes {action.name.upper()}")
            visualizer.render(display_state, percept, turn=turns, alive=environment.is_agent_alive())
        
        # Detect episode termination conditions
        if percept.reward == 1000:  # Escaped with gold
            escaped = True
            gold_collected = True
            break
        elif percept.reward == -1000:  # Died (pit or wumpus)
            died = True
            break
        
        if ended:
            # Episode ended naturally
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


def main() -> None:
    """
    Run the Wumpus World simulator.
    
    Default behavior:
    - Create a 4x4 Wumpus World with standard configuration
    - Run a NaiveAgent in the environment
    - Display output (optional visualization)
    - Print final statistics
    
    TODO: Implement main game loop
    TODO: Add command-line argument parsing for:
        - World size
        - Pit probability
        - Number of episodes
        - Agent type selection
        - Visualization on/off
    """
    # Parse command-line arguments
    verbose = "--verbose" in sys.argv
    
    # Game configuration
    NUM_EPISODES = 5
    WORLD_WIDTH = 4
    WORLD_HEIGHT = 4
    PIT_PROBABILITY = 0.2
    ALLOW_CLIMB_WITHOUT_GOLD = True
    
    # Header
    print("\n" + "=" * 70)
    print("WUMPUS WORLD SIMULATOR - Assignment 1")
    print("=" * 70)
    print(f"Configuration: {WORLD_WIDTH}x{WORLD_HEIGHT} world, {NUM_EPISODES} episodes")
    print(f"Pit Probability: {PIT_PROBABILITY}, Allow Climb Without Gold: {ALLOW_CLIMB_WITHOUT_GOLD}")
    print(f"Agent: NaiveAgent (uniform random action selection)")
    if verbose:
        print("Output Mode: Verbose (per-turn visualization)")
    else:
        print("Output Mode: Summary (episode summaries only)")
    print("=" * 70 + "\n")
    
    # Run episodes
    results = []
    for episode_num in range(NUM_EPISODES):
        # Print episode title if verbose
        if verbose:
            print("\n" + "=" * 50)
            print(f"EPISODE {episode_num + 1}")
            print("=" * 50)
        
        # Create new environment and agent for each episode
        env = WumpusWorld(
            width=WORLD_WIDTH,
            height=WORLD_HEIGHT,
            allow_climb_without_gold=ALLOW_CLIMB_WITHOUT_GOLD,
            pit_probability=PIT_PROBABILITY,
        )
        agent = NaiveAgent()
        
        # Optional visualizer
        visualizer = Visualizer(WORLD_WIDTH, WORLD_HEIGHT) if verbose else None
        
        # Run episode
        result = run_episode(agent, env, visualizer=visualizer, verbose=verbose)
        results.append(result)
        
        # Print episode summary
        status = "ESCAPED" if result["escaped"] else ("DIED" if result["died"] else "TIMEOUT")
        print(
            f"Episode {episode_num + 1:2d}: "
            f"Steps={result['turns_taken']:3d} | "
            f"Reward={result['total_reward']:7.0f} | "
            f"Gold={str(result['gold_collected']):5s} | "
            f"{status}"
        )
    
    # Print aggregate statistics
    print("\n" + "=" * 70)
    print("AGGREGATE STATISTICS")
    print("=" * 70)
    
    total_reward = sum(r["total_reward"] for r in results)
    total_steps = sum(r["turns_taken"] for r in results)
    escapes = sum(1 for r in results if r["escaped"])
    deaths = sum(1 for r in results if r["died"])
    gold_collected = sum(1 for r in results if r["gold_collected"])
    
    print(f"Total Episodes: {NUM_EPISODES}")
    print(f"Successful Escapes: {escapes}/{NUM_EPISODES} ({100*escapes/NUM_EPISODES:.1f}%)")
    print(f"Deaths: {deaths}/{NUM_EPISODES} ({100*deaths/NUM_EPISODES:.1f}%)")
    print(f"Gold Collected: {gold_collected}/{NUM_EPISODES} ({100*gold_collected/NUM_EPISODES:.1f}%)")
    print(f"Total Reward: {total_reward:.0f}")
    print(f"Average Reward per Episode: {total_reward/NUM_EPISODES:.1f}")
    print(f"Average Steps per Episode: {total_steps/NUM_EPISODES:.1f}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
