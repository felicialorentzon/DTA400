import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

if __name__ == "__main__":
    plt.close("all")

    start_satisfaction = None
    end_satisfaction = None
    averages = None

    with sqlite3.connect("statistics.db", autocommit=True) as db:
        start_satisfaction = pd.read_sql("SELECT * FROM start_satisfaction", db)
        end_satisfaction = pd.read_sql("SELECT * FROM end_satisfaction", db)
        averages = pd.read_sql(
            "SELECT num_phones, AVG(queue_size) as queue_size, AVG(queue_time) as queue_time, AVG(satisfaction) as satisfaction FROM end_satisfaction GROUP BY num_phones",
            db,
        )

    print(start_satisfaction)
    print(end_satisfaction)
    print(averages)
