# Tropical Cyclone Hazard Pipeline

This folder contains a set of scripts and job submission files to compute tropical cyclone (TC) hazard layers using CLIMADA. The workflow spans from generating synthetic tracks, computing hazards by basin, concatenating them into global datasets, and downscaling to individual countries.

## Overview

Each Python script has a corresponding SLURM job script (`.sh`) for running on the Euler cluster. The process is modular and should be executed in the following order.

## 1. Generate Synthetic TC Tracks

- **Script:** `compute_tc_tracks.py`
- **Job file:** `job_tc_tracks.sh`
- **Purpose:**  
  Reads historical TC tracks from the IBTrACS dataset and generates synthetic trajectories for a specific basin.
- **Output directory:**  

DATA_DIR/tracks/{n_tracks}/{basin}/

Contains the `.nc` file with synthetic and historical tracks.

## 2. Compute TC Hazard per Basin

- **Script:** `compute_tc_genesis_basin.py`
- **Job file:** `job_compute_tc_genesis_basin.sh`
- **Purpose:**  
Converts the generated tracks into a CLIMADA `TropCyclone` hazard object for each basin.
- **Output directory:**  

Contains the `.nc` file with synthetic and historical tracks.

## 2. Compute TC Hazard per Basin

- **Script:** `compute_tc_genesis_basin.py`
- **Job file:** `job_compute_tc_genesis_basin.sh`
- **Purpose:**  
Converts the generated tracks into a CLIMADA `TropCyclone` hazard object for each basin.
- **Output directory:**  

DATA_DIR/tropical_cyclones_v3/genesis_basin/{n_tracks}synth_tracks/{basin}/historical/

Contains an `.hdf5` file with the hazard object for the given basin.

## 3. Concatenate TC Hazards Across Basins

- **Script:** `tc_concat_basins.py`
- **Job file:** `job_concat_tc_basins.sh`
- **Purpose:**  
Merges the hazard files of all basins into a single global `TropCyclone` file for each year and scenario.
- **Output directory:**  

DATA_DIR/tropical_cyclones_v3/global/{n_tracks}synth_tracks/{scenario}/{year}/
Contains a single global `.hdf5` file per year and scenario.

## 4. Downscale Global TC Hazard to Countries

- **Script:** `compute_tc_countries.py`
- **Job file:** `job_tc_countries.sh`
- **Purpose:**  
Splits the global `TropCyclone` hazard into country-specific files using ISO3 country codes.
- **Output directory:**

DATA_DIR/tropical_cyclones_v3/countries/{n_tracks}synth_tracks/{scenario}/{year}/

Contains one `.hdf5` file per country per year and scenario.

## 5. (Optional) Compute TC Hazards Under Climate Change Scenarios

- **Script:** `compute_tc_climate_change.py`
- **Job file:** `job_compute_tc_climate_change.sh`
- **Purpose:**  
Generates TC hazard files for future climate scenarios (e.g., RCP8.5).
- **Output directory:**  

DATA_DIR/tropical_cyclones_v3/genesis_basin/{n_tracks}synth_tracks/{basin}/{scenario}/{year}/


## Example Execution Order

Submit the jobs in the following sequence:

```bash
sbatch job_tc_tracks.sh
sbatch job_compute_tc_genesis_basin.sh
sbatch job_concat_tc_basins.sh
sbatch job_tc_countries.sh
# Optional:
sbatch job_compute_tc_climate_change.sh
