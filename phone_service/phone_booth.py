import sys
import sqlite3
import simpy
import numpy as np
from math import floor, ceil

# fmt: off
MAX_SATISFACTION = 5                      # The highest level of satisfaction
MAX_START_SATISFACTION = 5                # The maximum level of satisfaction a person can start with
MIN_START_SATISFACTION = 2                # The minimum level of satisfaction a person can start with
MIN_SATISFACTION = 0                      # The amount of satisfaction that will prompt an exit from the system
NUM_CHANNELS = 99999                      # Number of channels in the phone service
MAX_CALL_TIME = 160                       # Duration of a call and the minutes the person can afford to call
CALL_SETUP_TIME = 0.5                     # The timestamp to authenticate and dial a peer
NUM_PERSONS = 800                         # Number of persons in the group
CALL_DROP_RATE = 0.95                     # The probability that calls are droped when high load
CALL_DROP_AMOUNT = 30                     # The number of active calls required before service starts failing
ARRIVAL_RATE = 13                         # How many persons that join the system per hour
FRUSTRATION_INTERVAL = 10                 # The time in minutes between a decrement in satisfaction
LOGGING = False
# fmt: on

queue_size = 0
active_channels = 0
total_channels = 0
active_calls = 0
total_calls = 0
total_drops = 0
previous_timestamp = -1
env = None
persons = []


def printer(message: str):
    if LOGGING:
        print(message)


def decrement_satisfaction(proxy_person):
    assert isinstance(proxy_person, ProxyPerson)
    person = proxy_person.person
    assert isinstance(person, Person)
    person.satisfaction -= 1

    printer("decremented satisfaction")

    if person.satisfaction <= MIN_SATISFACTION:
        proxy_person.process.interrupt("technical difficulties")


def maybe_decrement_satisfaction(env: simpy.Environment, proxy_person):
    assert isinstance(proxy_person, ProxyPerson)
    person = proxy_person.person
    assert isinstance(person, Person)

    if person.last_decrement_time + 10 <= env.now:
        printer("(certainly?) decremented satisfaction")

        person.satisfaction -= 1
        person.last_decrement_time = env.now

    if person.satisfaction <= MIN_SATISFACTION:
        proxy_person.process.interrupt("frustrated")


class PhoneBooth:
    def __init__(self, env: simpy.Environment, phone_service, num_phones: int):
        self.env = env
        self.phone_service = phone_service
        self.num_phones = num_phones
        self.phone = simpy.Resource(env, num_phones)


class Person:
    def __init__(
        self,
        env: simpy.Environment,
        phone_booth: PhoneBooth,
        id: int,
        call_time: int,
        satisfaction: int,
    ):
        self.env = env
        self.phone_booth = phone_booth
        self.id = id
        self.call_time = call_time
        self.satisfaction = satisfaction
        self.done = False
        self.queue_size = 0  # the queue size when the `Person` joined the queue
        self.queue_start = 0
        self.queue_end = 0
        self.last_decrement_time = 0

    def use_booth(self, proxy_person):
        try:
            global queue_size

            with self.phone_booth.phone.request() as request:
                yield request

                queue_size -= 1

                printer(
                    f"Person {self.id} enters the phone booth at {self.env.now:.2f}"
                )

                while self.call_time > 0:
                    yield self.env.process(
                        self.phone_booth.phone_service.call(db, proxy_person)
                    )
        except simpy.Interrupt:
            printer(f"Person {self.id} left the system at {env.now}")
            self.queue_end = env.now

        self.done = True
        self.queue_end = self.env.now


class ProxyPerson:
    def __init__(self, *args, **kwargs):
        self.person = Person(*args, **kwargs)
        self.process = None

    def start(self):
        self.process = env.process(self.person.use_booth(self))
        env.process(self.handle_frustration())
        yield self.process

    def handle_frustration(self):
        global env

        while self.person.queue_end == 0:
            yield env.timeout(FRUSTRATION_INTERVAL)
            if self.process.is_alive:
                maybe_decrement_satisfaction(env, self)


