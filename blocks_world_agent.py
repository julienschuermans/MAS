from pyhop import *
from blocks_world_tools import Action, StateSimulation, copyallHoldingVariables

import random, logging, time

class Agent():
    """An agent planning to act in a (multi-agent) blocks world."""

    def __init__(self,name):
        self.__name__ = name
        self.restricted_actions = None
        self.observed_state = None
        self.goal_state = None
        self.partial_plan = None        # single-agent plan returned by pyhop
        self.final_plan = {}            # schedule agreed upon by all agents until now
        self.scheduled_actions = []     # a list the same size as partial_plan, indicating which actions have been scheduled in the final_plan already
        self.rejections = {}            # dictionary mapping timeslots to rejected Actions
        self.planning_horizon = 50
        #TODO planning horizon recht evenredig met problemsize/nb_agents ?

    def reset(self):
        self.final_plan = {}
        self.scheduled_actions = [False] * len(self.partial_plan)
        self.rejections = {}

    def get_name(self):
        return self.__name__

    def observe(self,state, colour_dict={}):
        self.observed_state = state
        self.colour_dict = colour_dict

    def assign_actions(self,actions):
        # an agent may be restricted to perform a subset of all possible actions
        self.restricted_actions = actions

    def plan(self,tasks):
        self.goal_state = tasks[0][1]
        self.partial_plan = pyhop(self.observed_state,tasks,self.get_name(),verbose=0)
        assert self.partial_plan != False #pyhop should never fail
        self.scheduled_actions = [False] * len(self.partial_plan)

    def evaluate_dependencies(self, action, timeslot):
        # process self.partial_plan to detect dependencies between actions
        # some actions **have** to be performed before others.
        # This means that when you evaluate action X, all subsequent actions should still
        # be possible.

        # (1) calculate 'current simulated state' = apply state simulation updates of all
        # steps in the final_plan to the initial state. This is guaranteed to be a valid state,
        # that does not conflict with any agents' partial plans.

        sim = StateSimulation(self.observed_state) # start from the initial state

        for step in range(timeslot): #execute all actions with t<timeslot that have already been agreed upon
            if step in self.final_plan.keys():
                if len(self.final_plan[step]) == 1: #only 1 action at this step
                    # logging.debug('simulating ' + str(self.final_plan[step][0]))
                    sim.update(self.final_plan[step][0])
                elif len(self.final_plan[step]) > 1: # multiple in parallel
                    # logging.debug('simulating ' + str([str(x) for  x in self.final_plan[step]]))
                    sim.update_parallel(self.final_plan[step])
                else:
                    raise RuntimeError("This should not happen. something's wrong. No actions planned at step: " + str(step))

        # (2) to check if applying this specific Action(agent, action_tuple) leads to dependency problems
        # with the agent's partial plans, it performs a simulation to see whether all following actions
        # remain possible. All following actions are independent if their preconditions can still be met.

        # apply action currently under investigation at t=timeslot
        if timeslot in self.final_plan.keys():
            try:
                # logging.debug('simulating ' + str(self.final_plan[timeslot][0]) + ' and ' + str(action))

                # perform the new action in parallel with those already scheduled
                sim.update_parallel(self.final_plan[timeslot] + [action])
            except RuntimeError:
                # logging.debug('dependency violated in step 2a')
                return False
        else:
            try:
                # logging.debug('simulating ' + str(action))
                sim.update(action)
            except RuntimeError:
                # logging.debug('dependency violated in step 2b')
                return False

        # (3) apply all other actions with t>timeslot that were already in the final_plan.
        # if any of them return false, the insertion of the proposed action has ruined some dependency.
        if len(self.final_plan.keys()) > 0:
            for step in range(timeslot+1, max(self.final_plan.keys())+1):
                if step in self.final_plan.keys():
                    if len(self.final_plan[step]) == 1: #only 1 action at this step
                        # logging.debug('simulating ' + str(self.final_plan[step][0]))
                        try:
                            sim.update(self.final_plan[step][0])
                        except RuntimeError:
                            # logging.debug('dependency violated in step 3a')
                            return False
                    elif len(self.final_plan[step]) > 1:  # multiple in parallel
                        # logging.debug('simulating ' + [str(x) for  x in self.final_plan[step]])
                        try:
                            sim.update_parallel(self.final_plan[step])
                        except RuntimeError:
                            # logging.debug('dependency violated in step 3b')
                            return False
                    else:
                        raise RuntimeError("This should not happen. something's wrong. No actions planned at step: " + str(step))


        # (4) Apply all other actions from this agents' partial_plan in series.
        # If any update returns false, the proposed action has ruined some dependencies.
        virtualAgent = Agent('virtualagent')
        sim.state.holding['virtualagent'] = copyallHoldingVariables(sim.state)

        action_encountered_before = False

        for index in range(len(self.partial_plan)):
            action_tuple = self.partial_plan[index]
            # only check actions in partial plan that have not been scheduled yet
            # also, don't simulate an action if it's the same one that has been proposed
            # take special care when the same action appears multiple times in the (partial) plan!

            action_not_scheduled = not self.scheduled_actions[index]
            action_equal_to_proposal = False

            if action_not_scheduled:
                if action_encountered_before and (action.operator==self.partial_plan[index][0] and action.arguments==self.partial_plan[index][1:]):
                    action_equal_to_proposal = False #not the same since youve encountered it before
                else:
                    if (action.operator==self.partial_plan[index][0] and action.arguments==self.partial_plan[index][1:]):
                        action_equal_to_proposal = True
                        action_encountered_before = True
                    else:
                        action_equal_to_proposal = False

            if action_not_scheduled and not action_equal_to_proposal:
                # logging.debug('simulating ' + str(action_tuple))
                try:
                    # pretend that all these actions are performed in series by a single agent.
                    # in principle ok that different agents might stack/unstack (this is just a simulation)
                    sim.update(Action(virtualAgent,action_tuple))
                except RuntimeError:
                    # logging.debug('dependency violated in step 4 during simulation of ' + str(action_tuple))
                    return False
            else:
                pass
                # logging.debug('not simulating ' + str(action_tuple))

        if action.agent != self:
            # don't print this info when an agent uses evaluate_dependencies() as a part of make_proposal
           logging.debug(str(action) + ' at time ' + str(timeslot) + ' does not violate dependencies of agent ' + self.get_name())

        return True

    def evaluate_conflicts(self, action, timeslot):
        # some actions can not be processed concurrently.
        # This function checks that all arguments/objects in 2 concurrent actions are different.

        if timeslot in self.final_plan.keys():
            for a in self.final_plan[timeslot]: # all actions that have been planned at t=timeslot
                for arg in action.arguments:
                    if arg in a.arguments: # if both actions operate on the same objects, there's a conflict.
                        return False

        return True #true is a positive evaluation: there are no conflicts

    def make_proposal(self):
        # Returns a tuple of (action, timeslot).
        # Don't prosope an action that has already been scheduled
        # Don't propose anything that's in the list of rejected proposals.
        # Don't propose anything that conflicts with the 'final_plan' as agreed upon until now.
        # Don't propose anything that ruins the dependencies of other actions in this agent's partial plan.
        # Don't propose an action in a timeslot where this agent already performs another task.

        if self.partial_plan == []:
            return None

        if self.final_plan == {}:
            # first agent to make a proposal = easy:
            # just propose to execute your first action in the first timeslot
            action = False

            for index in range(len(self.scheduled_actions)):
                # print(str(self.partial_plan[index][0]), self.restricted_actions)
                if str(self.partial_plan[index][0]) in self.restricted_actions:
                    logging.debug('agent cannot execute this action')
                    continue

                elif self.colour_dict != {}:
                    if self.colour_dict[self.partial_plan[index][1]] in self.restricted_actions:
                        logging.debug('agent cannot handle blocks with the colour'+ str(self.colour_dict[self.partial_plan[index][1]]))
                        continue
                    else:
                        action = Action(self,self.partial_plan[index])
                        break

                else:
                    action = Action(self,self.partial_plan[index])
                    break

            if not action:
                return None
                    # TO DO: what if all actions of partial plan are restricted?

            t = 0
            if not self.evaluate_conflicts(action,t):
                logging.debug('action in conflict with another one')
            elif t in self.rejections.keys() and action in self.rejections[t]:
                logging.debug('action has been rejected previously')
            elif not self.evaluate_dependencies(action,t):
                logging.debug('action destroys dependencies')
            else:
                proposal = (action, t) # found an action, timestamp combo that does not conflict with any of the agent's goals
                logging.debug("new proposal: " + str(action) + ' at time ' + str(t))
                return proposal

        else:

            proposal_impossible = False
            t = 0
            while not proposal_impossible: #try successive timestamps to fit an action in the final plan
                for index in range(len(self.scheduled_actions)): ## select an unscheduled action in the partial plan from left to right
                    if self.scheduled_actions[index]==True:
                        logging.debug('action has already been scheduled')
                        continue

                    if t > max(self.final_plan.keys()) + 4: #only consider actions close to end of current final plan
                        break #TODO how to tune this parameter?

                    # print(str(self.partial_plan[index][0]), self.restricted_actions)
                    if str(self.partial_plan[index][0]) in self.restricted_actions:
                        logging.debug('agent cannot execute this action')
                        continue

                    elif self.colour_dict != {}:
                        if self.colour_dict[self.partial_plan[index][1]] in self.restricted_actions:
                            logging.debug('agent cannot handle blocks with the colour'+ str(self.colour_dict[self.partial_plan[index][1]]))
                            continue

                        else:
                            action = Action(self,self.partial_plan[index])

                    else:
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
                        elif t in self.rejections.keys() and action in self.rejections[t]:
                            logging.debug('action has been rejected previously')
                        elif not self.evaluate_dependencies(action,t):
                            logging.debug('action destroys dependencies')
                        else:
                            proposal = (action, t) # found an action, timestamp combo that does not conflict with any of the agent's goals
                            logging.debug("new proposal: " + str(action) + ' at time ' + str(t))
                            return proposal
                    else:
                        break #if the agent already has a task at time t, he doesnt need to check the other actions at the same timestep
                t+=1
                if t>self.planning_horizon:
                    proposal_impossible = True

        return None # a signal that the agent is happy/has no more tasks to complete


    def evaluate_proposal(self, action, timeslot):
        conflicts_ok = self.evaluate_conflicts(action,timeslot)
        dependencies_ok = self.evaluate_dependencies(action, timeslot)
        return conflicts_ok and dependencies_ok

    def update_final_plan(self, action, timeslot):

        logging.debug("add to final plan: t=" + str(timeslot) + ',' + str(action) )

        if timeslot not in self.final_plan.keys():
            self.final_plan[timeslot] = [action]
        else:
            self.final_plan[timeslot].append(action)

        for i in range(len(self.partial_plan)):
            a = self.partial_plan[i]

            # only set the first unscheduled action to 'scheduled'
            if not self.scheduled_actions[i] and a[0] == action.operator and a[1:]==action.arguments:
                self.scheduled_actions[i] = True
                break

    def print_final_plan(self):
        for step in sorted(self.final_plan.keys()):
            print(str(step) + ': %s' % [str(action) for action in self.final_plan[step]])

    def update_rejections(self, action, timeslot):
        if timeslot not in self.rejections.keys():
            self.rejections[timeslot] = [action] # rejections is combination of agent and
        else:
            self.rejections[timeslot].append(action)

    def check_final_plan(self):
        sim = StateSimulation(self.observed_state) # start from the initial state
        for step in sorted(self.final_plan.keys()): #execute all actions that have been agreed upon
            if len(self.final_plan[step]) == 1: #only 1 action at this step
                sim.update(self.final_plan[step][0])
            elif len(self.final_plan[step]) > 1: # multiple in parallel
                sim.update_parallel(self.final_plan[step])

        for key in self.goal_state.__dict__.keys():
            if key != '__name__' and key != 'clear': # only care about the position of blocks !
                for key2, value2 in self.goal_state.__dict__[key].items():
                    if value2 != sim.state.__dict__[key][key2]:
                        return False

        return True


