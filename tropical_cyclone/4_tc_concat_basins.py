import os
import sys
import numpy as np
from datetime import datetime
from climada.hazard import TropCyclone
from config import DATA_DIR
from create_log_file import log_msg

# List of basins to concatenate
BASINS = ['EP', 'WP', 'SP', 'NI', 'SI']  # Replace with your actual list

# File naming templates
FILE_NAME = "tropical_cyclone_{n_tracks}synth_tracks_150arcsec_genesis_{basin}_{scenario}_{year}.hdf5"
FILE_NAME_HIST = "tropical_cyclone_{n_tracks}synth_tracks_150arcsec_genesis_{basin}_historical_{year}.hdf5"
FILE_NAME_GLOBAL = "tropical_cyclone_{n_tracks}synth_tracks_150arcsec_genesis_global_{scenario}_{year}.hdf5"
FILE_NAME_GLOBAL_HIST = "tropical_cyclone_{n_tracks}synth_tracks_150arcsec_genesis_global_historical_{year}.hdf5"

LOG_FILE = "progress_concat_tc_genesis.txt"

def main(climate_scenarios=None, n_tracks=10, years=None):
    """
    Concatenate basin-level TC genesis files into global datasets, per scenario and year.

    Parameters:
        climate_scenarios (list of str): List of scenarios, e.g., ['rcp26', 'rcp85', 'historical']
        n_tracks (int): Number of synthetic tracks (default: 10)
        years (list of str): Target years as strings, e.g., ['2040', '2060', '2080']
    """
    if climate_scenarios is None:
        climate_scenarios = ['rcp85']
    if years is None:
        years = ['2040', '2060', '2080']

    tracks_str = f"{n_tracks}synth_tracks"
    current_ym = datetime.now().strftime("%m_%Y")  # e.g. "03_2025"

    for scenario in climate_scenarios:
        for year in years:
            log_msg(f"Starting concatenating basins for year {year} and scenario {scenario}\n", LOG_FILE)

            tc = TropCyclone()
            basin_base_path = os.path.join(DATA_DIR, 'tropical_cyclones', current_ym, 'genesis_basin', tracks_str)

            # Read NI basin as the base
            ni_path = os.path.join(basin_base_path, 'NI')
            if scenario == 'historical':
                tc_file = FILE_NAME_HIST.format(n_tracks=n_tracks, basin='NI', year=year)
                tc_file_path = os.path.join(ni_path, scenario, tc_file)
            else:
                tc_file = FILE_NAME.format(n_tracks=n_tracks, basin='NI', year=year, scenario=scenario)
                tc_file_path = os.path.join(ni_path, scenario, year, tc_file)

            tc.read_hdf5(tc_file_path)
            max_event_id = np.max(tc.event_id)

            # Append other basins
            for basin in BASINS:
                if basin == 'NI':
                    continue  # Already included

                basin_path = os.path.join(basin_base_path, basin)
                if scenario == 'historical':
                    basin_file = FILE_NAME_HIST.format(n_tracks=n_tracks, basin=basin, year=year)
                    basin_file_path = os.path.join(basin_path, scenario, basin_file)
                else:
                    basin_file = FILE_NAME.format(n_tracks=n_tracks, basin=basin, year=year, scenario=scenario)
                    basin_file_path = os.path.join(basin_path, scenario, year, basin_file)

                    # Sanity check: only one file per directory
                    basin_dir = os.path.join(basin_path, scenario, year)
                    if os.path.exists(basin_dir):
                        all_files = os.listdir(basin_dir)
                        if len(all_files) > 1:
                            raise ValueError(f"Multiple files found in {basin_dir}")

                basin_tc = TropCyclone()
                basin_tc.read_hdf5(basin_file_path)
                basin_tc.event_id += max_event_id
                max_event_id = np.max(basin_tc.event_id)

                tc.append(basin_tc)

            # Save global file in date-based directory
            if scenario == 'historical':
                global_file = FILE_NAME_GLOBAL_HIST.format(n_tracks=n_tracks, scenario=scenario, year=year)
            else:
                global_file = FILE_NAME_GLOBAL.format(n_tracks=n_tracks, scenario=scenario, year=year)

            global_output_dir = os.path.join(
                DATA_DIR, 'tropical_cyclones', current_ym, 'genesis_basin', tracks_str, 'global', scenario, str(year)
            )
            os.makedirs(global_output_dir, exist_ok=True)

            tc.write_hdf5(os.path.join(global_output_dir, global_file))
            log_msg(f"Finished concatenating basins for year {year} and scenario {scenario}\n", LOG_FILE)


if __name__ == "__main__":
    print(sys.argv)
    scenario_input = sys.argv[1] if len(sys.argv) > 1 else 'rcp85'
    n_tracks = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    year_input = sys.argv[3] if len(sys.argv) > 3 else '2040,2060,2080'

    # Parse scenarios and years
    scenarios = scenario_input.split(',')
    years_list = year_input.split(',')

    main(
        climate_scenarios=scenarios,
        n_tracks=n_tracks,
        years=years_list
    )