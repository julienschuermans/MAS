import multiprocessing, argparse
from ma_htn import *
from itertools import product

logging.basicConfig(level=logging.INFO)

# setup argparser
parser = argparse.ArgumentParser()
parser.add_argument(
    '-id', '--experiment',
    help = 'Experiment identifier',
    default = 'demo'
)
args = parser.parse_args()
current = args.experiment

if current == 'demo':
    RUN_ALL = False
    RUN_DEMO_ONLY = True
    experiment_id = 'demo'
elif current == 'all':
    RUN_ALL = True
    RUN_DEMO_ONLY = False
    experiment_id = 1
else:
    RUN_ALL = False
    RUN_DEMO_ONLY = False
    experiment_id = int(current)

colours_list = ['red', 'blue', 'yellow']


if RUN_DEMO_ONLY:
    RUN_ALL = False
    experiment_id = 'demo'

    print("""
    ****************************************
    Multi-agent HTN planning demo
    ****************************************
    """)
    nb_blocks = 15
    state, goal = generate_solvable_problem(nb_blocks)

    print("- Define state:")
    print_state(state)
    print('')
    print("- Define goal:")
    print_goal(goal)
    print('')

    path_to_results = './demo_results/'
    if os.path.isdir(path_to_results):
        logging.error("Directory './demo_results/' already exists! Remove it and try again.")
        exit()
    write_csv_header(path_to_results)

    tasks = [('move_blocks', goal)]

    print("This shouldn't take too long. Relax.\n")
    nb_trials = 5
    for nb_agents in range(2,12,2):
        print("- Solving problem with %d agents" % nb_agents)
        action_limitations = [ [] for i in range(nb_agents) ]
        run_experiment(path_to_results,state,tasks,action_limitations,nb_blocks,nb_trials, colours_list)

    print("- Done. Results can be found here: \n" + os.path.abspath(path_to_results))


if experiment_id == 1 or RUN_ALL:
    if RUN_ALL:
        experiment_id = 1
    ##### EXPERIMENT 1
    """Test to see what happens when agents have limited capabilities. (e.g. swap-only agents)"""

    path_to_results = './experiment' + '{:02d}'.format(experiment_id) + '/normal/'
    path_to_results_constrained = './experiment' + '{:02d}'.format(experiment_id) + '/constrained/'

    write_csv_header(path_to_results)
    write_csv_header(path_to_results_constrained)

    nb_agents = 5
    nb_blocks = [10]*10  #perform 10 experiments with 10 blocks
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
    out = zip(pool.map(experiment_wrapper, nb_blocks))


if experiment_id == 2 or RUN_ALL:
    if RUN_ALL:
        experiment_id = 2
    ##### EXPERIMENT 2
    """Test to see what happens when agents have colour-limited capabilities. (e.g red-only agents)"""

    path_to_results = './experiment' + '{:02d}'.format(experiment_id) + '/normal/'
    path_to_results_constrained = './experiment' + '{:02d}'.format(experiment_id) + '/constrained/'

    write_csv_header(path_to_results)
    write_csv_header(path_to_results_constrained)

    nb_agents = 2
    nb_blocks = [10]*10 #perform 10 experiments with 10 blocks
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
    out = zip(pool.map(experiment_wrapper, nb_blocks))

if experiment_id == 3 or RUN_ALL:
    if RUN_ALL:
        experiment_id = 3
    ##### EXPERIMENT 3
    """Test to see how the planning algorithm performs in function of the number of agents."""

    nb_blocks = 20
    nb_agents = range(2, 9)
    nb_trials = 5

    state, goal = generate_solvable_problem(nb_blocks)
    tasks = [('move_blocks', goal)]

    def experiment_wrapper(nb_agents):
        path_to_results = './experiment' + '{:02d}'.format(experiment_id) + '/' + '{:02d}'.format(nb_agents) + 'agents/'
        write_csv_header(path_to_results) #make a separate folder for each trial
        action_limitations = [ [] for i in range(nb_agents) ]
        run_experiment(path_to_results,state,tasks,action_limitations,nb_blocks,nb_trials,colours_list)
        return 0

    pool = multiprocessing.Pool(4)
    out = zip(pool.map(experiment_wrapper, nb_agents)) #iterate over nb agents in parallel

    combine_results('./experiment' + '{:02d}'.format(experiment_id) + '/' )

