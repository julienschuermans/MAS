from pyhop import *
from blocks_world_tools import *
from blocks_world_agent import Agent

# state specification
state1 = State('state1')
state1.pos={'a':'c', 'b':'d', 'c':'table', 'd':'table'}
state1.clear={'a':True, 'c':False,'b':True, 'd':False}
state1.holding={}


agents = {}
nb_agents = 2
for i in range(nb_agents):
    name = 'A'+str(i)
    agents[name] = Agent(name)
    state1.holding[name] = False

sim = StateSimulation(state1)

print('before:')
print_state(sim.state)


## Scenario 1: A single agent performs all actions in the plan
plan = [('unstack', 'a', 'c'), ('putdown', 'a'), ('unstack', 'b', 'd'), ('stack', 'b', 'c'), ('pickup', 'a'), ('stack', 'a', 'd')]

for step in plan:
    sim.update(Action(agents['A0'],step))
    print_state(sim.state)


## Scenario 2: Agents perform independent, non-conflicting actions in parallel
# sim.update_parallel([Action(agents['A0'],('unstack', 'a', 'c')),Action(agents['A1'],('unstack', 'b', 'd'))])


print('\nafter:')
print_state(sim.state)
