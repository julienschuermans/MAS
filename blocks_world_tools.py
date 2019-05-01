import pyhop
from blocks_world_operators import *
import copy

class Action():
    def __init__(self, agent, action_tuple):
        assert(type(action_tuple)==tuple)
        self.agent = agent
        self.operator = action_tuple[0]
        self.arguments = action_tuple[1:]

class StateSimulation():

    def __init__(self, initialState):
        assert(type(initialState)==pyhop.State)
        self.state = copy.deepcopy(initialState)
        self.step = 0

    def update(self, action):
        if action.operator in pyhop.operators:
            operator = pyhop.operators[action.operator]
            newState = operator(copy.deepcopy(self.state),*action.arguments,action.agent.__name__)
            if newState == False:
                raise RuntimeError("Tried to apply illegal operator during simulation.")
            else:
                self.state = newState
            self.step += 1
        else:
            raise KeyError("Operator not defined in pyhop: " + action.operator)

    def update_parallel(self,actions):
        # You have to be very careful when you call this function:
        # It assumes all given actions are independent, and can be executed concurrently.
        # It should NOT matter in which order they are given (since it's parallel! duh).

        start = self.step
        for action in actions:
            self.update(action)
        self.step = start + 1


class Dependency():
    def __init__(self, action_1, action_2):
        self.action_1 = action_1
        self.action_2 = action_2
    

class Conflict():
    def __init__(self,type='concurrent'):
        self.type = type

class DependencyMap():
    def __init__(self, dependencies):
        self.dependencies = dependencies

class ConflictMap():
    def __init__(self,conflicts):
        self.type = type

