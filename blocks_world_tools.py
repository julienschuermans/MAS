import pyhop
from blocks_world_operators import *
import copy

class Action():
    def __init__(self, action_data):
        assert(type(action_data)==tuple)
        self.operator = action_data[0]
        self.arguments = action_data[1:]


class StateSimulation():

    def __init__(self, initialState):
        assert(type(initialState)==pyhop.State)
        self.state = copy.deepcopy(initialState)
        self.step = 0

    def update(self, action):
        if action.operator in pyhop.operators:
            operator = pyhop.operators[action.operator]
            newState = operator(copy.deepcopy(self.state),*action.arguments)
            if newState == False:
                raise RuntimeError("Tried to apply illegal operator during simulation")
            else:
                self.state = newState
            self.step += 1
        else:
            raise KeyError("Operator not defined in pyhop: " + action.operator)