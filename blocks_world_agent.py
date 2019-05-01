from pyhop import *
from blocks_world_tools import Action

import random

class Agent():
    """An agent planning to act in a (multi-agent) blocks world."""

    def __init__(self,name):
        self.__name__ = name
        self.possible_actions = None
        self.observed_state = None
        self.partial_plan = None
        self.final_plan = None
    
    def observe(self,state):
        self.observed_state = state
    
    def assign_actions(self,actions):
        # an agent may be restricted to perform a subset of all possible actions
        self.possible_actions = actions

    def plan(self,tasks):
        self.partial_plan = pyhop(self.observed_state,tasks,self.__name__,verbose=0)

    def evaluate_dependencies(self):
        # TODO: process self.partial_plan to detect dependencies between actions
        # some actions **have** to be performed before others
        # this is almost becoming a scheduling problem
        raise NotImplementedError('whoops')

    def evaluate_conflicts(self):
        # TODO: process self.partial_plan to detect conflicts between actions
        # some actions can not be processed concurrently
        # some actions produce effects that make future actions impossible
        raise NotImplementedError('whoops')

    def generate_random_number(self):
        return random.random()


    def make_proposal(self):
        # Returns a tuple of (action, timeslot) compatible with own partial plans
        # Don't propose anything that's in the list of rejected proposals
        raise NotImplementedError('whoops')

    def evaluate_proposal(self):
        # TODO if you reject the proposal, make sure to update your own rejections
        raise NotImplementedError('whoops')

    def update_final_plan(self):
        raise NotImplementedError('whoops')

    def update_rejections(self):
        raise NotImplementedError('whoops')

    def check_final_plan(self):
        raise NotImplementedError('whoops')



class MultiAgentNegotiation():
    """A class of agents communicating to develop a common plan"""

    def __init__(self,name):
        self.__name__ = name
        self.agents = []
    
    def add_agent(self,agent):
        self.agents.append(agent)

    def add_agents(self, agents):
        # appends a list of agents to the existing list
        self.agents += agents

    def find_resolution(self):
        all_agents_happy = True

        for agent in self.agents:
            happy = agent.check_final_plan()
            if not happy:
                all_agents_happy = False

        while not all_agents_happy:
            # agents play rock-paper-scissors to see who talks first

            # TODO pick a random agent from the list
            if self.agents[0].generate_random_number() < self.agents[1].generate_random_number():
                a0 = self.agents[0]
                a1 = self.agents[1]
            else:
                a0 = self.agents[1]
                a1 = self.agents[0]
            
            (action, timeslot) = a0.make_proposal() 
            #an Action is a combination of: (1) an agent, (2) a tuple with a operator name and some arguments
            evaluation = a1.evaluate_proposal(action,timeslot)

            if evaluation == True:
                # both agents agree
                a0.update_final_plan(action,timeslot)
                a1.update_final_plan(action,timeslot)
            else:
                # a1 has rejected the proposal
                a0.update_rejections(action,timeslot)

            a0_happy = a0.check_final_plan()
            a1_happy = a1.check_final_plan()
        
        return self.agents[0].final_plan