class PhoneService:
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.channels = simpy.Resource(env, NUM_CHANNELS)

    def call(self, db: sqlite3.Cursor, proxy_person: ProxyPerson):
        global active_calls, total_drops, active_channels, total_channels, total_calls
        assert isinstance(proxy_person, ProxyPerson)
        person = proxy_person.person
        assert isinstance(person, Person)
        try:
            with self.channels.request() as _caller:
                active_channels += 1
                total_channels += 1

                yield self.env.timeout(CALL_SETUP_TIME)

                printer(f"Person {person.id} tries calling at {self.env.now:.2f}")
                person.call_start = self.env.now

                if (
                    active_channels > CALL_DROP_AMOUNT
                    and np.random.uniform() > CALL_DROP_RATE
                ):
                    active_channels -= 1
                    total_drops += 1
                    raise RuntimeError

                with self.channels.request() as _called:
                    active_channels += 1
                    total_channels += 1
                    active_calls += 1
                    total_calls += 1
                    start = self.env.now
                    yield self.env.timeout(person.call_time)
                    person.call_time = 0
                    end = self.env.now
                    printer(
                        f"Person {person.id} talked for {end - start:.2f} minutes at {self.env.now:.2f}"
                    )
                active_channels -= 1
                active_calls -= 1
            active_channels -= 1

            person.finished = self.env.now
        except RuntimeError:
            if proxy_person.process.is_alive:
                decrement_satisfaction(proxy_person)

            printer(f"Person {person.id} tries calling again at {self.env.now:.2f}")


def setup(
    env: simpy.Environment,
    db: sqlite3.Cursor,
    proxy_persons,
    time_interval: float,
):
    global queue_size

    for proxy_person in proxy_persons:
        person = proxy_person.person

        assert isinstance(person, Person)
        yield env.timeout(np.random.uniform() * time_interval * 2)

        printer(f"Person {person.id} arrives to the queue at {env.now:.2f}")
        queue_size += 1
        person.queue_size = queue_size
        person.queue_start = env.now

        env.process(proxy_person.start())


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        print("Usage: python phone_booth.py <num_phones> <arrival_rate>")
        exit(1)

    try:
        num_phones = int(sys.argv[1])
    except Exception:
        print("Number of phones must be an integer")
        exit(1)

    try:
        arrival_rate = int(sys.argv[2])
    except Exception:
        print("Arrival rate must be an integer")
        exit(1)

    average_service_rate = num_phones / (MAX_CALL_TIME / 2) * 60
    average_time_interval = 60 / arrival_rate # The interval a person arrives

    print(f"Service rate: {average_service_rate}")
    print(f"Arrival rate: {arrival_rate}")

    with sqlite3.connect("statistics.db", autocommit=True) as db:
        cursor = db.cursor()

        try:
            cursor.execute(
                "CREATE TABLE rates(num_phones, service, arrival, expected_waiting_time, expected_queue_length)"
            )
        except Exception:
            printer("Table rates already exists")

        rates = [
            (
                num_phones,
                average_service_rate,
                arrival_rate,
            )
        ]

        printer("Inserting rate data into database")
        cursor.executemany(
            "INSERT INTO rates(num_phones, service, arrival) VALUES (?, ?, ?)",
            rates,
        )

        # Create an environment
        env = simpy.Environment()

        phone_service = PhoneService(env)

        # Create the phone booths
        phone_booth = PhoneBooth(env, phone_service, num_phones)

        proxy_persons = [
            ProxyPerson(
                env,
                phone_booth,
                id,
                floor(np.random.uniform(0, MAX_CALL_TIME)),
                ceil(np.random.uniform(MIN_START_SATISFACTION, MAX_START_SATISFACTION)),
            )
            for id in range(NUM_PERSONS)
        ]

        start_satisfaction = [
            (
                num_phones,
                proxy_person.person.id,
                proxy_person.person.satisfaction,
            )
            for proxy_person in proxy_persons
        ]

        try:
            cursor.execute(
                "CREATE TABLE start_satisfaction(num_phones, id, satisfaction)"
            )
        except Exception:
            printer("Table start_satisfaction already exists")

        try:
            cursor.execute(
                "CREATE TABLE end_satisfaction(num_phones, id, satisfaction, queue_size, queue_time)"
            )
        except Exception:
            printer("Table end_satisfaction already exists")

        printer("Inserting start data into database")
        cursor.executemany(
            "INSERT INTO start_satisfaction(num_phones, id, satisfaction) VALUES (?, ?, ?)",
            start_satisfaction,
        )

        # Start the setup process
        env.process(setup(env, cursor, proxy_persons, average_time_interval))

        # Execute!
        env.run()

        assert sum(
            [1 if proxy_person.person.done else 0 for proxy_person in proxy_persons]
        ) == len(proxy_persons), "Everyone should be done at this point"

        end_satisfaction = [
            (
                num_phones,
                proxy_person.person.id,
                proxy_person.person.satisfaction,
                proxy_person.person.queue_size,
                proxy_person.person.queue_end
                - proxy_person.person.queue_start,  # this is the queuing time
            )
            for proxy_person in proxy_persons
        ]

        printer("Inserting finalized data into database")
        cursor.executemany(
            "INSERT INTO end_satisfaction(num_phones, id, satisfaction, queue_size, queue_time) VALUES (?, ?, ?, ?, ?)",
            end_satisfaction,
        )

        cursor.close()
