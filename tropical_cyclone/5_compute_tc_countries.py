import os
import sys
from datetime import datetime
from pathlib import Path
import argparse

from climada.hazard import TropCyclone
from pycountry import countries

# Add parent directory to sys.path to access config and utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import DATA_DIR
from create_log_file import log_msg

# File naming templates
FILE_NAME = 'tropical_cyclone_{n_tracks}synth_tracks_150arcsec_{scenario}_{country}_{year}.hdf5'
FILE_NAME_HIST = 'tropical_cyclone_{n_tracks}synth_tracks_150arcsec_genesis_{scenario}_{country}_{year}.hdf5'
LOG_FILE = 'progress_tc_country_downscaling.txt'

def main(years_list=None, scenarios=None, n_tracks=10, replace=True):
    if years_list is None:
        years_list = [2040, 2060, 2080]
    if scenarios is None:
        scenarios = [26, 45, 60, 85]

    tracks_str = f"{n_tracks}synth_tracks"
    current_ym = datetime.now().strftime("%m_%Y")
    base_path = os.path.join(DATA_DIR, "tropical_cyclones", current_ym)

    for scenario in scenarios:
        if scenario == 'historical':
            scenario_str = 'historical'
            scenario_years = ['1980_2020']
        else:
            scenario_str = f"rcp{scenario}"
            scenario_years = years_list

        for year in scenario_years:
            log_msg(f"Processing country-level files for {scenario_str} - {year}\n", LOG_FILE)

            global_path = os.path.join(base_path, 'global', tracks_str, scenario_str, str(year))
            
            # Adjust output path: skip year subfolder for historical
            if scenario == 'historical':
                output_path_base = os.path.join(base_path, 'countries', tracks_str, scenario_str)
            else:
                output_path_base = os.path.join(base_path, 'countries', tracks_str, scenario_str, str(year))
            
            os.makedirs(output_path_base, exist_ok=True)

            for filename in os.listdir(global_path):
                file_path = os.path.join(global_path, filename)
                tc = TropCyclone.from_hdf5(file_path)

                for country in countries:
                    if scenario == 'historical':
                        file_name = FILE_NAME_HIST.format(
                            scenario=scenario_str, year=year, country=country.alpha_3, n_tracks=n_tracks
                        )
                    else:
                        file_name = FILE_NAME.format(
                            scenario=scenario_str, year=year, country=country.alpha_3, n_tracks=n_tracks
                        )

                    output_file = os.path.join(output_path_base, file_name)

                    if os.path.exists(output_file) and not replace:
                        continue

                    tc_country = tc.select(reg_id=int(country.numeric))
                    if tc_country is None:
                        continue

                    tc_country.write_hdf5(output_file)
                    
if __name__ == "__main__":
    print(sys.argv)
    scenario_input = sys.argv[1] if len(sys.argv) > 1 else 'rcp85'
    n_tracks = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    year_input = sys.argv[3] if len(sys.argv) > 3 else '2040,2060,2080'

    # Split input
    scenarios = scenario_input.split(',')
    years_list = year_input.split(',')

    main(
        years_list=years_list,
        scenarios=scenarios,
        n_tracks=n_tracks
    )
