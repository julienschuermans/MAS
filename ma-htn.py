from __future__ import print_function
from pyhop import *

import blocks_world_operators
import blocks_world_methods

from blocks_world_agent import Agent, MultiAgentNegotiation

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
    state1.holding[name] = False

for _,agent in agents.items():
    agent.observe(state1)
    agent.plan(tasks)

# agents communicate to resolve dependencies/conflicts and assign tasks
comms = MultiAgentNegotiation('test')
comms.add_agents(agents.values())

plan = comms.find_resolution()

