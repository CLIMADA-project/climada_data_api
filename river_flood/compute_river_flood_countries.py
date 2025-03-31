import os
import sys
from pathlib import Path

import numpy as np

from climada_petals.hazard.river_flood import RiverFlood
from pycountry import countries

# Add parent directory to sys.path to access config and utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import DATA_DIR
from create_log_file import log_msg

def main(years=None, scenario='rcp26', replace=True):
    """
    Process river flood hazard data from global to individual country scale.

    Parameters:
        years (list of str, optional): Start and end year as strings, e.g., ['2010', '2030'].
        scenario (str, optional): Climate scenario (e.g., 'rcp26', 'rcp85'). Default is 'rcp26'.
        replace (bool, optional): Whether to overwrite existing country files. Default is True.
    """
    LOG_FILE = "progress_make_river_flood_countries.txt"

    if years is None:
        years = ['2010', '2030']
    years_str = "_".join(years)

    base_path = os.path.join(DATA_DIR, 'river_flood', 'river_flood_v3')
    global_path = os.path.join(base_path, 'global', scenario, years_str)
    country_path = os.path.join(base_path, 'country', scenario, years_str)
    os.makedirs(country_path, exist_ok=True)

    log_msg(f"Reading global flood files for scenario '{scenario}' and years {years_str}\n", LOG_FILE)

    for file in os.listdir(global_path):
        file_path = os.path.join(global_path, file)
        rf = RiverFlood.from_hdf5(file_path)

        file_parts = file.split('_', 4)  # Example: river_flood_150arcsec_rcp26_2010_2030.hdf5

    for country in countries:
        country_file_name = f"{file_parts[0]}_{file_parts[1]}_{file_parts[2]}_{file_parts[3]}_{country.alpha_3}_{file_parts[4]}"
        country_file_path = os.path.join(country_path, country_file_name)

        if Path(country_file_path).exists() and not replace:
            continue

        try:
            rf_country = rf.select(reg_id=int(country.numeric))
        except RuntimeError:
            continue
        if rf_country is None:
            continue

        rf_country.write_hdf5(country_file_path)
        log_msg(f"Saved {country.alpha_3} flood file.\n", LOG_FILE)


if __name__ == "__main__":

    start_year = sys.argv[1]
    end_year = sys.argv[2]
    scenario = sys.argv[3]

    main(years=[start_year, end_year], scenario=scenario)
