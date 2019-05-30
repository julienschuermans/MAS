# TODO

000) fix all remaining stuff in the current code
  - DONE

00) evaluate timing: why does resolution take very long sometimes
- are there easy fixes for this?#
- something related to rejected_proposals? NO
- DONE:
 ```
  INFO:root:make_proposal 14.6518 sec
  INFO:root:evaluate_proposal 0.9802 sec
  INFO:root:update plan 0.0038 sec
  INFO:root:check plan 0.5286 sec
  ```
    - agents spend lots of time in make_proposal:
    - nested loops: O(len(partial_plan) x planning_horizon)
       - decrease planning_horizon? too small, might not find a solution
       - early exit from the loop?
           - got a quick implementation working (only look at timesteps close to end of current final_plan)

0) run_n_trials --> compute average time, solution quality, extract best plan
  - DONE

1) LAURANE: specialised agents
   - limit actions of a certain agent
   - don't care at all in partial plan
   - only extra constraints in make_proposal
   - DONE

2) JULIEN: easily scale to larger problems.
  - generate a 10/100/1000-burger initial state and corresponding goals
  - DONE


3) agents that do not observe the full state
  - can they still have a valid partial_plan ? depends on pyhop I guess


4) plan_pruning: deterministic method that all agents can apply independently.
  - eliminate redundant putdown/pickup
  - other inefficiencies?


5) smart agent order instead of random (round robin?)

6) detect & escape infinite loops in find_resolution
  - when every agent has proposed None?
    - I've tried this and the constraint is too harsh
    - it is possible too find a plan when all agents have proposed None once:
    - 2-agent example:
        agent 0 proposes None
        agent 1 proposes an action
        agent 0 proposes an action
        agent 1 proposes None --> at this point both agents have proposed None, but there is no need to exit the while loop!
        agent 0 proposes an action
