from __future__ import print_function
from pyhop import *

import logging
import time
import blocks_world_operators
import blocks_world_methods

from blocks_world_agent import Agent, MultiAgentNegotiation

logging.basicConfig(level=logging.ERROR)

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

# state specification
state3 = State('state3')
state3.pos = {1:12, 12:13, 13:'table', 11:10, 10:5, 5:4, 4:14, 14:15, 15:'table', 9:8, 8:7, 7:6, 6:'table', 19:18, 18:17, 17:16, 16:3, 3:2, 2:'table'}
state3.clear = {x:False for x in range(1,20)}
state3.clear.update({1:True, 11:True, 9:True, 19:True})
state3.holding = {}


# goal specification
goal3 = Goal('goal3')
goal3.pos = {15:13, 13:8, 8:9, 9:4, 4:'table', 12:2, 2:3, 3:16, 16:11, 11:7, 7:6, 6:'table'}
goal3.clear = {17:True, 15:True, 12:True}


# task specification
tasks = [('move_blocks', goal3)]

# agent creation
agents = {} # dictionary of names mapping to Agent() objects
nb_agents = 10
for i in range(nb_agents):
    name = 'A'+str(i)
    agents[name] = Agent(name)
    state3.holding[name] = False #by default, in the beginning, an agent isn't holding anything

for agent in agents.values():
    agent.observe(state3) #TODO what happens when agents don't observe everything?
    agent.plan(tasks) #use pyphop to generate a personal plan

# agents communicate to resolve dependencies/conflicts and assign tasks
comms = MultiAgentNegotiation('test')
comms.add_agents(agents.values())
start = time.time()
plan = comms.find_resolution()
stop = time.time()
# agents['A0'].print_final_plan()

def print_plan(plan):
    for t,steps in plan.items():
        print('t=' + str(t))
        for action in steps:
            print(action)
        
print_plan(plan)
print(stop-start)
