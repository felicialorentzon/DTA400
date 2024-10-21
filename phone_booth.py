import sqlite3
import random
import simpy

# fmt: off
RANDOM_SEED = 42
NUM_CHANNELS = 99999   # Number of channels in the phone service
NUM_PHONES = 700       # Number of phones in the phone booth
MAX_CALL_TIME = 160    # Duration of a call and the minutes the person can afford to call
SERVICE_RATE = NUM_PHONES / (MAX_CALL_TIME / 2) * 60
CALL_SETUP_TIME = 0.5  # The timestamp to authenticate and dial a peer
NUM_PERSONS = 6000      # Number of persons in the group
CALL_DROP_RATE = 0.95  # The probability that calls are droped when high load
CALL_DROP_AMOUNT = 30  # The number of active calls required before service starts failing
ARRIVAL_RATE = 50
TIME_INTERVAL = ARRIVAL_RATE / 60 # The interval a person arrives
DEBUG = False
# fmt: on

print(f"Service rate: {SERVICE_RATE}")
print(f"Arrival rate: {ARRIVAL_RATE}")

queue_size = 0
active_channels = 0
total_channels = 0
active_calls = 0
total_calls = 0
total_drops = 0
previous_timestamp = -1


def printer(message: str):
    if DEBUG:
        print(message)


def time_series(db: sqlite3.Cursor, timestamp):
    global queue_size
    global active_channels
    global total_channels
    global active_calls
    global total_calls
    global total_drops
    global previous_timestamp

    if timestamp <= previous_timestamp:
        return
    previous_timestamp = timestamp

    db.execute(
        "INSERT INTO time_series VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            timestamp,
            queue_size,
            active_channels,
            total_channels,
            active_calls,
            total_calls,
            total_drops,
        ),
    )


def update(db: sqlite3.Cursor, field: str, id: int, value):
    db.execute(f"UPDATE person_statistics SET {field} = ? WHERE id = ?", (value, id))


class PhoneBooth:
    def __init__(self, env: simpy.Environment, phone_service, num_phones: int):
        self.env = env
        self.phone_service = phone_service
        self.num_phones = num_phones
        self.phone = simpy.Resource(env, num_phones)


class Person:
    def __init__(
        self, env: simpy.Environment, phone_booth: PhoneBooth, id: int, call_time: int
    ):
        self.env = env
        self.phone_booth = phone_booth
        self.id = id
        self.call_time = call_time
        self.arrival = 0
        self.access = 0
        self.call_start = 0
        self.finished = 0
        self.insufficient_funds = False

    def process(self, db: sqlite3.Cursor):
        global queue_size

        with self.phone_booth.phone.request() as request:
            yield request

            queue_size -= 1

            printer(f"Person {self.id} enters the phone booth at {self.env.now:.2f}")
            self.access = self.env.now
            update(db, "access", self.id, self.access)
            time_series(db, self.env.now)

            if self.call_time <= 0:
                self.insufficient_funds = True
                update(db, "insufficient_funds", self.id, self.insufficient_funds)

            while self.call_time > 0:
                try:
                    yield self.env.process(
                        self.phone_booth.phone_service.call(db, self)
                    )
                except RuntimeError:
                    printer(
                        f"Person {self.id} tries calling again at {self.env.now:.2f}"
                    )
                    time_series(db, self.env.now)


class PhoneService:
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.channels = simpy.Resource(env, NUM_CHANNELS)

    def call(self, db: sqlite3.Cursor, person: Person):
        global active_calls, total_drops, active_channels, total_channels, total_calls
        with self.channels.request() as _caller:
            active_channels += 1
            total_channels += 1

            yield self.env.timeout(CALL_SETUP_TIME)

            printer(f"Person {person.id} tries calling at {self.env.now:.2f}")
            person.call_start = self.env.now
            update(db, "call_start", person.id, person.call_start)
            time_series(db, self.env.now)

            if active_channels > CALL_DROP_AMOUNT and random.random() > CALL_DROP_RATE:
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
                time_series(db, self.env.now)
            active_channels -= 1
            active_calls -= 1
        active_channels -= 1

        person.finished = self.env.now
        update(db, "finished", person.id, person.finished)
        time_series(db, self.env.now)


def setup(env, db: sqlite3.Cursor, time_interval):
    global queue_size

    for person in persons:
        yield env.timeout(random.random() * time_interval)

        printer(f"Person {person.id} arrives at the phone booth at {env.now:.2f}")
        person.arrival = env.now
        update(db, "arrival", person.id, person.arrival)

        queue_size += 1
        time_series(db, env.now)

        env.process(person.process(db))


if __name__ == "__main__":
    with sqlite3.connect("statistics.db", autocommit=True) as db:
        # Create an environment
        env = simpy.Environment()

        phone_service = PhoneService(env)

        # Create the phone booths
        phone_booth = PhoneBooth(env, phone_service, NUM_PHONES)

        persons = [
            Person(env, phone_booth, id, random.randint(0, MAX_CALL_TIME))
            for id in range(NUM_PERSONS)
        ]

        starting_statistics = [
            (
                person.id,
                person.call_time,
                person.arrival,
                person.access,
                person.call_start,
                person.finished,
                person.insufficient_funds,
            )
            for person in persons
        ]

        cursor = db.cursor()

        cursor.execute(
            "CREATE TABLE person_statistics(id, start_funds, arrival, access, call_start, finished, insufficient_funds)"
        )

        cursor.execute(
            "CREATE TABLE time_series(timestamp, queue_size, active_channels, total_channels, active_calls, total_calls, total_drops)"
        )

        cursor.executemany(
            "INSERT INTO person_statistics(id, start_funds, arrival, access, call_start, finished, insufficient_funds) VALUES (?, ?, ?, ?, ?, ?, ?)",
            starting_statistics,
        )

        # Setup and start the simulation
        random.seed(RANDOM_SEED)  # This helps to reproduce the results

        # Start the setup process
        env.process(setup(env, cursor, TIME_INTERVAL))

        # Execute!
        env.run()

        cursor.close()