if experiment_id == 4 or RUN_ALL:
    if RUN_ALL:
        experiment_id = 4
    ##### EXPERIMENT 4
    """
    Test to see how consistent our problem-generating code is.
    If you select a number of blocks and generate 10 problems,
    how does the diffulty of the problems vary? (diffulty=single_agent_plan_length)
    """

    path_to_results = './experiment' + str(experiment_id) + '/'
    write_csv_header(path_to_results)

    nb_agents = 2 #doesnt really matter. we're only interested in the single_agent_plan_length anyways
    nb_trials = 5
    nb_blocks = [5]*5 + [10]*5 + [15]*5 + [20]*5 + [25]*5 + [30]*5 + [35]*5 + [40]*5

    action_limitations = [ [] for i in range(nb_agents) ]

    action_limitations[1] = ['red']
    action_limitations[0] = ['yellow']

    def experiment_wrapper(nb_blocks):
        state, goal = generate_solvable_problem(nb_blocks)
        tasks = [('move_blocks', goal)]
        run_experiment(path_to_results,state,tasks,action_limitations,nb_blocks,nb_trials,colours_list)
        return 0

    pool = multiprocessing.Pool(4)
    out = zip(pool.map(experiment_wrapper, nb_blocks))

if experiment_id == 5 or RUN_ALL:
    if RUN_ALL:
        experiment_id = 5
    ##### EXPERIMENT 5
    """Test to see how the planning algorithm performs in function of the number of agents and blocks."""

    nb_blocks = range(10,100,10)
    nb_agents = range(2, 9)
    nb_trials = 5

    def experiment_wrapper_helper(tup):
        return experiment_wrapper(*tup)

    def experiment_wrapper(nb_blocks,nb_agents):

        state, goal = generate_solvable_problem(nb_blocks)
        tasks = [('move_blocks', goal)]

        path_to_results = './experiment' + '{:02d}'.format(experiment_id) + '/' + '{:02d}'.format(nb_blocks) + 'blocks/' +'{:02d}'.format(nb_agents) +'agents/'
        write_csv_header(path_to_results) #make a separate folder for each trial
        action_limitations = [ [] for i in range(nb_agents) ]
        run_experiment(path_to_results,state,tasks,action_limitations,nb_blocks,nb_trials,colours_list)
        return 0

    pool = multiprocessing.Pool(4)
    out = zip(pool.map(experiment_wrapper_helper,product(nb_blocks,nb_agents))) #iterate over nb agents in parallel

    combine_results('./experiment' + '{:02d}'.format(experiment_id) + '/' )


if experiment_id == 6 or RUN_ALL:
    if RUN_ALL:
        experiment_id = 6
    ##### EXPERIMENT 6
    """Test to see how the planning algorithm performs in function of the number of agents and blocks."""

    nb_blocks = range(10,50,10)
    nb_agents = range(3, 10, 2)
    nb_trials = 5 # solve each problem 5 times to generate statistics

    # for each block size, generate N problems to avg it out
    nb_problems_per_blocksize = 5

    def experiment_wrapper_helper(tup):
        return experiment_wrapper(*tup)

    def experiment_wrapper(nb_blocks,nb_agents):
        path_to_results = './experiment' + '{:02d}'.format(experiment_id) + '/' + '{:02d}'.format(nb_blocks) + 'blocks/' +'{:02d}'.format(nb_agents) +'agents/'
        write_csv_header(path_to_results) #make a separate folder for each trial
        action_limitations = [ [] for i in range(nb_agents) ]

        for i in range(0,nb_agents-1,2):
            action_limitations[i+1] = ['red']
            action_limitations[i] = ['yellow']
        print(action_limitations)


        for i in range(nb_problems_per_blocksize):
            state, goal = generate_solvable_problem(nb_blocks)
            tasks = [('move_blocks', goal)]
            run_experiment(path_to_results,state,tasks,action_limitations,nb_blocks,nb_trials,colours_list)
        return 0

    pool = multiprocessing.Pool(4)
    out = zip(pool.map(experiment_wrapper_helper,product(nb_blocks,nb_agents)))

    combine_results('./experiment' + '{:02d}'.format(experiment_id) + '/' )
