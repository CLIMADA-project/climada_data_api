import os
import sys
import glob
import datetime
from pathlib import Path

# Add parent directory to sys.path to access config and utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from climada.hazard import Centroids
from climada_petals.hazard.river_flood import RiverFlood
from climada.util.api_client import Client
from config import DATA_DIR
from create_log_file import log_msg

# Output file naming template
OUT_FILE_NAME = 'river_flood_150arcsec_{scenario}_{years_str}.hdf5'
OUT_FILE_NAME_LP_GRID = 'river_flood_150arcsec_{scenario}_{years_str}_litpop_aligned.hdf5'
DATE_CENTROIDS = '03_2025'

# Optional: helpful reference to data sources
DATA_LINKS = {
    'ISIMIP2a': 'https://zenodo.org/record/4446364',
    'ISIMIP2b': 'https://zenodo.org/record/4627841',
}
def main(years=None, scenario='hist', aligned='litpop'):
    """
    Compute river flood hazard for a given year range and scenario, then save to file.

    Parameters:
        years (list of int): Start and end year, e.g. [1980, 2010].
        scenario (str): Scenario name (e.g., 'hist', 'rcp85', etc.)
        aligned (str):  Which grid to align the centroids on land ('litpop' or 'climate_data').
    """
    # === Set up date-based folder and logging ===
    today = datetime.date.today()
    date_folder = today.strftime("%m_%Y")  # e.g. '03_2025'
    years_str = f"{years[0]}_{years[1]}"
    LOG_FILE = f"progress_make_river_flood_global_{scenario}_{date_folder}.txt"
    log_path = Path(LOG_FILE)

    if log_path.exists():
        log_path.unlink()

    log_msg(f"Started computing floods for scenario '{scenario}' and years {years_str}\n", LOG_FILE)

    # === Set data input directory ===
    if scenario == 'hist':
        flddph_data_dir = os.path.join(DATA_DIR, 'river_flood', 'flood_flddph_hist')
    else:
        flddph_data_dir = os.path.join(DATA_DIR, 'river_flood', 'flood_flddph', scenario)

    # === Set centroids ===
    if aligned == "litpop":
        centroids = Centroids.from_hdf5(os.path.join(
            DATA_DIR, 'centroids', DATE_CENTROIDS,
            'earth_centroids_150asland_1800asoceans_distcoast_region_litpop_aligned.hdf5'))
        out_file_name_template = OUT_FILE_NAME_LP_GRID
    elif aligned == 'climate_data':
        centroids = Centroids.from_hdf5(os.path.join(
            DATA_DIR, 'centroids', DATE_CENTROIDS,
            'earth_centroids_150asland_1800asoceans_distcoast_region.hdf5'))
        out_file_name_template = OUT_FILE_NAME

    # === Output path ===
    out_dir = os.path.join(DATA_DIR, 'river_flood', date_folder, scenario, years_str)
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, out_file_name_template.format(scenario=scenario, years_str=years_str))

    # === Process input files ===
    rf_list = []
    input_files = glob.glob(os.path.join(flddph_data_dir, '*.nc*'))

    for flddph_file_path in input_files:
        fldfrc_file_path = flddph_file_path.replace('flddph', 'fldfrc')
        try:
            rf = RiverFlood.from_nc(
                years=range(int(years[0]), int(years[1])),
                dph_path=flddph_file_path,
                frc_path=fldfrc_file_path,
                centroids=centroids
            )
            gcm_id = flddph_file_path.split('/')[-1].split('_')
            date_year = [datetime.date.fromordinal(ordinal).year for ordinal in rf.date]
            rf.event_name = [f"{y}_{gcm_id[3]}_{gcm_id[2]}_{scenario}" for y in date_year]
            rf_list.append(rf)
            log_msg("Computation for one GCM done\n", LOG_FILE)
        except Exception as e:
            log_msg(f"Failed on file: {flddph_file_path} with error: {e}\n", LOG_FILE)

    # === Save result ===
    if rf_list:
        rf_concat = rf.concat(rf_list)
        rf_concat.frequency = rf_concat.frequency / len(rf_list)
        rf_concat.write_hdf5(out_file)
        log_msg(f"Completed flood hazard for scenario '{scenario}' and years {years_str}\n", LOG_FILE)
    else:
        log_msg(f"No flood data was processed successfully for scenario '{scenario}' and years {years_str}\n", LOG_FILE)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python compute_river_flood.py <start_year> <end_year> <scenario>")
        sys.exit(1)

    start_year = int(sys.argv[1])
    end_year = int(sys.argv[2])
    scenario = sys.argv[3]

    main(years=[start_year, end_year], scenario=scenario)
