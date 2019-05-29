from __future__ import print_function
from pyhop import *

import logging, time, csv, os, random
from string import ascii_lowercase
import numpy as np

import blocks_world_operators
import blocks_world_methods
import blocks_world_tools as bwt

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

    for j in range(nb_fixed_blocks):
        i = shuffled_blocks[j]
        if random.randint(1,nb_fixed_blocks) < random.random()*nb_fixed_blocks:
            goal.pos[i] = 'table'
        else:

            def check(block,candidate):
                if block == candidate:
                    return False
                elif candidate in goal.pos.keys():
                    return check(block,goal.pos[candidate]) #check the block under the candidate
                else:
                    return True # the candidate is free

            potential_destinations = list(set([k for k in shuffled_blocks if check(i,k)]) - set(goal.pos.values()))
            if len(potential_destinations) > 0:
                dest = random.choice(potential_destinations)
                goal.pos[i] = dest

    # potentially_clear_blocks = list(set([i for i in range(1,nb_blocks+1)]) - set(goal.pos.values()))
    # random.shuffle(potentially_clear_blocks)
    #
    # nb_clear_blocks = random.randint(0,len(potentially_clear_blocks))
    goal.clear = {x:True for x in list(set(goal.pos.keys())-set(goal.pos.values()))}

    return goal

def generate_problem(nb_blocks):
    return generate_state(nb_blocks), generate_goal(nb_blocks)


def generate_solvable_problem(nb_blocks):
    # make sure that the generated problem can be solved by a single agent
    # our assumption = pyhop can solve the block stacking task alone

    state, goal = generate_problem(nb_blocks=nb_blocks)
    print_state(state)
    print_goal(goal)
    tasks = [('move_blocks', goal)]
    canBeSolvedByPyhop = False

    while not canBeSolvedByPyhop:
        try:
            state.holding['dummy_agent'] = False
            single_agent_plan = pyhop(state,[('move_blocks', goal)],'dummy_agent')
            if single_agent_plan != False:
                print('good plan')
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
        # print_plan(best_plan)


##### start experiments here

path_to_results = './results.csv'
path_to_best_plan = './best_plan.csv'

# write the column headers in the csv with metrics
with open(path_to_results, 'w', newline='') as csvfile:
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

path_to_results_constraints = './results_constraints.csv'
path_to_best_plan_constraints = './best_plan_constraints.csv'

# write the column headers in the csv with metrics
with open(path_to_results_constraints, 'w', newline='') as csvfile:
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

nb_agents = 10
action_limitations = [ [] for i in range(nb_agents) ]
print(action_limitations)

nb_blocks = 80
nb_trials = 1

state, goal = generate_solvable_problem(nb_blocks)
tasks = [('move_blocks', goal)]

print_state(state)
print_goal(goal)
# 
run_experiment(path_to_results,path_to_best_plan,state,tasks,action_limitations, nb_blocks, nb_trials)

action_limitations[1] = ['swap']
action_limitations[0] = ['unstack']
run_experiment(path_to_results_constraints,path_to_best_plan_constraints,state,tasks,action_limitations, nb_blocks, nb_trials)


# name = 'agent'
# generated_state = State('state')
# generated_state.pos = {3: 'table', 1: 3, 2: 1}
# generated_state.clear = {1: False, 2: True, 3: False}
# generated_state.holding = {}
# generated_state.holding[name] = False
# generated_goal = Goal('goal')
# generated_goal.pos = {1: 3, 2: 'table', 3: 2}
# generated_goal.clear = {1: True}

# task = [('move_blocks',generated_goal)]
# pyhop(generated_state,task,name,verbose=3)


# name = 'agent1'
# # state specification
# state2 = State('state2')
# state2.pos={'1':'2','2':'5', '5':'3', '3':'4', '4':'table'}
# state2.clear={'1':True, '2':False,'3':False, '4':False,'5':False}
# state2.holding={}
# state2.holding[name] = False

# # goal specification
# goal2 = Goal('goal2')
# goal2.pos={'5':'4', '2':'3','1':'table','3':'table','4':'table'}

# # task specification
# tasks2 = [('move_blocks', goal2)]

# weird_state = State('weird')
# weird_goal = Goal('weirdgoal')
# weird_state.pos = {2: 'table', 1: 'table', 3: 2, 4: 1, 5: 4}
# weird_state.clear = {1: False, 2: False, 3: True, 4: False, 5: True}
# weird_state.holding = {}
# weird_state.holding[name] = False

# weird_goal.pos = {3: 1, 5: 2}
# weird_goal.clear = {3: True, 5: True}
# tasks = [('move_blocks', weird_goal)]

# pyhop(weird_state,[('move_blocks', weird_goal)],name, verbose=3)




# for i in range(2,20,2):
#     logging.info("number of agents: " + str(i))
#     run_experiment(path_to_csv,path_to_best_plan,state3,tasks3,nb_agents=i,nb_trials=10)

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
    #           - got a quick implementation working (only look at timesteps close to end of current final_plan)

# 0) run_n_trials --> compute average time, solution quality, extract best plan
    # => DONE

# 1) LAURANE: specialised agents
#       - limit actions of a certain agent
#       - don't care at all in partial plan
#       - only extra constraints in make_proposal
    # ==> DONE
#
# 2) JULIEN: easily scale to larger problems.
#       - generate a 10/100/1000-burger initial state and corresponding goals
    # ==> DONE

#
# 3) agents that do not observe the full state
#       - can they still have a valid partial_plan ? depends on pyhop I guess
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
