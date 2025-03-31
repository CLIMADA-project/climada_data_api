# River Flood Hazard Processing

This folder contains scripts to compute **river flood hazard data** using  CLIMADA and CLIMADA Petals.

The workflow consists of two main steps:
1. **Global Hazard Computation** (`compute_river_flood.py`)
2. **Country Selection** (`compute_flood_countries.py`)

---

## 1. Global River Flood Computation

### Script: `compute_river_flood.py`

This script reads in river flood depth and fraction data (from ISIMIP), computes hazard events for each GCM and time period, and aggregates them into a global hazard file.

It uses the `RiverFlood.from_nc()` method and remaps the hazard to defined centroids. The script computes:
- Historical scenarios (`hist`)
- Future climate scenarios (`rcp26`, `rcp60`, `rcp85`)

job_compute_historical_river_flood.sh
Runs the script for the historical period (e.g., 1980–2000 or 1980-2010).
job_compute_river_flood_future.sh
Runs the script across several future periods and RCPs (e.g. rcp26, rcp60, rcp85), by chunks of 20 years.

SLURM scripts:
job_river_flood_country_historical.sh
job_river_flood_country_future.sh

These run the equivalent python scripts on the euler cluster

The files available here must be available as defined in the scripts: 
DATA_LINKS = {
    'ISIMIP2a': 'https://zenodo.org/record/4446364',
    'ISIMIP2b': 'https://zenodo.org/record/4627841',
}