#!/bin/bash
#SBATCH -n 1
#SBATCH --cpus-per-task=1
#SBATCH --time=4:00:00
#SBATCH --mem-per-cpu=40000


. /cluster/project/climate/$USER/venv/climada_env/bin/activate

for year in 2030 2050 2070
do
    year2=$((year + 20))
    for rcp in rcp26 rcp60 rcp85
    do
        sleep_time=$(( ($RANDOM % 5) + 5 ))
        echo "Sleeping $sleep_time seconds before launching $rcp for $year–$year2"
        sleep $sleep_time

        echo "Running: compute_river_flood.py $year $year2 $rcp"
        python3 compute_river_flood.py $year $year2 $rcp
    done
done
