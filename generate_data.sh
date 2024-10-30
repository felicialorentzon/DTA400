#!/bin/env bash

if [ -f "statistics.db" ]; then
    rm statistics.db
fi

for num_phones in {1..100}; do
    for iterations in {1..10}; do
        python phone_booth.py $num_phones
    done
done

python database_reader.py
