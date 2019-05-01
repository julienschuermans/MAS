from pyhop import *
from blocks_world_tools import *

# state specification
state1 = State('state1')
state1.pos={'a':'c', 'b':'d', 'c':'table', 'd':'table'}
state1.clear={'a':True, 'c':False,'b':True, 'd':False}
state1.holding=False

sim = StateSimulation(state1)

print('before:')
print_state(sim.state)

plan = [('unstack', 'a', 'c'), ('putdown', 'a'), ('unstack', 'b', 'd'), ('stack', 'b', 'c'), ('pickup', 'a'), ('stack', 'a', 'd')]

for step in plan:
    sim.update(Action(step))

print('\nafter:')
print_state(sim.state)
