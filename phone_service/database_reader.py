import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

if __name__ == "__main__":
    plt.close("all")

    start_satisfaction = None
    end_satisfaction = None
    averages = None

    with sqlite3.connect("statistics.db", autocommit=True) as db:
        averages = pd.read_sql(
            "SELECT num_phones, AVG(queue_size) as queue_size, AVG(queue_time) as queue_time, AVG(satisfaction) as satisfaction FROM end_satisfaction GROUP BY num_phones",
            db,
        )

    print(averages)

    queue_size = averages[["num_phones", "queue_size"]]
    queue_size.set_index("num_phones", inplace=True)
    plt.figure()
    queue_size.plot()
    plt.xlabel("Number of phones")
    plt.ylabel("People in queue")
    plt.title("Average queue size upon arrival")
    plt.savefig("queue_size.png", dpi=600)

    queue_time = averages[["num_phones", "queue_time"]]
    queue_time.set_index("num_phones", inplace=True)
    plt.figure()
    queue_time.plot()
    plt.xlabel("Number of phones")
    plt.ylabel("Time in queue")
    plt.title("Average queue time upon exit")
    plt.savefig("queue_time.png", dpi=600)

    satisfaction = averages[["num_phones", "satisfaction"]]
    satisfaction.set_index("num_phones", inplace=True)
    plt.figure()
    satisfaction.plot()
    plt.xlabel("Number of phones")
    plt.ylabel("Satisfaction")
    plt.title("Average satisfaction")
    plt.savefig("satisfaction.png", dpi=600)
