import multiprocessing
from ma_htn import *
from itertools import product

logging.basicConfig(level=logging.ERROR)

experiment_id = 5 # to select a single experiment
RUN_ALL = False

colours_list = ['red', 'blue', 'yellow']

if experiment_id == 1 or RUN_ALL:
    if RUN_ALL:
        experiment_id = 1
    ##### EXPERIMENT 1
    """Test to see what happens when agents have limited capabilities. (e.g. swap-only agents)"""

    path_to_results = './experiment' + str(experiment_id) + '/normal/'
    path_to_results_constrained = './experiment' + str(experiment_id) + '/constrained/'

    write_csv_header(path_to_results)
    write_csv_header(path_to_results_constrained)

    nb_agents = 5
    nb_blocks = 10
    nb_trials = 5

    def experiment_wrapper(nb_blocks):
        state, goal = generate_solvable_problem(nb_blocks)
        tasks = [('move_blocks', goal)]
        action_limitations = [ [] for i in range(nb_agents) ]
        # no limitations
        run_experiment(path_to_results,state,tasks,action_limitations,nb_blocks,nb_trials,colours_list)
        # handicapped agents
        action_limitations[1] = ['swap']
        action_limitations[0] = ['unstack']
        run_experiment(path_to_results_constrained,state,tasks,action_limitations, nb_blocks, nb_trials, colours_list)

        return 0

    pool = multiprocessing.Pool(4)
    out = zip(pool.map(experiment_wrapper, [10]*10)) #perform 10 experiments with 10 blocks in parallel


if experiment_id == 2 or RUN_ALL:
    if RUN_ALL:
        experiment_id = 2
    ##### EXPERIMENT 2
    """Test to see what happens when agents have colour-limited capabilities. (e.g red-only agents)"""

    path_to_results = './experiment' + str(experiment_id) + '/normal/'
    path_to_results_constrained = './experiment' + str(experiment_id) + '/constrained/'

    write_csv_header(path_to_results)
    write_csv_header(path_to_results_constrained)

    nb_agents = 5
    nb_blocks = 10
    nb_trials = 5


    def experiment_wrapper(nb_blocks):
        state, goal = generate_solvable_problem(nb_blocks, colours_list)
        tasks = [('move_blocks', goal)]
        action_limitations = [ [] for i in range(nb_agents) ]
        # no limitations
        run_experiment(path_to_results,state,tasks,action_limitations,nb_blocks, nb_trials, colours_list)
        # handicapped agents
        action_limitations[1] = ['red']
        action_limitations[0] = ['yellow'] 
        run_experiment(path_to_results_constrained,state,tasks,action_limitations, nb_blocks, nb_trials, colours_list)

        return 0

    pool = multiprocessing.Pool(4)
    out = zip(pool.map(experiment_wrapper, [10]*10)) #perform 10 experiments with 10 blocks in parallel

if experiment_id == 3 or RUN_ALL:
    if RUN_ALL:
        experiment_id = 3
    ##### EXPERIMENT 3
    """Test to see how the planning algorithm performs in function of the number of agents."""

    nb_blocks = 20
    nb_trials = 5

    state, goal = generate_solvable_problem(nb_blocks)
    tasks = [('move_blocks', goal)]

    def experiment_wrapper(nb_agents):
        path_to_results = './experiment' + str(experiment_id) + '/' + str(nb_agents) + 'agents/'
        write_csv_header(path_to_results) #make a separate folder for each trial
        action_limitations = [ [] for i in range(nb_agents) ]
        run_experiment(path_to_results,state,tasks,action_limitations,nb_blocks,nb_trials,colours_list)
        return 0

    pool = multiprocessing.Pool(4)
    out = zip(pool.map(experiment_wrapper, range(2, 9))) #iterate over nb agents in parallel

    combine_results('./experiment' + str(experiment_id) + '/' )

if experiment_id == 4 or RUN_ALL:
    if RUN_ALL:
        experiment_id = 4
    ##### EXPERIMENT 4
    """
    Test to see how consistent our problem-generating code is.
    If you select a fixed number of blocks and generate N problems,
    how does the diffulty of the problems vary?
    """

    path_to_results = './experiment' + str(experiment_id) + '/'
    write_csv_header(path_to_results)

    nb_agents = 5
    nb_trials = 5
    nb_blocks = 10

    action_limitations = [ [] for i in range(nb_agents) ]

    def experiment_wrapper(nb_blocks):
        state, goal = generate_solvable_problem(nb_blocks)
        tasks = [('move_blocks', goal)]
        run_experiment(path_to_results,state,tasks,action_limitations,nb_blocks,nb_trials,colours_list)
        return 0

    pool = multiprocessing.Pool(4)
    out = zip(pool.map(experiment_wrapper, [10]*10)) #perform 10 experiments with 10 blocks in parallel

    # in this case the resulting plans aren't very important
    os.remove(os.path.join(path_to_results,'best_plan.csv'))
    os.remove(os.path.join(path_to_results,'worst_plan.csv'))
    os.remove(os.path.join(path_to_results,'single_agent_plan.csv'))


if experiment_id == 5 or RUN_ALL:
    if RUN_ALL:
        experiment_id = 5
    ##### EXPERIMENT 5
    """Test to see how the planning algorithm performs in function of the number of agents."""

    nb_blocks = 20
    nb_trials = 5

    def experiment_wrapper_helper(tup):
        return experiment_wrapper(*tup)

    def experiment_wrapper(nb_blocks,nb_agents):

        state, goal = generate_solvable_problem(nb_blocks)
        tasks = [('move_blocks', goal)]

        path_to_results = './experiment' + str(experiment_id) + '/' + str(nb_blocks) + 'blocks/' +str(nb_agents) +'agents/'
        write_csv_header(path_to_results) #make a separate folder for each trial
        action_limitations = [ [] for i in range(nb_agents) ]
        run_experiment(path_to_results,state,tasks,action_limitations,nb_blocks,nb_trials,colours_list)
        return 0

    pool = multiprocessing.Pool(4)
    out = zip(pool.map(experiment_wrapper_helper,product(range(10,100,10),range(2, 9)))) #iterate over nb agents in parallel

    combine_results('./experiment' + str(experiment_id) + '/' )