class MultiAgentNegotiation():
    """A class of agents communicating to develop a common plan"""

    def __init__(self,name):
        self.__name__ = name
        self.agents = []
        self.silent_agents = []

    def add_agent(self,agent):
        self.agents.append(agent)

    def add_agents(self, agents):
        # appends a list of agents to the existing list
        self.agents += agents


    def find_resolution(self):
        logging.info('Starting communications...')

        all_agents_happy = True

        last_x_chosen_ones = []
        nb_times_fail = 0
        everyone_chosen = 0

        for agent in self.agents:
            happy = agent.check_final_plan()
            if not happy:
                all_agents_happy = False

        while not all_agents_happy:

            if nb_times_fail > 5*len(self.agents):
                # the problem is unsolvable, can be the case when the constraints are too restrictive
                for agent in self.agents:
                    if agent.get_name() in last_x_chosen_ones[-5*len(self.agents):]:
                        everyone_chosen+=1
                if everyone_chosen==len(self.agents):
                    # exiting the loop when too many iterations "None" is returned as proposal, 
                    # and every agent has made a proposal at least once in the last 5*nb_agents steps
                    logging.info('No solution is found')
                    return None     # if you want to see which blocks can't be moved anymore: return self.agents[0].final_plan
            #  pick a random agent from the list
            the_chosen_one = random.choice(self.agents)
            last_x_chosen_ones.append(the_chosen_one.get_name())
            proposal = the_chosen_one.make_proposal()

            # Does the chosen one have a proposal? if not, pick another agent
            if proposal == None:
                nb_times_fail+=1
                continue
            else:
                (action, timeslot) = proposal

            # Everyone else has to agree to the proposal.
            for current_agent in self.agents:
                if current_agent.get_name() != the_chosen_one.get_name():
                    evaluation = current_agent.evaluate_proposal(action,timeslot)

                    if evaluation:
                        logging.debug(current_agent.get_name() + " has accepted the proposal")
                    else:
                        logging.debug(current_agent.get_name() + " has rejected the proposal")
                        break #one of the agents has disagreed. no reason to check the others.

            if evaluation == True:
                nb_times_fail = 0
                # all agents agree, add it to their final plans
                for agent in self.agents:
                    agent.update_final_plan(action,timeslot)
            else:
                # nb_times_fail +=1
                # some agent has rejected the proposal
                for agent in self.agents:
                    agent.update_rejections(action,timeslot)


            # if all agents are happy with the current plan, we can exit the while loop
            all_agents_happy = True
            for agent in self.agents:
                happy = agent.check_final_plan()
                if not happy:
                    all_agents_happy = False

        if all_agents_happy:
            logging.info('All agents agree on the plan.')
            return self.agents[0].final_plan
        else:
            logging.warning("No multi-agent plan possible.")
            return None
