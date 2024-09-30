"""
Carwash example.

Covers:

- Waiting for other processes
- Resources: Resource

Scenario:
  A carwash has a limited number of washing machines and defines
  a washing processes that takes some (random) time.

  Car processes arrive at the carwash at a random time. If one washing
  machine is available, they start the washing process and wait for it
  to finish. If not, they wait until they can use one.

"""

import itertools
import random

import simpy

# fmt: off
RANDOM_SEED = 42
NUM_MACHINES = 2     # Number of machines in the carwash
WASHTIME = 15        # Minutes it takes to clean a car
REPAIR_TIME = 30     # Minutes it takes for the repair person to repair the carwash
T_REPAIR_INTER = 50  # Time between repairs
T_INTER = 7          # Create a car every ~7 minutes
SIM_TIME = 300       # Simulation time in minutes
# fmt: on


class Carwash:
    """A carwash has a limited number of machines (``NUM_MACHINES``) to
    clean cars in parallel.

    Cars have to request one of the machines. When they got one, they
    can start the washing processes and wait for it to finish (which
    takes ``washtime`` minutes).

    """

    def __init__(self, env, num_machines, washtime):
        self.env = env
        self.num_machines = num_machines
        self.machine = simpy.PreemptiveResource(env, num_machines)
        self.washtime = washtime

    def wash(self, car):
        """The washing processes. It takes a ``car`` processes and tries
        to clean it."""
        yield self.env.timeout(random.randint(WASHTIME - 3, WASHTIME + 3))
        pct_dirt = random.randint(50, 99)
        print(f"Carwash removed {pct_dirt}% of {car}'s dirt.")

def car(env, name, cw, prio=0):
    """The car process (each car has a ``name``) arrives at the carwash
    (``cw``) and requests a cleaning machine.

    It then starts the washing process, waits for it to finish and
    leaves to never come back ...

    """
    print(f'{name} arrives at the carwash at {env.now:.2f}.')
    with cw.machine.request(priority=prio, preempt=False) as request:
        yield request

        try:
            print(f'{name} enters the carwash at {env.now:.2f}.')
            yield env.process(cw.wash(name))
        except simpy.Interrupt as interrupt:
            assert(interrupt.cause is not None)
            usage = env.now - interrupt.cause.usage_since
            print(f'{name} got preempted by repair person at {env.now:.2f}'
                  f' after {usage:.2f}')

        print(f'{name} leaves the carwash at {env.now:.2f}.')

def repair(env, cw, prio=-1):
    while True:
        yield env.timeout(random.randint(T_REPAIR_INTER - 20, T_REPAIR_INTER + 20))
        print(f'Repair person arrives at {env.now:.2f}')
        washes = [ cw.machine.request(priority=prio, preempt=True) for _ in range(cw.num_machines)]

        for req in washes:
            yield req
        
        print(f'Repair person repairing the washes at {env.now:.2f}.')
        yield env.timeout(REPAIR_TIME)

        for req in washes:
            cw.machine.release(req)
        print(f'Repair person finishes at {env.now:.2f}')
        

def setup(env, num_machines, washtime, t_inter):
    """Create a carwash, a number of initial cars and keep creating cars
    approx. every ``t_inter`` minutes."""
    # Create the carwash
    carwash = Carwash(env, num_machines, washtime)

    car_count = itertools.count()

    # Create 4 initial cars
    for _ in range(4):
        env.process(car(env, f'Car {next(car_count)}', carwash))

    # Create repair person
    env.process(repair(env, carwash))

    # Create more cars while the simulation is running
    while True:
        yield env.timeout(random.randint(t_inter - 2, t_inter + 2))
        env.process(car(env, f'Car {next(car_count)}', carwash))


# Setup and start the simulation
random.seed(RANDOM_SEED)  # This helps to reproduce the results

# Create an environment and start the setup process
env = simpy.Environment()
env.process(setup(env, NUM_MACHINES, WASHTIME, T_INTER))

# Execute!
env.run(until=SIM_TIME)