import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

WITH_DROP = True

if __name__ == "__main__":
    plt.close("all")

    person_statistics = None
    time_series = None

    with sqlite3.connect("statistics.db", autocommit=True) as db:
        person_statistics = pd.read_sql("SELECT * FROM person_statistics", db)
        time_series = pd.read_sql("SELECT * FROM time_series", db)

    title = " with drop" if WITH_DROP else ""
    filename = "_with_drop" if WITH_DROP else ""

    df = person_statistics
    queue_duration = df["access"] - df["arrival"]
    plt.figure()
    queue_duration.plot()
    plt.xlabel("Number of people")
    plt.ylabel("Time waiting in queue")
    plt.title(f"Time waiting in queue{title}")
    plt.savefig(f"wait_time{filename}.png", dpi=600)

    df = person_statistics
    queue_duration = (df["access"] - df["arrival"]) / df["id"]
    df = queue_duration.cumsum()
    plt.figure()
    queue_duration.plot()
    plt.xlabel("Number of people")
    plt.ylabel("Cumulative summation of time waiting in queue")
    plt.title(f"Cumulative summation of time waiting in queue{title}")
    plt.savefig(f"cumsum_wait_time{filename}.png", dpi=600)

    print(queue_duration.mean(axis=0))

    df = time_series
    df = df[["timestamp", "queue_size"]]
    df.set_index("timestamp", inplace=True)
    plt.figure()
    df.plot(figsize=(16, 4))
    plt.xlabel("Timestamp (minutes)")
    plt.ylabel("People in queue")
    plt.title(f"Queue size{title}")
    plt.savefig(f"queue_size{filename}.png", dpi=600)

    if WITH_DROP:
        df = time_series
        df = df[["timestamp", "total_drops"]]
        df.set_index("timestamp", inplace=True)
        plt.figure()
        df.plot()
        plt.xlabel("Timestamp (minutes)")
        plt.ylabel("Channels dropped")
        plt.title("Channels dropped")
        plt.savefig("channels_dropped.png", dpi=600)
