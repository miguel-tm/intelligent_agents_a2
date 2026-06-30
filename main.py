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
import sys

from utils import run_episode


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
