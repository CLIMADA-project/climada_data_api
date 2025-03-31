#!/bin/bash
#SBATCH -n 1
#SBATCH --cpus-per-task=1
#SBATCH --time=20:00:00
#SBATCH --mem-per-cpu=20000

. /cluster/project/climate/$USER/venv/climada_env/bin/activate

# === Run future scenarios ===
# Scenarios: rcp26, rcp45, rcp60, rcp85
# Years: 2040, 2060, 2080
python3 compute_tc_countries.py rcp26,rcp45,rcp60,rcp85 10 2040,2060,2080

# === Run historical scenario ===
# Year fixed to 1980_2020
python3 5_compute_tc_countries.py historical 10 1980_2020