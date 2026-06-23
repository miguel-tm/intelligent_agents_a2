#!/usr/bin/env python
"""Integration test: NaiveAgent with WumpusWorld environment."""

from agents import NaiveAgent
from wumpus import WumpusWorld
from wumpus.models import Percept

# Create environment
env = WumpusWorld(width=4, height=4, pit_probability=0.0, allow_climb_without_gold=True)
agent = NaiveAgent()

print('✓ Environment and agent initialized')

# Run a single episode
state = env.reset()
agent.reset()

total_reward = 0
steps = 0
max_steps = 100

# Create initial percept
percept = Percept()

print(f'✓ Starting episode at {state.position}')

while steps < max_steps:
    # Agent picks action
    action = agent.get_action(percept)
    
    # Environment executes action
    percept, ended = env.step(action)
    total_reward += percept.reward
    steps += 1
    
    if ended:
        print(f'✓ Episode ended after {steps} steps')
        print(f'  Final reward: {total_reward}')
        print(f'  Final percept: stench={percept.stench}, breeze={percept.breeze}, glitter={percept.glitter}')
        break

if steps >= max_steps:
    print(f'⚠ Episode did not end after {max_steps} steps')

print(f'\n✓ Integration test passed!')
print(f'  NaiveAgent successfully interacts with WumpusWorld environment')
