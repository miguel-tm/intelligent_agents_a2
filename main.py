"""
Main entry point for the Wumpus World simulator.

This script runs multiple episodes of the Wumpus World with a NaiveAgent baseline.

Usage:
    python main.py              # Run 5 episodes (default)
    python main.py --verbose    # Run with per-turn visualization

Output:
    - Per-episode summary: steps, reward, gold collected, status
    - Aggregate statistics: escape rate, death rate, avg reward, avg steps
    - Optional: Per-turn grid visualization and percepts (with --verbose)
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
    - Run a NaiveAgent in the environment (5 episodes)
    - Display output (optional visualization with --verbose)
    - Print final statistics
    
    Future enhancement:
    - Add full command-line argument parsing for:
        - World size (--world-size N)
        - Pit probability (--pit-prob P)
        - Number of episodes (--episodes E)
        - Agent type selection (--agent-type TYPE)
        - Visualization control (--no-visualization)
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
    print("\n" + "=" * 80)
    print("WUMPUS WORLD SIMULATOR - Assignment 1")
    print("=" * 80)
    print(f"Configuration: {WORLD_WIDTH}x{WORLD_HEIGHT} world, {NUM_EPISODES} episodes")
    print(f"Pit Probability: {PIT_PROBABILITY}, Allow Climb Without Gold: {ALLOW_CLIMB_WITHOUT_GOLD}")
    print(f"Agent: NaiveAgent (uniform random action selection)")
    if verbose:
        print("Output Mode: Verbose (per-turn visualization)")
    else:
        print("Output Mode: Summary (episode summaries only)")
    print("=" * 80 + "\n")
    
    # Run episodes
    results = []
    for episode_num in range(NUM_EPISODES):
        # Print episode title if verbose
        if verbose:
            print("\n\n" + "=" * 80)
            print(f"EPISODE {episode_num + 1}")
            print("=" * 80)
        
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
            f"\n{'-' * 60}"
            f"\nEpisode ended"
            f"\nEpisode {episode_num + 1:2d}: "
            f"Steps={result['turns_taken']:3d} | "
            f"Reward={result['total_reward']:7.0f} | "
            f"Gold={str(result['gold_collected']):5s} | "
            f"{status}"
            f"\n{'-' * 60}"
        )
    
    # Print aggregate statistics
    print("\n" + "=" * 80)
    print("AGGREGATE STATISTICS")
    print("=" * 80)
    
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
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
