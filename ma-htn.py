from __future__ import print_function
from pyhop import *

import logging, time, csv, os

import numpy as np

import blocks_world_operators
import blocks_world_methods

from blocks_world_agent import Agent, MultiAgentNegotiation

logging.basicConfig(level=logging.INFO)

# state specification
state1 = State('state1')
state1.pos={'a':'c', 'b':'d', 'c':'table', 'd':'table'}
state1.clear={'a':True, 'c':False,'b':True, 'd':False}
state1.holding={}

# goal specification
goal1 = Goal('goal1')
goal1.pos={'b':'c', 'a':'d'}

# task specification
tasks1 = [('move_blocks', goal1)]

# state specification
state3 = State('state3')
state3.pos = {1:12, 12:13, 13:'table', 11:10, 10:5, 5:4, 4:14, 14:15, 15:'table', 9:8, 8:7, 7:6, 6:'table', 19:18, 18:17, 17:16, 16:3, 3:2, 2:'table'}
state3.clear = {x:False for x in range(1,20)}
state3.clear.update({1:True, 11:True, 9:True, 19:True})
state3.holding = {}

# goal specification
goal3 = Goal('goal3')
goal3.pos = {15:13, 13:8, 8:9, 9:4, 4:'table', 12:2, 2:3, 3:16, 16:11, 11:7, 7:6, 6:'table'}
goal3.clear = {17:True, 15:True, 12:True}

# task specification
tasks3 = [('move_blocks', goal3)]

def print_plan(plan):
    for t,steps in plan.items():
        print('t=' + str(t))
        for action in steps:
            print(action)

def run_experiment(path_to_csv, state,tasks,nb_agents=2,nb_trials=1):
    """
    computes metrics, averaging over nb_trials
    writes a single new line with all results to the given csv file
    """

    # agent initialisation
    agents = {} # dictionary of names mapping to Agent() objects

    for i in range(nb_agents):
        name = 'A'+str(i)
        agents[name] = Agent(name)
        state.holding[name] = False #by default, in the beginning, an agent isn't holding anything

    for agent in agents.values():
        agent.observe(state) #what happens when agents don't observe everything?
        agent.plan(tasks) #use pyphop to generate a personal plan

    single_agent_plan_length = len(agents['A0'].partial_plan)
    # logging.info("single agent plan length: " + '{:d}'.format(single_agent_plan_length))

    # agents communicate to resolve dependencies/conflicts and assign tasks
    comms = MultiAgentNegotiation('test')
    comms.add_agents(agents.values())


    # setup lists for averaging
    time_measurements = []
    plan_lengths = []

    for trial in range(nb_trials):

        for agent in agents.values(): # wipes the results from the previous run
            agent.reset()

        start = time.time()
        plan = comms.find_resolution()
        stop = time.time()
        time_measurements.append(stop-start)

        if plan is not None:
            plan_lengths.append(len(plan))
        else:
            logging.info('trial ' + str(trial) + ' did not find a solution')

    with open(path_to_csv, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow( \
            ['20'] \
            + [str(single_agent_plan_length)] \
            + [str(nb_agents)] \
            + [str(nb_trials)] \
            + ['{:.4f}'.format(np.min(time_measurements))] \
            + ['{:.4f}'.format(np.max(time_measurements))] \
            + ['{:.4f}'.format(np.mean(time_measurements))] \
            + ['{:.0f}'.format(np.ceil(np.min(plan_lengths)))] \
            + ['{:.0f}'.format(np.ceil(np.max(plan_lengths)))] \
            + ['{:.0f}'.format(np.ceil(np.mean(plan_lengths)))] \
            + ['{:.4f}'.format(single_agent_plan_length/np.ceil(np.mean(plan_lengths)))] \
            + ['{:.4f}'.format(single_agent_plan_length/(np.ceil(np.mean(plan_lengths))*nb_agents))] \
            )


##### start experiments here

path_to_csv = './results.csv'
with open(path_to_csv, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow( \
    ['problem size', \
    'single agent plan length', \
    '#agents', \
    '#trials', \
    'min time', \
    'max time', \
    'avg time', \
    'min length', \
    'max length', \
    'avg length', \
    'avg compression', \
    'avg plan density'])


for i in range(2,20,2):
    logging.info("number of agents: " + str(i))
    run_experiment(path_to_csv,state3,tasks3,nb_agents=i,nb_trials=10)

##### TODO #####
#
# 000) fix all remaining stuff in the current code
    # => DONE
#
# 00) evaluate timing: why does resolution take very long sometimes
#       - are there easy fixes for this?
#       - something related to rejected_proposals? NO
    # => DONE:

    # INFO:root:make_proposal 14.6518 sec
    # INFO:root:evaluate_proposal 0.9802 sec
    # INFO:root:update plan 0.0038 sec
    # INFO:root:check plan 0.5286 sec

    #   ==> agents spend lots of time in make_proposal:
    #   nested loops: O(len(partial_plan)*planning_horizon)
    #       - decrease planning_horizon? too small, might not find a solution
    #       - early exit from the loop?
    #           - got a quick implementation working

# 0) run_n_trials --> compute average time, solution quality
    # => DONE (mostly)
        #TODO extract best plan

# 1) LAURANE: specialised agents
#       - limit actions of a certain agent
#       - don't care at all in partial plan
#       - only extra constraints in make_proposal
#
# 2) JULIEN: easily scale to larger problems.
# generate a 10/100/1000-burger initial state and corresponding goals
#
# 3) agents that do not observe the full state
#
#
# 4) plan_pruning: deterministic method that all agents can apply independently.
#       - eliminate redundant putdown/pickup
#       - other inefficiencies?
#
#
# 5) smart agent order instead of random (round robin?)

# 6) detect & escape infinite loops in find_resolution
#   when every agent has proposed None?
    # ==> I've tried this and the constraint is too harsh
    # it is possible too find a plan when all agents have proposed None once:
    # 2-agent example:
        # agent 0 proposes None
        # agent 1 proposes an action
        # agent 0 proposes an action
        # agent 1 proposes None --> at this point both agents have proposed None, but there is no need to exit the while loop!
        # agent 0 proposes an action
