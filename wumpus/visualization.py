"""
Visualization utilities for the Wumpus World environment.

This module provides tools to display the game state in a human-readable format.
The visualizer shows:
- The agent's position and facing direction
- The agent's current percepts
- The grid with visible symbols
- Game status (alive, dead, gold collected, etc.)

Important: The visualizer only displays what the agent KNOWS or CAN SEE,
not the hidden world state (wumpus location, pit locations, etc.).

Key class:
- Visualizer: Renders the game state
"""

from wumpus.models import AgentState, Direction, Percept


class Visualizer:
    """
    Displays the Wumpus World game state to the user.
    
    The Visualizer shows:
    - The grid with the agent's position
    - The agent's current percepts
    - Game status information
    - Turn count and other statistics
    
    Note:
        The visualizer respects the agent's information constraints and only
        displays information the agent can perceive or deduce.
    
    TODO: Implement grid rendering, symbol drawing, and formatted output
    """

    def __init__(self, width: int, height: int):
        """
        Initialize the Visualizer.
        
        Args:
            width: Grid width
            height: Grid height
        """
        self.width = width
        self.height = height

    def render(
        self,
        agent_state: AgentState,
        percept: Percept,
        turn: int = 0,
        alive: bool = True,
        total_reward: int = 0,
    ) -> None:
        """
        Render the current game state to console output.
        
        Args:
            agent_state: The agent's current state (position, direction, items)
            percept: The agent's current percepts (stench, breeze, glitter, etc.)
            turn: Current turn number (for display purposes)
            alive: Whether the agent is still alive
            total_reward: Cumulative reward so far in the episode
            
        Displayed information:
        - Grid with agent position and direction arrow
        - Current position and inventory
        - Current percepts
        - Game status
        
        TODO: Implement grid rendering and formatting
        """
        # Header with turn and status
        status = "Alive" if alive else "Dead"
        print(f"\n{'-' * 60}")
        print(f"Turn {turn} | Status: {status} | Position: {agent_state.position}")
        print(f"{'-' * 60}")
        
        # Grid display
        print(self._draw_grid(agent_state))
        
        # Percepts and inventory
        print(f"Percepts: {self._render_percepts(percept)}")
        print(f"Reward: {percept.reward}, Total Reward: {total_reward}")
        print(f"Inventory: Gold={agent_state.has_gold}, Arrow={agent_state.has_arrow}")

    def _draw_grid(self, agent_state: AgentState) -> str:
        """
        Generate a string representation of the grid.
        
        Grid symbols:
        - A: Agent (with direction: > ^ v <)
        - .: Empty cell (no known hazards)
        - ?: Unknown cell (not yet visited)
        
        Returns:
            Formatted grid as a string
            
        TODO: Implement grid drawing
        """
        lines = ["+" + "-" * (self.width * 2 + 1) + "+"]
        
        # Draw grid from top to bottom (y decreasing in display, but coordinates increase upward)
        for y in range(self.height - 1, -1, -1):
            row = "| "
            for x in range(self.width):
                # Check if agent is at this position
                # Note: agent_state.position is in user coordinates [1,1] to [4,4]
                # Loop variables x,y are array indices [0,0] to [3,3]
                # Convert user coords to array indices by subtracting 1
                if agent_state.position.x - 1 == x and agent_state.position.y - 1 == y:
                    # Draw agent with direction symbol
                    row += self._direction_symbol(agent_state.direction)
                else:
                    # Draw empty cell
                    row += "."
                row += " "
            row += "|"
            lines.append(row)
        
        lines.append("+" + "-" * (self.width * 2 + 1) + "+")
        return "\n".join(lines)

    def _direction_symbol(self, direction: Direction) -> str:
        """
        Get the symbol representing a direction.
        
        TODO: Implement direction to symbol conversion
        """
        direction_symbols = {
            Direction.NORTH: "^",
            Direction.SOUTH: "v",
            Direction.EAST: ">",
            Direction.WEST: "<",
        }
        return direction_symbols.get(direction, "?")

    def _render_percepts(self, percept: Percept) -> str:
        """
        Format percepts into a readable string.
        
        Returns:
            String like "Stench, Breeze, Glitter" or "No percepts"
            
        TODO: Implement percept formatting
        """
        percepts = []
        if percept.stench:
            percepts.append("Stench")
        if percept.breeze:
            percepts.append("Breeze")
        if percept.glitter:
            percepts.append("Glitter")
        if percept.bump:
            percepts.append("Bump")
        if percept.scream:
            percepts.append("Scream")
        
        if percepts:
            return " | ".join(percepts)
        else:
            return "None"
