from pyhop import *
from blocks_world_tools import Action, StateSimulation, copyallHoldingVariables

import random, logging

class Agent():
    """An agent planning to act in a (multi-agent) blocks world."""

    def __init__(self,name):
        self.__name__ = name
        self.possible_actions = None
        self.observed_state = None
        self.goal_state = None
        self.partial_plan = None
        self.final_plan = {}
        self.scheduled_actions = [] # a list the same size as partial_plan, indicating which actions have been scheduled in the final_plan already 
        self.rejections = {}

    def observe(self,state):
        self.observed_state = state
    
    def assign_actions(self,actions):
        # an agent may be restricted to perform a subset of all possible actions
        self.possible_actions = actions

    def plan(self,tasks):
        self.goal_state = tasks[0][1] #TODO expand to list with multiple tasks
        self.partial_plan = pyhop(self.observed_state,tasks,self.__name__,verbose=0)
        assert self.partial_plan != False
        self.scheduled_actions = [False] * len(self.partial_plan)

    def evaluate_dependencies(self, action, timeslot):
        # process self.partial_plan to detect dependencies between actions
        # some actions **have** to be performed before others.
        # This means that when you evaluate action X, all subsequent actions should still
        # be possible.

        # access to 'final_plan' = schedule agreed upon by all agents until now

        # calculate 'current simulated state' = apply state simulation updates of all
        # steps in the final_plan to the initial state. This is guaranteed to be a valid state,
        # that does not conflict with any agents' partial plans.

        sim = StateSimulation(self.observed_state) # start from the initial state

        for step in range(timeslot): #execute all actions with t<timeslot that have already been agreed upon
            if step in self.final_plan.keys():
                if len(self.final_plan[step]) == 1: #only 1 action at this step
                    sim.update(self.final_plan[step][0])
                elif len(self.final_plan[step]) > 1: # multiple in parallel
                    sim.update_parallel(self.final_plan[step])
                else:
                    raise RuntimeError("This should not happen. something's wrong. No actions planned at step: " + str(step))

        # to check if applying this specific Action(agent, action_tuple) leads to dependency problems
        # with the agent's partial plans, it performs a simulation to see whether all following actions
        # remain possible. All following actions are independent if their preconditions can still be met.

        # apply action currently under investigation at t=timeslot
        if timeslot in self.final_plan.keys():
            try:
                # perform the new action in parallel with those already scheduled
                sim.update_parallel(self.final_plan[timeslot] + [action])
            except RuntimeError as e:
                print(e)
                return False
        else:
            try:
                sim.update(action)
            except RuntimeError as e:
                print(e)
                return False

        # apply all other actions with t>timeslot that were already in the final_plan.
        # if any of them return false, the insertion of the proposed action has ruined some dependency.
        if len(self.final_plan.keys()) > 0:
            for step in range(timeslot+1, max(self.final_plan.keys())+1):
                if step in self.final_plan.keys():
                    if len(self.final_plan[step]) == 1: #only 1 action at this step
                        try:
                            sim.update(self.final_plan[step][0])
                        except RuntimeError as e:
                            print(e)
                            return False
                    elif len(self.final_plan[step]) > 1:  # multiple in parallel
                        try:
                            sim.update_parallel(self.final_plan[step])
                        except RuntimeError as e:
                            print(e)
                            return False
                    else:
                        raise RuntimeError("This should not happen. something's wrong. No actions planned at step: " + str(step))


        # Apply all other actions from this agents' partial_plan in series. (TODO: does this assumption make sense?)
        # If any update returns false, the proposed action has ruined some dependencies.
        virtualAgent = Agent('virtualagent')
        sim.state.holding['virtualagent'] = copyallHoldingVariables(sim.state)
        for index in range(len(self.partial_plan)):
            action_tuple = self.partial_plan[index]
            # only check actions in partial plan that have not been scheduled yet
            # also, don't simulate an action if it's equal to the one that has been proposed
            if not self.scheduled_actions[index] and not (action.operator==self.partial_plan[index][0] and action.arguments==self.partial_plan[index][1:]):
                try:
                    print("simulating: " + str(action_tuple))
                    # pretend that all these actions are performed in series by a single agent.
                    # ok when different agents can stack/unstack

                    sim.update(Action(virtualAgent,action_tuple)) #TODO dont simulate 'self' executing the action, but use a more general VirtualAgent who has access to all Real Agents' capabilties
                except RuntimeError as e:
                    print(e)
                    return False
        if action.agent != self:
            # don't print this info when an agent uses evaluate_dependencies() as a part of make_proposal
           logging.info(str(action) + ' at time ' + str(timeslot) + ' does not violate dependencies of agent ' + self.__name__)
        
        return True

    def evaluate_conflicts(self, action, timeslot):
        # some actions can not be processed concurrently.
        # For now, only checks that all arguments/objects in 2 concurrent actions are different.

        # some actions produce effects that make future actions impossible ==> TODO: I don't even look at this.

        if timeslot in self.final_plan.keys():
            for a in self.final_plan[timeslot]: # all actions that have been planned at t=timeslot
                for arg in action.arguments:
                    if arg in a.arguments: # if both actions operate on the same objects, there's a conflict. 
                        return False
        return True

    def generate_random_number(self):
        return random.random()

    def make_proposal(self):
        # Returns a tuple of (action, timeslot).
        # Don't propose anything that's in the list of rejected proposals.
        # Don't propose anything that conflicts with the 'final_plan' as agreed upon until now.
        # Don't propose anything that ruins the dependencies of other actions in this agent's partial plan.
        # Don't propose an action in a timeslot where this agent already performs another task.

        if self.final_plan == {}:
            # first agent to make a proposal = easy
            # just propose to execute your first action in the first timeslot
            # TODO: is this always the best strategy?
            action = Action(self,self.partial_plan[0])
            t = 0
            proposal = (action, t)
            logging.debug("new proposal: " + str(action) + ' at time ' + str(t))
            return proposal
        else:

            proposal_impossible = False
            t = 0
            while not proposal_impossible:#try 10 successive timestamps to fit the action in the final plan, otherwise continue
                for index in range(len(self.scheduled_actions)): ## try all unscheduled actions in partial plan from left to right
                    if self.scheduled_actions[index]==True:
                        # action has already been scheduled
                        logging.debug('action has already been scheduled')
                        continue
                
                    action = Action(self,self.partial_plan[index])
                    logging.debug('trying at t=' + str(t) + ',' + str(action))
                    agentAlreadyHasTaskatTimeT = False
                    if t in self.final_plan.keys():
                        for planned_action in self.final_plan[t]:
                            if planned_action.agent == self:
                                logging.debug('agent already has a task')
                                agentAlreadyHasTaskatTimeT = True
                                break
                    if not agentAlreadyHasTaskatTimeT:
                        if not self.evaluate_conflicts(action,t):
                            logging.debug('action in conflict with another one')
                        elif not self.evaluate_dependencies(action,t):
                            logging.debug('action destroys dependencies')
                        elif t in self.rejections.keys() and (action.operator,action.arguments) in self.rejections[t]:
                            print(self.rejections)
                            logging.debug('action has been rejected previously')                    
                        else:
                            proposal = (action, t) # found an action, timestamp combo that does not conflict with any of the agent's goals
                            logging.debug("new proposal: " + str(action) + ' at time ' + str(t))
                            return proposal
                t+=1
                if t>10:
                    proposal_impossible = True
        return None # TODO is this a good way to signal that the agent is happy/has no more tasks to complete?
        # What if the agent is unhappy, but is still not able to propose any action/timeslot-combinations?
        

    def evaluate_proposal(self, action, timeslot):
        conflicts_ok = self.evaluate_conflicts(action,timeslot)
        dependencies_ok = self.evaluate_dependencies(action, timeslot)        
        return conflicts_ok and dependencies_ok

    def update_final_plan(self, action, timeslot):

        logging.info("add to final plan: t=" + str(timeslot) + ',' + str(action) )

        if timeslot not in self.final_plan.keys():
            self.final_plan[timeslot] = [action]
        else:
            self.final_plan[timeslot].append(action)

        for i in range(len(self.partial_plan)):
            a = self.partial_plan[i]
            if a[0] == action.operator and a[1:]==action.arguments:
                self.scheduled_actions[i] = True

    def print_final_plan(self):
        for step in sorted(self.final_plan.keys()):
            print(str(step) + ': %s' % [str(action) for action in self.final_plan[step]])

    def update_rejections(self, action, timeslot):
        if timeslot not in self.rejections.keys():
            self.rejections[timeslot] = [(action.operator,action.arguments)] #TODO rejections should include action.agent.__name__
        else:
            self.rejections[timeslot].append((action.operator,action.arguments))

    def check_final_plan(self):
        # #TODO check if this works

        sim = StateSimulation(self.observed_state) # start from the initial state
        for step in sorted(self.final_plan.keys()): #execute all actions that have been agreed upon
            if len(self.final_plan[step]) == 1: #only 1 action at this step
                sim.update(self.final_plan[step][0])
            elif len(self.final_plan[step]) > 1: # multiple in parallel
                sim.update_parallel(self.final_plan[step])
        

        print(self.goal_state.__dict__)
        print(sim.state.__dict__)

        for key,value in self.goal_state.__dict__.items():
            if key != '__name__':
                for key2, value2 in self.goal_state.__dict__[key].items():
                    print(value2, sim.state.__dict__[key][key2])
                    if value2 != sim.state.__dict__[key][key2]:
                        return False

        print('I am happy!')
        return True


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
            print('check happy')
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
            
            proposal = a0.make_proposal()
            if proposal == None:
                #return self.agents[0].final_plan
                continue
                # you should 'continue' here, e.g. ask for proposals from other agents
                # until they're all happy
            else:
                # an Action is a combination of: 
                    #   (1) an agent, 
                    #   (2) a tuple with an operator and some arguments
                (action, timeslot) = proposal
            
            # TODO extend to multiple agents. Everyone has to agree to the proposal.
            evaluation = a1.evaluate_proposal(action,timeslot)
            if evaluation:
                logging.debug(a1.__name__ + " has accepted the proposal")
            else:
                logging.debug(a1.__name__ + " has rejected the proposal")

            if evaluation == True:
                # all agents agree
                a0.update_final_plan(action,timeslot)
                a1.update_final_plan(action,timeslot)
            else:
                # a1 has rejected the proposal
                a0.update_rejections(action,timeslot)
                a1.update_rejections(action,timeslot)

            all_agents_happy = True
            for agent in self.agents:
                print('happy?')
                happy = agent.check_final_plan()
                if not happy:
                    all_agents_happy = False
        print("Everyone is happy!")
        return self.agents[0].final_plan