#!/bin/bash
#SBATCH -n 1
#SBATCH --cpus-per-task=1
#SBATCH --time=20:00:00
#SBATCH --mem-per-cpu=20000

. /cluster/project/climate/$USER/venv/climada_env/bin/activate

for year in 2030 2050 2070
do
    year2=$((year + 20))
    for scenario in rcp26 rcp60 rcp85
    do
        python3 compute_river_flood_countries.py $year $year2 $scenario
    done
done
