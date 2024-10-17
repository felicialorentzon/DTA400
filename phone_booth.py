import random
import simpy

# fmt: off
RANDOM_SEED = 42
NUM_CHANNELS = 99999  # Number of channels in the phone service
NUM_PHONES = 300       # Number of phones in the phone booth
MAX_CALL_TIME = 45    # Duration of a call and the minutes the person can afford to call
CALL_SETUP_TIME = 0.5 # The time to authenticate and dial a peer
NUM_PERSONS = 400     # Number of persons in the group
CALL_DROP_RATE = 0.9  # The probability that calls are droped when high load
CALL_DROP_AMOUNT = 5  # The number of active calls required before service starts failing
T_INTER = 8           # The interval a person arrives
SIM_TIME = 3000        # Simulation time in minutes
# fmt: on

class PhoneBooth:
    def __init__(self, env: simpy.Environment, phone_service, num_phones: int, call_time: int):
        self.env = env
        self.phone_service = phone_service
        self.num_phones = num_phones
        self.phone = simpy.Resource(env, num_phones)
        self.call_time = call_time

    def call(self, person):
        yield self.env.process(self.phone_service.call(person))

class Person:
    def __init__(self, env: simpy.Environment, phonebooth: PhoneBooth, name: int, call_time: int):
        self.env = env
        self.phonebooth = phonebooth
        self.name = name
        self.call_time = call_time
        self.arrival = 0
        self.access = 0
        self.call_start = 0
        self.finished = 0
        self.insufficient_funds = False

    def process(self):
        # print(f'Person {self.name} arrives at the phone booth at {env.now:.2f}')
        self.arrival = env.now
        with self.phonebooth.phone.request() as request:
            yield request

            # print(f'Person {self.name} enters the phone booth at {env.now:.2f}')
            self.access = env.now
            while self.call_time > 0:
                try:
                    # print(f'Person {self.name} tries calling at {env.now:.2f}')
                    self.call_start = env.now
                    yield env.process(self.phonebooth.call(self))
                except RuntimeError:
                    # print (f"Person {self.name} tries calling again at {env.now:.2f}")
                    pass
                except Exception:
                    break
            self.finished = env.now
            self.insufficient_funds = self.finished == self.access

class PhoneService:
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.current_channels = 0
        self.channels = simpy.Resource(env, NUM_CHANNELS)

    def call(self, person: Person):
        with self.channels.request() as caller:
            self.current_channels += 1
            yield env.timeout(CALL_SETUP_TIME)

            if person.call_time <= 0:
                raise Exception

            if self.current_channels > CALL_DROP_AMOUNT and random.random() > CALL_DROP_RATE:
                raise RuntimeError
            
            with self.channels.request() as called:
                self.current_channels += 1
                start = env.now
                yield env.timeout(person.call_time)
                end = env.now
                # print(f"Person {person.name} talked for {end - start:.2f} minutes at {env.now:.2f}")
            self.current_channels -= 1
        self.current_channels -= 1
            
def setup(env, t_inter):
    for person in persons:
        yield env.timeout(random.randint(t_inter - 8, t_inter + 8))
        env.process(person.process())

# Create an environment 
env = simpy.Environment()

phone_service = PhoneService(env)

# Create the phone booths
phonebooth = PhoneBooth(env, phone_service, NUM_PHONES, MAX_CALL_TIME)

persons = [Person(env, phonebooth, name, random.randint(0, MAX_CALL_TIME)) for name in range(NUM_PERSONS)]

# Setup and start the simulation
random.seed(RANDOM_SEED)  # This helps to reproduce the results

# Start the setup process
env.process(setup(env, T_INTER))

# Execute!
env.run(until=SIM_TIME)

for person in persons:
    print(f"{person.name:5} | {person.arrival:5.2f} | {person.access:5.2f} | {person.finished:5.2f} | {person.insufficient_funds}")