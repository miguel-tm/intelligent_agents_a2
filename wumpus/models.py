"""
Data models for the Wumpus World environment.

This module defines the core data structures used throughout the Wumpus World
simulator, including game state representations, percepts, and agent beliefs.
All models use type hints and dataclasses for clarity and type safety.

Key classes:
- Direction: Enum for agent facing direction with turn helpers
- Action: Enum for possible agent actions
- Position: Dataclass for 2D grid coordinates
- Percept: Dataclass for sensory information returned to agent
- AgentState: Dataclass for agent's internal belief state (not hidden world state)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class Direction(Enum):
    """
    Enum representing the four cardinal directions the agent can face.
    
    Values:
        NORTH: Agent facing up (decreasing y)
        EAST: Agent facing right (increasing x)
        SOUTH: Agent facing down (increasing y)
        WEST: Agent facing left (decreasing x)
    """
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def turn_left(self) -> "Direction":
        """
        Return the direction after a 90-degree left turn.
        
        TODO: Implement turn_left logic (rotate counter-clockwise)
        """
        # Rotate counter-clockwise: EAST->NORTH->WEST->SOUTH->EAST
        return Direction((self.value - 1) % 4)

    def turn_right(self) -> "Direction":
        """
        Return the direction after a 90-degree right turn.
        
        TODO: Implement turn_right logic (rotate clockwise)
        """
        # Rotate clockwise: EAST->SOUTH->WEST->NORTH->EAST
        return Direction((self.value + 1) % 4)

    def get_forward_position(self, current_pos: "Position") -> "Position":
        """
        Calculate the position one step forward from current position in this direction.
        
        Args:
            current_pos: The current position of the agent
            
        Returns:
            A new Position representing one step forward
            
        TODO: Implement forward position calculation based on direction
        """
        # Move one step in the direction
        # Grid coordinate system: x increases right (EAST), y increases up (NORTH)
        # Uses mathematical coordinates: [1,1] at bottom-left, [4,4] at top-right
        if self == Direction.NORTH:
            return Position(current_pos.x, current_pos.y + 1)
        elif self == Direction.SOUTH:
            return Position(current_pos.x, current_pos.y - 1)
        elif self == Direction.EAST:
            return Position(current_pos.x + 1, current_pos.y)
        elif self == Direction.WEST:
            return Position(current_pos.x - 1, current_pos.y)
        else:
            raise ValueError(f"Unknown direction: {self}")


class Action(Enum):
    """
    Enum representing all possible actions the agent can take.
    
    Values:
        FORWARD: Move one step in the current facing direction
        TURN_LEFT: Rotate 90 degrees counter-clockwise
        TURN_RIGHT: Rotate 90 degrees clockwise
        SHOOT: Fire the arrow in the current facing direction
        GRAB: Pick up gold at current location
        CLIMB: Exit the environment (only works at [1,1])
    """
    FORWARD = "forward"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    SHOOT = "shoot"
    GRAB = "grab"
    CLIMB = "climb"


@dataclass(frozen=True)
class Position:
    """
    Immutable representation of a 2D position on the grid.
    
    Attributes:
        x: Column coordinate (0 to width-1)
        y: Row coordinate (0 to height-1)
    
    Note:
        Position [1,1] is the agent's starting location in standard configuration.
        Uses 0-based indexing internally, but may be displayed as 1-based in visualizations.
    """
    x: int
    y: int

    def is_valid(self, width: int, height: int) -> bool:
        """
        Check if this position is within grid bounds.
        
        Args:
            width: Grid width
            height: Grid height
            
        Returns:
            True if 0 <= x < width and 0 <= y < height
            
        TODO: Implement bounds checking
        """
        return 0 <= self.x < width and 0 <= self.y < height

    def __eq__(self, other: object) -> bool:
        """Check if two positions are identical."""
        if not isinstance(other, Position):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        """Make Position hashable for use in sets and dicts."""
        return hash((self.x, self.y))


@dataclass
class Percept:
    """
    Represents the sensory information returned to the agent.
    
    The agent perceives the environment through these five senses plus a reward signal.
    The agent has NO direct access to hidden world state (wumpus location, pit locations, etc.).
    
    Attributes:
        stench: bool - True if wumpus is in an adjacent square
        breeze: bool - True if pit is in an adjacent square
        glitter: bool - True if gold is at the current location
        bump: bool - True if agent just tried to move outside the grid
        scream: bool - True if the wumpus was just killed by an arrow
        reward: float - Immediate reward/penalty for the action taken
    
    Note:
        The environment determines rewards. Typical values:
        - +1000 for reaching [1,1] with gold and climbing out
        - -1 per action
        - -10 for dying
        - +1 for finding gold
    """
    stench: bool = False
    breeze: bool = False
    glitter: bool = False
    bump: bool = False
    scream: bool = False
    reward: float = 0.0


@dataclass
class AgentState:
    """
    Represents the agent's internal belief state and tracked data.
    
    This is NOT the hidden world state. This is what the agent believes or remembers.
    The environment (WumpusWorld) maintains the true hidden state separately.
    
    Attributes:
        position: Agent's current position
        direction: Agent's current facing direction
        has_gold: Whether the agent believes it has picked up the gold
        is_alive: Whether the agent is still alive (not in a pit, not killed by wumpus)
        has_arrow: Whether the agent still has its arrow
    
    Note:
        A simple agent may not use all these fields. More sophisticated agents
        (e.g. MovePlanningAgent) track additional beliefs such as visited safe cells,
        estimated position, and planned action sequences separately inside the agent class.
        For reference implementations, this dataclass is primarily for action outcome tracking.
    """
    position: Position
    direction: Direction
    has_gold: bool = False
    is_alive: bool = True
    has_arrow: bool = True
