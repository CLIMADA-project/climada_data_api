#!/bin/bash
#SBATCH -n 1
#SBATCH --cpus-per-task=1
#SBATCH --time=20:00:00
#SBATCH --mem-per-cpu=20000

. /cluster/project/climate/$USER/venv/climada_env/bin/activate

for year in 1980
do
    for scenario in hist
    do
        year2=$((year + 20))
        echo "Running compute_flood_countries.py for scenario '$scenario' and years $year–$year2"
        python3 compute_river_flood_countries.py $year $year2 $scenario
    done
done
