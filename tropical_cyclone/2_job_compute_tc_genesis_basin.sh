#!/bin/bash
#SBATCH -n 1
#SBATCH --cpus-per-task=4
#SBATCH --time=8:00:00
#SBATCH --mem-per-cpu=50000


. /cluster/project/climate/$USER/venv/climada_env/bin/activate

for basin in "NI" "SI" "NA" "SP" "WP" "SA" "EP"
do
    sleep_time=$((($RANDOM % 5) + 5))
    echo "Sleeping for $sleep_time seconds before running basin $basin"
    sleep $sleep_time

    echo "Running TC genesis computation for basin $basin"
    python3 2_compute_tc_genesis_basin.py $basin 10 1980 2020
done