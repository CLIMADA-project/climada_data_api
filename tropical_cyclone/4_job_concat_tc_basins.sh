#!/bin/bash
#SBATCH -n 1
#SBATCH --cpus-per-task=1
#SBATCH --time=4:00:00
#SBATCH --mem-per-cpu=20000

. /cluster/project/climate/$USER/venv/climada_env/bin/activate

N_TRACKS=10
SCRIPT="4_tc_concat_basins.py"

# Run future scenarios together
echo "Running future scenarios..."
python3 $SCRIPT rcp26,rcp60,rcp85 $N_TRACKS 2040,2060,2080

# Run historical separately
echo "Running historical..."
python3 $SCRIPT historical $N_TRACKS 1980_2020