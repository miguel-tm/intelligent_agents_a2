# Assignment 1 Requirements - Wumpus World Simulator

## Objective
Build a Python simulator for the Wumpus World environment and a NaiveAgent.

## Functional Requirements
- Configurable environment with:
  - width
  - height
  - allowClimbWithoutGold
  - pitProb
- Standard configuration: (4, 4, true, 0.2)
- Agent starts at [1,1] facing right
- Random placement of Wumpus and gold in non-start squares
- Independent pit generation for non-start squares
- Wumpus, gold, and pit may overlap
- Actions:
  - Forward
  - TurnLeft
  - TurnRight
  - Shoot
  - Grab
  - Climb
- Percepts:
  - Stench
  - Breeze
  - Glitter
  - Bump
  - Scream
  - Reward
- Environment returns reward as part of percept
- Agent cannot directly inspect hidden environment state
- Episode ends on death or climb
- Include a simple visualizer
- Include a NaiveAgent with uniform random action selection

## Non-Functional Requirements
- Python
- object-oriented style
- maintain separation between environment state and agent knowledge
- code should be extensible for Assignment 2

## Proposed Modules
- models
- environment
- visualization
- agents
- tests

## Out of Scope for Assignment 1
- safe-cell memory
- planning
- graph search
- shortest path escape logic
- Assignment 2 functionality
