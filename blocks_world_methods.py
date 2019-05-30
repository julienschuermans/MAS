"""
Blocks World methods for Pyhop 1.1.
Author: Dana Nau <nau@cs.umd.edu>, November 15, 2012
This file should work correctly in both Python 2.7 and Python 3.2.
"""

import pyhop


"""
Here are some helper functions that are used in the methods' preconditions.
"""

def get_nb_blocks_above(b1,state):
    above = 0
    for upper, lower in state.pos.items():
        if lower==b1:
            above+=1
            break
    if above ==0:
        return above
    else:
        return above + get_nb_blocks_above(upper,state)

def is_done(b1,state,goal):
    # print(state.pos[b1])
    # print(b1)
    # print(goal.pos)
    if b1 == 'table': return True
    if b1 in goal.pos and state.pos[b1] == goal.pos[b1] and is_done(state.pos[b1],state,goal): return True
    if b1 in goal.pos and (goal.pos[b1] != state.pos[b1]):
        return False
    if (not b1 in goal.pos) and (state.pos[b1] in goal.pos.values()): return False
    if (not b1 in goal.pos) and state.pos[b1] == 'table': return True
    return is_done(state.pos[b1],state,goal)

def status(b1,state,goal):
    if is_done(b1,state,goal):
        return 'done'
    elif not state.clear[b1]:
        return 'inaccessible'
    elif not (b1 in goal.pos):
        if state.pos[b1]!='table': #every block that is not specified in the goals, is put on the table
            # if state.pos[b1]!='table' and (state.pos[b1] in goal.pos.values()):
            return 'move-to-table'
        else:
            return 'waiting'
    elif goal.pos[b1] == 'table':
        return 'move-to-table'
    elif not (state.clear[goal.pos[b1]]):
        #print(state.pos[b1])
        if get_nb_blocks_above(goal.pos[b1],state)>1 and state.pos[b1]!='table':
            print('no swap')
            return 'move-to-table'
        elif get_nb_blocks_above(goal.pos[b1],state)==1 and state.pos[b1]!=goal.pos[b1]:
            print('swap')
            # if is_done(goal.pos[b1],state,goal):
            return 'swap'
        else:
            print('waitingg')
            return 'waiting'
    elif is_done(goal.pos[b1],state,goal) and state.clear[goal.pos[b1]]:
        return 'move-to-block'
    else:
        return 'waiting'

def all_blocks(state):
    return state.clear.keys()


"""
In each Pyhop planning method, the first argument is the current state (this is analogous to Python methods, in which the first argument is the class instance). The rest of the arguments must match the arguments of the task that the method is for. For example, ('pickup', b1) has a method get_m(state,b1), as shown below.
"""

### methods for "move_blocks"

def moveb_m(state,goal):
    """
    This method implements the following block-stacking algorithm:
    If there's a block that can be moved to its final position, then
    do so and call move_blocks recursively. Otherwise, if there's a
    block that needs to be moved and can be moved to the table, then 
    do so and call move_blocks recursively. Otherwise, no blocks need
    to be moved.
    """
    for b1 in all_blocks(state):
        s = status(b1,state,goal)
        # print(s)
        # print(b1, get_nb_blocks_above(b1,state))
        if s == 'move-to-table':
            return [('move_one',b1,'table'),('move_blocks',goal)]
        elif s == 'move-to-block':
            return [('move_one',b1,goal.pos[b1]), ('move_blocks',goal)]
        elif s == 'swap':
            return [('swap_blocks',b1,goal.pos[b1]),('move_blocks',goal)]
        else:
            continue
    #
    # if we get here, no blocks can be moved to their final locations
    b1 = pyhop.find_if(lambda x: status(x,state,goal) == 'waiting', all_blocks(state))
    if b1 != None:
        print('no more waiting')
        return [('move_one',b1,'table'), ('move_blocks',goal)]
    #
    # if we get here, there are no blocks that need moving
    return []

"""
declare_methods must be called once for each taskname. Below, 'declare_methods('get',get_m)' tells Pyhop that 'get' has one method, get_m. Notice that 'get' is a quoted string, and get_m is the actual function.
"""
pyhop.declare_methods('move_blocks',moveb_m)


### methods for "move_one"

def move1(state,b1,dest):
    """
    Generate subtasks to get b1 and put it at dest.
    """
    return [('get', b1), ('put', b1,dest)]

pyhop.declare_methods('move_one',move1)

def swap_m(state,b1,dest):
    obstacle = [key  for (key, value) in state.pos.items() if value == dest]
    if state.clear[b1] and state.clear[obstacle[0]]:
        return [('swap',b1,obstacle[0])]
    else:
        return False

pyhop.declare_methods('swap_blocks',swap_m)


### methods for "get"

def get_m(state,b1):
    """
    Generate either a pickup or an unstack subtask for b1.
    """
    if state.clear[b1]:
        if state.pos[b1] == 'table':
                return [('pickup',b1)]
        else:
                return [('unstack',b1,state.pos[b1])]
    else:
        return False

pyhop.declare_methods('get',get_m)


### methods for "put"

def put_m(state,b1,b2):
    """
    Generate either a putdown or a stack subtask for b1.
    b2 is b1's destination: either the table or another block.
    """
    if b1 in state.holding.values(): #dirty hack: "if someone is holding b1"
        if b2 == 'table':
                return [('putdown',b1)]
        else:
                return [('stack',b1,b2)]
    else:
        return False

pyhop.declare_methods('put',put_m)


