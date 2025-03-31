#!/bin/bash
#SBATCH -n 1
#SBATCH --cpus-per-task=1
#SBATCH --time=4:00:00
#SBATCH --mem-per-cpu=10000

. /cluster/project/climate/$USER/venv/climada_env/bin/activate

for basin in "NI" "SI" "NA" "SP" "WP" "SA" "EP"
do
    sleep_time=$((($RANDOM % 5) + 5))
    echo "Sleeping for $sleep_time seconds before running basin $basin..."
    sleep $sleep_time

    echo "Running TC track generation for basin: $basin"
    python3 1_compute_tc_tracks.py $basin 10 1980 2020
done