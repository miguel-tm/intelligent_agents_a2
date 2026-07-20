"""
Main entry point for the Wumpus World simulator.

This script runs multiple episodes of the Wumpus World with a selectable agent.

Usage:
    python main.py                             # Run 5 episodes with MovePlanningAgent (default)
    python main.py --agent naive               # Run with NaiveAgent baseline
    python main.py --verbose                   # Per-turn visualization (MovePlanningAgent)
    python main.py --agent naive --verbose     # Per-turn visualization (NaiveAgent)

Output:
    - Per-episode summary: steps, reward, gold collected, status
    - Aggregate statistics: escape rate, death rate, avg reward, avg steps
    - Optional: Per-turn grid visualization and percepts (with --verbose)
"""

from wumpus import WumpusWorld, Visualizer
from agents import NaiveAgent, MovePlanningAgent
import sys

from utils import run_episode


def main() -> None:
    """
    Run the Wumpus World simulator.

    Default behaviour:
    - Create a 4×4 Wumpus World with standard configuration.
    - Run the selected agent for 5 episodes.
    - Display output (optional per-turn visualization with --verbose).
    - Print final aggregate statistics.
    """
    # Parse command-line arguments
    verbose = "--verbose" in sys.argv

    agent_choice = "move_planning"
    if "--agent" in sys.argv:
        idx = sys.argv.index("--agent")
        if idx + 1 < len(sys.argv):
            agent_choice = sys.argv[idx + 1]

    if agent_choice not in ("move_planning", "naive"):
        print(f"Unknown agent '{agent_choice}'. Choose 'move_planning' or 'naive'.")
        sys.exit(1)

    # Game configuration
    NUM_EPISODES = 5
    WORLD_WIDTH = 4
    WORLD_HEIGHT = 4
    PIT_PROBABILITY = 0.2
    ALLOW_CLIMB_WITHOUT_GOLD = True  # World-level setting; may not affect all agents
                                     # (e.g. MovePlanningAgent never CLIMBs without gold
                                     # regardless of this flag, due to its internal logic)

    # Header
    agent_label = "MovePlanningAgent" if agent_choice == "move_planning" else "NaiveAgent (uniform random)"
    print("\n" + "=" * 80)
    print("WUMPUS WORLD SIMULATOR - Assignment 2")
    print("=" * 80)
    print(f"Configuration: {WORLD_WIDTH}x{WORLD_HEIGHT} world, {NUM_EPISODES} episodes")
    print(f"Pit Probability: {PIT_PROBABILITY}, Allow Climb Without Gold: {ALLOW_CLIMB_WITHOUT_GOLD}")
    print(f"Agent: {agent_label}")
    if verbose:
        print("Output Mode: Verbose (per-turn visualization)")
    else:
        print("Output Mode: Summary (episode summaries only)")
    print("=" * 80 + "\n")

    # Run episodes
    results = []
    for episode_num in range(NUM_EPISODES):
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
        agent = MovePlanningAgent() if agent_choice == "move_planning" else NaiveAgent()

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
