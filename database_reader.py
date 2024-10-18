import sqlite3

if __name__ == "__main__":
    with sqlite3.connect("statistics.db", autocommit=True) as db:
        cursor = db.cursor()

        cursor.execute("SELECT * FROM person_statistics")
        statistics = cursor.fetchall()
        cursor.close()

        print(f"{"ID":<5} {"Starting funds":<15} {"Arrival":<9} {"Access":<8} {"Call start":<12} {"Finished":<10} {"Insufficient funds":<18}")
        for person in statistics:
            (id, start_funds, arrival, access, call_start, finished, insufficient_funds) = person
            print(f"{id:<5} {start_funds:<15} {arrival:<9.2f} {access:<8.2f} {call_start:<12.2f} {finished:<10.2f} {insufficient_funds:<18}")
