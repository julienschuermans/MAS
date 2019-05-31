
import multiprocessing
from ma_htn import *


logging.basicConfig(level=logging.INFO)

##### TEST problems

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
colours_list = ['red','yellow','blue']

SELECTED_EXPERIMENT = 1

def run(experiment_id):

    if experiment_id == 1:
        ##### EXPERIMENT 1
        """Test to see what happens when agents have limited capabilities. (e.g. swap-only agents)"""

        path_to_results = './experiment' + str(experiment_id) + '/normal/'
        path_to_results_constrained = './experiment' + str(experiment_id) + '/constrained/'

        write_csv_header(path_to_results)
        write_csv_header(path_to_results_constrained)

        nb_agents = 5
        nb_blocks = 20
        nb_trials = 10

        state, goal = generate_solvable_problem(nb_blocks)
        tasks = [('move_blocks', goal)]

        # no limitations
        action_limitations = [ [] for i in range(nb_agents) ]
        run_experiment(path_to_results,state,tasks,action_limitations, nb_blocks, nb_trials, colours_list)

        # handicapped agents
        action_limitations[1] = ['swap']
        action_limitations[0] = ['unstack']
        run_experiment(path_to_results_constrained,state,tasks,action_limitations, nb_blocks, nb_trials, colours_list)

    elif experiment_id == 2:
        ##### EXPERIMENT 2
        """Test to see how the planning algorithm performs in function of the number of agents."""

        path_to_results = './experiment' + str(experiment_id) + '/'
        write_csv_header(path_to_results)

        nb_blocks = 20
        nb_trials = 5

        state, goal = generate_solvable_problem(nb_blocks)
        tasks = [('move_blocks', goal)]

        def experiment_wrapper(nb_agents):
            action_limitations = [ [] for i in range(nb_agents) ]
            run_experiment(path_to_results,state,tasks,action_limitations,nb_blocks,nb_trials,colours_list)
            return 0

        pool = multiprocessing.Pool(4)
        out = zip(pool.map(experiment_wrapper, range(2, 9))) #iterate over nb agents in parallel

    elif experiment_id == 3:
        ##### EXPERIMENT 3
        """
        Test to see how consistent our problem-generating code is.
        If you select a fixed number of blocks and generate N problems,
        how does the diffulty of the problems vary?
        """

        path_to_results = './experiment' + str(experiment_id) + '/'
        write_csv_header(path_to_results)

        nb_agents = 5
        nb_trials = 5

        action_limitations = [ [] for i in range(nb_agents) ]

        def experiment_wrapper(nb_blocks):
            state, goal = generate_solvable_problem(nb_blocks)
            tasks = [('move_blocks', goal)]
            run_experiment(path_to_results,state,tasks,action_limitations,nb_blocks,nb_trials,colours_list)
            return 0

        pool = multiprocessing.Pool(4)
        out = zip(pool.map(experiment_wrapper, [10]*10)) #perform 10 experiments with 10 blocks in parallel


run(SELECTED_EXPERIMENT)
