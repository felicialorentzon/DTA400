import sqlite3
import random
import simpy

# fmt: off
RANDOM_SEED = 42
NUM_CHANNELS = 99999  # Number of channels in the phone service
NUM_PHONES = 200      # Number of phones in the phone booth
MAX_CALL_TIME = 45    # Duration of a call and the minutes the person can afford to call
CALL_SETUP_TIME = 0.5 # The time to authenticate and dial a peer
NUM_PERSONS = 400     # Number of persons in the group
CALL_DROP_RATE = 0.9  # The probability that calls are droped when high load
CALL_DROP_AMOUNT = 5  # The number of active calls required before service starts failing
TIME_INTERVAL = 8     # The interval a person arrives
# fmt: on


def update(db: sqlite3.Cursor, field: str, id: int, value):
    db.execute(f"UPDATE person_statistics SET {field} = ? WHERE id = ?", (value, id))


class PhoneBooth:
    def __init__(self, env: simpy.Environment, phone_service, num_phones: int):
        self.env = env
        self.phone_service = phone_service
        self.num_phones = num_phones
        self.phone = simpy.Resource(env, num_phones)

    def call(self, db: sqlite3.Cursor, person):
        yield self.env.process(self.phone_service.call(db, person))


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
        print(f"Person {self.id} arrives at the phone booth at {env.now:.2f}")
        self.arrival = env.now
        update(db, "arrival", self.id, self.arrival)
        with self.phone_booth.phone.request() as request:
            yield request

            print(f"Person {self.id} enters the phone booth at {env.now:.2f}")
            self.access = env.now
            update(db, "access", self.id, self.access)

            while self.call_time > 0:
                try:
                    yield env.process(self.phone_booth.call(db, self))
                except RuntimeError:
                    print(f"Person {self.id} tries calling again at {env.now:.2f}")
                except Exception:
                    self.insufficient_funds = True
                    update(db, "insufficient_funds", self.id, self.insufficient_funds)
                    break


class PhoneService:
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.current_channels = 0
        self.channels = simpy.Resource(env, NUM_CHANNELS)

    def call(self, db: sqlite3.Cursor, person: Person):
        with self.channels.request() as _caller:
            self.current_channels += 1

            yield env.timeout(CALL_SETUP_TIME)

            print(f"Person {person.id} tries calling at {env.now:.2f}")
            person.call_start = env.now
            update(db, "call_start", person.id, person.call_start)

            if person.call_time <= 0:
                raise Exception

            if (
                self.current_channels > CALL_DROP_AMOUNT
                and random.random() > CALL_DROP_RATE
            ):
                raise RuntimeError

            with self.channels.request() as _called:
                self.current_channels += 1
                start = env.now
                yield env.timeout(person.call_time)
                person.call_time = 0
                end = env.now
                print(
                    f"Person {person.id} talked for {end - start:.2f} minutes at {env.now:.2f}"
                )
            self.current_channels -= 1
        self.current_channels -= 1

        person.finished = env.now
        update(db, "finished", person.id, person.finished)


def setup(env, db: sqlite3.Cursor, time_interval):
    for person in persons:
        yield env.timeout(random.randint(time_interval - 8, time_interval + 8))
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
