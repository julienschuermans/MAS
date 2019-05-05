from __future__ import print_function
from pyhop import *

import logging

import blocks_world_operators
import blocks_world_methods

from blocks_world_agent import Agent, MultiAgentNegotiation

logging.basicConfig(level=logging.DEBUG)

# state specification
state1 = State('state1')
state1.pos={'a':'c', 'b':'d', 'c':'table', 'd':'table'}
state1.clear={'a':True, 'c':False,'b':True, 'd':False}
state1.holding={}

# goal specification
goal2b = Goal('goal2b')
goal2b.pos={'b':'c', 'a':'d'}

# task specification
tasks = [('move_blocks', goal2b)]

# agent creation
agents = {} # dictionary of names mapping to Agent() objects
nb_agents = 2
for i in range(nb_agents):
    name = 'A'+str(i)
    agents[name] = Agent(name)
    state1.holding[name] = False #by default, in the beginning, an agent isn't holding anything

for agent in agents.values():
    agent.observe(state1) #TODO what happens when agents don't observe everything?
    agent.plan(tasks) #use pyphop to generate a personal plan

# agents communicate to resolve dependencies/conflicts and assign tasks
comms = MultiAgentNegotiation('test')
comms.add_agents(agents.values())

plan = comms.find_resolution()

# agents['A0'].print_final_plan()

def print_plan(plan):
    for t,steps in plan.items():
        print('t=' + str(t))
        for action in steps:
            print(action)
        
print_plan(plan)