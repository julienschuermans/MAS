"""
Blocks World domain definition for Pyhop 1.1.
Author: Dana Nau <nau@cs.umd.edu>, November 15, 2012
This file should work correctly in both Python 2.7 and Python 3.2.
"""

import pyhop

"""Each Pyhop planning operator is a Python function. The 1st argument is
the current state, and the others are the planning operator's usual arguments.
This is analogous to how methods are defined for Python classes (where
the first argument is always the name of the class instance). For example,
the function pickup(state,b) implements the planning operator for the task
('pickup', b).

The blocks-world operators use three state variables:
- pos[b] = block b's position, which may be 'table', 'hand', or another block.
- clear[b] = False if a block is on b or the hand is holding b, else True.
- holding = name of the block being held, or False if the hand is empty.
"""

def pickup(state,b,agent_name):
    if agent_name == 'virtualagent' and state.pos[b] == 'table' and state.clear[b] == True and (False in state.holding['virtualagent']):
        state.pos[b] = 'hand'
        state.clear[b] = False
        for i,value in enumerate(state.holding[agent_name],0):
            if value == False:
                state.holding[agent_name][i] = b
                break
        return state
    elif state.pos[b] == 'table' and state.clear[b] == True and state.holding[agent_name] == False:
        state.pos[b] = 'hand'
        state.clear[b] = False
        state.holding[agent_name] = b
        return state
    else: return False

def unstack(state,b,c,agent_name):
    if agent_name == 'virtualagent' and state.pos[b] == c and c != 'table' and state.clear[b] == True and (False in state.holding['virtualagent']):
        state.pos[b] = 'hand'
        state.clear[b] = False
        for i,value in enumerate(state.holding[agent_name],0):
            if value == False:
                state.holding[agent_name][i] = b
                break
        state.clear[c] = True
        return state
    elif state.pos[b] == c and c != 'table' and state.clear[b] == True and state.holding[agent_name] == False:
        state.pos[b] = 'hand'
        state.clear[b] = False
        state.holding[agent_name] = b
        state.clear[c] = True
        return state
    else: return False
    
def putdown(state,b,agent_name):
    if agent_name == 'virtualagent' and state.pos[b] == 'hand' and (b in state.holding[agent_name]):
        state.pos[b] = 'table'
        state.clear[b] = True
        # assuming only one value in the holding list of 'virtualagent' is equal to b
        for i,value in enumerate(state.holding[agent_name],0):
            if value == b:
                state.holding[agent_name][i] = False
                break
        #state.holding[agent_name] = [False for value in state.holding[agent_name] if value==b]
        return state
    elif state.pos[b] == 'hand' and state.holding[agent_name]==b:
        state.pos[b] = 'table'
        state.clear[b] = True
        state.holding[agent_name] = False
        return state
    else: return False

def stack(state,b,c,agent_name):
    if agent_name == 'virtualagent' and state.pos[b] == 'hand' and state.clear[c] == True and (b in state.holding[agent_name]):
        state.pos[b] = c
        state.clear[b] = True
        state.clear[c] = False
        for i,value in enumerate(state.holding[agent_name],0):
            if value == b:
                state.holding[agent_name][i] = False
                break
        return state
    if state.pos[b] == 'hand' and state.clear[c] == True and state.holding[agent_name]==b:
        state.pos[b] = c
        state.clear[b] = True
        state.holding[agent_name] = False
        state.clear[c] = False
        return state
    else: return False

"""
Below, 'declare_operators(pickup, unstack, putdown, stack)' tells Pyhop
what the operators are. Note that the operator names are *not* quoted.
"""

pyhop.declare_operators(pickup, unstack, putdown, stack)
