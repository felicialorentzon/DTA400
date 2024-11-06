#!/bin/env bash

if [ -f "statistics.db" ]; then
    rm statistics.db
fi

for arrival_rate in {3..23..10}; do
    for num_phones in {1..100}; do
        for iterations in {1..10}; do
            python phone_booth.py $num_phones $arrival_rate
        done
    done

    python database_reader.py $arrival_rate
    rm statistics.db
done
