from __future__ import print_function
from pyhop import *

import logging, time, csv, os, random
from string import ascii_lowercase
import numpy as np

import blocks_world_operators
import blocks_world_methods
import blocks_world_tools as bwt

from blocks_world_agent import Agent, MultiAgentNegotiation

def print_plan(plan):
    for t,steps in plan.items():
        print('t=' + str(t))
        for action in steps:
            print(action)


def save_plan(plan,nb_agents,path_to_plan):

    nb_timesteps = len(plan)

    with open(path_to_plan, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['timeslot'] + [str(i) for i in range(nb_timesteps)])

        def fill(agent_id,t):
            for action in plan[t]:
                if action.agent.get_name() == 'A' + str(agent_id):
                    return action.operator + str(action.arguments)
            return ''

        for i in range(nb_agents):
            writer.writerow(['A' + str(i)] + [fill(i,t) for t in range(nb_timesteps)])


def generate_state(nb_blocks):
    state = State('generated_state')
    state.pos = {}
    if nb_blocks > 4:
        nb_blocks_on_table = random.randint(1,nb_blocks//4) #don't put too many blocks on the table,
    else:
        nb_blocks_on_table = random.randint(1,nb_blocks)
    # it makes the generated problems rather easy to solve
    shuffled_blocks  = [i for i in range(1,nb_blocks+1)]
    random.shuffle(shuffled_blocks)

    for j in range(nb_blocks_on_table):
        i = shuffled_blocks[j]
        state.pos[i] = 'table'

    for j in range(nb_blocks_on_table, nb_blocks):
        i = shuffled_blocks[j]
        state.pos[i] = random.choice(list(set(state.pos.keys()) - set(state.pos.values()) - set([i])))

    state.clear = {x:False for x in range(1,nb_blocks+1)}

    for j in range(1,nb_blocks+1):
        if j not in state.pos.values():
            state.clear.update({j:True})
    state.holding = {}
    return state

def generate_goal(nb_blocks):
    goal = Goal('generated_goal')
    goal.pos = {}

    # nb_fixed_blocks = random.randint(1,nb_blocks)
    nb_fixed_blocks = nb_blocks
    shuffled_blocks  = [i for i in range(1,nb_blocks+1)]
    random.shuffle(shuffled_blocks)


    def check(block,candidate):
        if block == candidate:
            return False
        elif candidate in goal.pos.keys():
            return check(block,goal.pos[candidate]) #check the block under the candidate
        else:
            return True # the candidate is free

    for j in range(nb_fixed_blocks):
        i = shuffled_blocks[j]
        if random.randint(1,nb_fixed_blocks) < random.random()*nb_fixed_blocks:
            goal.pos[i] = 'table'
        else:
            potential_destinations = list(set([k for k in shuffled_blocks if check(i,k)]) - set(goal.pos.values()))
            if len(potential_destinations) > 0:
                dest = random.choice(potential_destinations)
                goal.pos[i] = dest

    goal.clear = {x:True for x in list(set(goal.pos.keys())-set(goal.pos.values()))}

    return goal


def generate_problem(nb_blocks):
    return generate_state(nb_blocks), generate_goal(nb_blocks)


def generate_solvable_problem(nb_blocks):
    # make sure that the generated problem can be solved by a single agent
    # our assumption = pyhop can solve the block stacking task alone

    state, goal = generate_problem(nb_blocks=nb_blocks)
    tasks = [('move_blocks', goal)]
    canBeSolvedByPyhop = False

    while not canBeSolvedByPyhop:
        try:
            state.holding['dummy_agent'] = False
            single_agent_plan = pyhop(state,[('move_blocks', goal)],'dummy_agent')
            if single_agent_plan != False:
                logging.debug("found a valid problem")
                state.holding = {}
                canBeSolvedByPyhop = True
            else:
                logging.debug("pyhop can't solve this, try again")
                state, goal = generate_problem(nb_blocks=nb_blocks)
                tasks = [('move_blocks', goal)]
        except:
            logging.debug("pyhop can't solve this, try again")
            state, goal = generate_problem(nb_blocks=nb_blocks)
            tasks = [('move_blocks', goal)]

    return state, goal

def write_csv_header(path):
    # write the column headers in the csv with metrics
    with open(path, 'w', newline='') as csvfile:
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

def run_experiment(path_to_csv,path_to_best_plan,state,tasks,action_limitations, nb_blocks, nb_trials=1):
    """
    computes metrics, averaging over nb_trials
    writes a single new line with all results to the given csv file
    stores the shortest plan as a csv
    """

    nb_agents = len(action_limitations)
    # agent initialisation
    agents = {} # dictionary of names mapping to Agent() objects

    for i,restricted_actions in enumerate(action_limitations):
        name = 'A'+str(i)
        agents[name] = Agent(name)
        agents[name].assign_actions(restricted_actions)
        state.holding[name] = False #by default, in the beginning, an agent isn't holding anything

    for agent in agents.values():
        agent.observe(state) #what happens when agents don't observe everything?
        agent.plan(tasks) #use pyphop to generate a personal plan

    single_agent_plan_length = len(agents['A0'].partial_plan)
    if single_agent_plan_length == 0:
        # the partial plan is an empty list: no actions required to reach goal state
        logging.warning("skipping useless experiment")
        return -1
    else:
        # agents communicate to resolve dependencies/conflicts and assign tasks
        comms = MultiAgentNegotiation('test')
        comms.add_agents(agents.values())


        # setup lists for averaging
        time_measurements = []
        plan_lengths = []

        best_plan = None

        for trial in range(nb_trials):

            for agent in agents.values(): # wipes the results from the previous run
                agent.reset()

            start = time.time()
            plan = comms.find_resolution()
            stop = time.time()
            time_measurements.append(stop-start)

            if plan is not None:
                plan_lengths.append(len(plan))
                if best_plan is None or len(plan) < len(best_plan):
                    best_plan = plan
            else:
                logging.info('trial ' + str(trial) + ' did not find a solution')


        with open(path_to_csv, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow( \
                [str(nb_blocks)] \
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

        save_plan(best_plan, nb_agents, path_to_best_plan)
        return 0
