import os
import sys
import numpy as np
from datetime import datetime
from climada.hazard import TropCyclone

# Add parent directory to sys.path to access config and utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import DATA_DIR
from create_log_file import log_msg

from datetime import datetime


import os
import numpy as np
from datetime import datetime
from climada.hazard import TropCyclone
from config import DATA_DIR
from create_log_file import log_msg

OUT_FILE_NAME = "tropical_cyclone_{tracks}_150arcsec_genesis_{basin}_{scenario}_{year}.hdf5"
HIST_FILE_NAME = "tropical_cyclone_{tracks}_150arcsec_genesis_{basin}_{start_year}_{end_year}.hdf5"

def main(basin='EP', climate_scenarios=None, future_years=None, n_tracks=10, min_year=1980, max_year=2020):
    """
    Generate climate-adjusted tropical cyclone genesis files for specific basins and scenarios.

    Parameters:
        basin (str): TC genesis basin code (e.g., 'EP' for Eastern Pacific).
        climate_scenarios (list of int): Climate scenarios (e.g., [26, 45, 60, 85]).
        future_years (list of int): Target years for climate projections.
        n_tracks (int): Number of synthetic tracks used in filenames.
        min_year (int): Start year of historical baseline period.
        max_year (int): End year of historical baseline period.
    """
    if future_years is None:
        future_years = [2040, 2060, 2080]
    if climate_scenarios is None:
        climate_scenarios = [26, 45, 60, 85]

    LOG_FILE = "progress_make_tc_climate.txt"
    current_ym = datetime.now().strftime("%m_%Y")  # e.g., "03_2025"

    # Define root output directory for this basin
    genesis_output_dir = os.path.join(
        DATA_DIR, 'tropical_cyclones', current_ym, 'genesis_basin', f'{n_tracks}synth_tracks', basin
    )

    # Load historical data
    path_hist = os.path.join(genesis_output_dir, "historical")
    file_name_hist = HIST_FILE_NAME.format(
        tracks=f"{n_tracks}synth_tracks", basin=basin, start_year=min_year, end_year=max_year
    )
    hist_file_path = os.path.join(path_hist, file_name_hist)

    if not os.path.exists(hist_file_path):
        print(f"Error: Historical file {hist_file_path} not found. Ensure that compute_tc_genesis_basin.py has run successfully.")
        return

    # Load historical TC hazard
    tc_haz = TropCyclone.from_hdf5(hist_file_path)

    for climate_scenario in climate_scenarios:
        for year in future_years:
            log_msg(f"Started computing climate change for scenario {climate_scenario} and year {year}.\n", LOG_FILE)

            rcp_str = f'rcp{climate_scenario}'
            path_future = os.path.join(genesis_output_dir, rcp_str, str(year))
            os.makedirs(path_future, exist_ok=True)

            file_name_future = OUT_FILE_NAME.format(
                tracks=f"{n_tracks}synth_tracks", basin=basin, scenario=climate_scenario, year=year
            )
            output_file = os.path.join(path_future, file_name_future)

            if os.path.exists(output_file):
                print(f"Warning: Output file {output_file} already exists.")

            # Apply climate scenario transformation
            scenario_str = f"{str(climate_scenario)[0]}.{str(climate_scenario)[1]}"
            tc_haz_future = tc_haz.apply_climate_scenario_knu(target_year=year, scenario=scenario_str)

            # Save output
            tc_haz_future.write_hdf5(output_file)
            log_msg(f"Finished computing climate change for scenario {climate_scenario} and year {year}.\n", LOG_FILE)


if __name__ == "__main__":
    print(sys.argv)
    basin = sys.argv[1] if len(sys.argv) > 1 else 'EP'
    n_tracks = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    min_year = int(sys.argv[3]) if len(sys.argv) > 3 else 1980
    max_year = int(sys.argv[4]) if len(sys.argv) > 4 else 2020
    main(basin, n_tracks=n_tracks, min_year=min_year, max_year=max_year)