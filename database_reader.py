import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import sys

if __name__ == "__main__":
    with_drop = len(sys.argv) > 1

    plt.close("all")

    person_statistics = None
    time_series = None

    with sqlite3.connect("statistics.db", autocommit=True) as db:
        person_statistics = pd.read_sql("SELECT * FROM person_statistics", db)
        time_series = pd.read_sql("SELECT * FROM time_series", db)

    title = " with drop" if with_drop else ""
    filename = "_with_drop" if with_drop else ""

    print(person_statistics["arrival"], person_statistics["access"])

    df = person_statistics
    queue_duration = df["access"] - df["arrival"]
    plt.figure()
    queue_duration.plot()
    plt.xlabel("Number of people")
    plt.ylabel("Time waiting in queue")
    plt.title(f"Time waiting in queue{title}")
    plt.savefig(f"wait_time{filename}.png", dpi=600)

    df = person_statistics
    queue_duration = df["access"] - df["arrival"]
    df = queue_duration.cumsum()
    plt.figure()
    queue_duration.plot()
    plt.xlabel("Number of people")
    plt.ylabel("Cumulative summation of time waiting in queue")
    plt.title(f"Cumulative summation of time waiting in queue{title}")
    plt.savefig(f"cumsum_wait_time{filename}.png", dpi=600)

    print(queue_duration)
    print(queue_duration.mean())

    df = time_series
    df = df[["timestamp", "queue_size"]]
    df.set_index("timestamp", inplace=True)
    plt.figure()
    df.plot(figsize=(16, 4))
    plt.xlabel("Timestamp (minutes)")
    plt.ylabel("People in queue")
    plt.title(f"Queue size{title}")
    plt.savefig(f"queue_size{filename}.png", dpi=600)

    if with_drop:
        df = time_series
        df = df[["timestamp", "total_drops"]]
        df.set_index("timestamp", inplace=True)
        plt.figure()
        df.plot()
        plt.xlabel("Timestamp (minutes)")
        plt.ylabel("Channels dropped")
        plt.title("Channels dropped")
        plt.savefig("channels_dropped.png", dpi=600)
