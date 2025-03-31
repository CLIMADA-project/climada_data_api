
"""
Created August 2022

description: Load subsets of 2D windfields from the STORM model and combine them
             to global and basin-wide hazard sets. Present climate model simulations.

@author: simonameiler
"""

import copy as cp

# import CLIMADA modules:
from climada.hazard import TropCyclone
from climada.util.constants import SYSTEM_DIR

haz_dir = SYSTEM_DIR/"hazard"

# boundaries of (sub-)basins (lonmin, lonmax, latmin, latmax)
BASIN_BOUNDS = {
    # North Atlantic/Eastern Pacific Basin
    'AP': [-180.0, 0.0, 0.0, 65.0],

    # Indian Ocean Basin
    'IO': [30.0, 100.0, 0.0, 40.0],

    # Southern Hemisphere Basin
    'SH': [-180.0, 180.0, -60.0, 0.0],

    # Western Pacific Basin
    'WP': [100.0, 180.0, 0.0, 65.0],
}

reg_id = {'AP': 5000, 'IO': 5001, 'SH': 5002, 'WP': 5003}

# Initiate CHAZ tracks
def basin_split_haz(hazard, basin):
    """ Split CHAZ global hazard up into ocean basins of choice """
    tc_haz_split = TropCyclone()
    # get basin bounds
    x_min, x_max, y_min, y_max = BASIN_BOUNDS[str(basin)]
    basin_idx = (hazard.centroids.lat > y_min) & (
                 hazard.centroids.lat < y_max) & (
                 hazard.centroids.lon > x_min) & (
                 hazard.centroids.lon < x_max)
    hazard.centroids.region_id[basin_idx] = reg_id[basin]
    tc_haz_split = hazard.select(reg_id=reg_id[basin]) 
    return tc_haz_split

# load all STORM hazard files and append to list
STORM_hazard = []
for i_basin in ['EP', 'NA', 'NI', 'SI', 'SP', 'WP']:
    for i_ens in range(10):
        tc_hazard = TropCyclone.from_hdf5(haz_dir.joinpath(f"TC_{i_basin}_{i_ens}_0300as_STORM.hdf5"))
        STORM_hazard.append(tc_hazard)

# create master TropCyclone object of hazard list; save
STORM_master = cp.deepcopy(STORM_hazard[0])
for haz in range(1,len(STORM_hazard)):
    STORM_master.append(STORM_hazard[haz])    
STORM_master.write_hdf5(haz_dir.joinpath("TC_global_0300as_STORM.hdf5"))

# call basin split function and save results
for bsn in BASIN_BOUNDS:
    STORM_basin = TropCyclone()
    STORM_basin = basin_split_haz(STORM_master, bsn)
    STORM_basin.write_hdf5(haz_dir.joinpath(f"TC_{bsn}_0300as_STORM.hdf5"))

    

