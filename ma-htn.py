from __future__ import print_function
from pyhop import *

import blocks_world_operators
import blocks_world_methods

from blocks_world_agent import Agent, MultiAgentNegotiation

# state specification
state1 = State('state1')
state1.pos={'a':'c', 'b':'d', 'c':'table', 'd':'table'}
state1.clear={'a':True, 'c':False,'b':True, 'd':False}
state1.holding=False

# goal specification
goal2b = Goal('goal2b')
goal2b.pos={'b':'c', 'a':'d'}

# task specification
tasks = [('move_blocks', goal2b)]

# agent creation
a1 = Agent('agent 1')
a2 = Agent('agent 2')

# for now, both agents observe the (complete) state the same way
# later on, agents may only perceive partial
a1.observe(state1)
a2.observe(state1)

# agents calculate a (partial) plan
a1.plan(tasks)
a2.plan(tasks)

# agents communicate to resolve dependencies/conflicts and assign tasks
comms = MultiAgentNegotiation('test')

comms.add_agent(a1)
comms.add_agent(a2)

plan = comms.find_resolution()
