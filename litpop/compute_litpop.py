import os
import sys
from datetime import datetime

from affine import Affine
from rasterio.crs import CRS
from pycountry import countries
from climada.entity import LitPop

# Add parent directory to sys.path to access config and utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import DATA_DIR
from create_log_file import log_msg

missing_country = []

# Get today's date info
DATE_STR = datetime.today().strftime('%Y%m%d')
MONTH_STR = datetime.today().strftime('%m_%Y')

# Output directories include date
OUT_DIR_COUNTRIES = os.path.join(DATA_DIR, 'litpop', 'countries', MONTH_STR)
OUT_DIR = os.path.join(DATA_DIR, 'litpop', 'global', MONTH_STR)

# Create them if needed
os.makedirs(OUT_DIR_COUNTRIES, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

EXPONENTS = {'pop': (0,1), 'default': (1,1), 'assets': (3,0)}
FIN_MODE = {'pop': 'pop', 'default': 'pc', 'assets': 'pc'}
EXP_STR = {'pop': 'pop', 'default': '', 'assets': 'assets_pc'}

OUT_FILE_COUNTRY = f'LitPop_{{exposure}}_150arcsec_{{country}}_remaped.hdf5'
OUT_FILE = f'LitPop_{{exposure}}_150arcsec_remaped.hdf5'
LOG_FILE = f"progress_make_litpop_{DATE_STR}.txt"

# Define the aligned grid
target_res_deg = 150 / 3600  # 0.0416667°
aligned_lon_min = -180 + (target_res_deg / 2)
aligned_lat_max = 90 - (target_res_deg / 2)
width = int(360 / target_res_deg)
height = int(180 / target_res_deg)

transform = Affine(
    target_res_deg, 0, aligned_lon_min,
    0, -target_res_deg, aligned_lat_max
)

target_grid = {
    "driver": "GTiff",
    "dtype": "float32",
    "nodata": None,
    "width": width,
    "height": height,
    "count": 1,
    "crs": CRS.from_epsg(4326),
    "transform": transform,
}

def make_litpop(exposure, use_aligned_grid=True):
    """
    Create LitPop exposures at a country level and then concatenate them to create a global exposure.
    Parameters:
        exposure (str): 'pop', 'default', or 'assets'
        use_aligned_grid (bool): If False, target_grid is skipped
    """
    litpop_list = []

    for country in countries:
        try:
            if use_aligned_grid:
                litpop = LitPop.from_countries(
                    country.alpha_3, res_arcsec=150,
                    exponents=EXPONENTS[exposure],
                    fin_mode=FIN_MODE[exposure],
                    target_grid=target_grid
                )
            else:
                litpop = LitPop.from_countries(
                    country.alpha_3, res_arcsec=150,
                    exponents=EXPONENTS[exposure],
                    fin_mode=FIN_MODE[exposure]
                )

            # Save country-level output
            out_path = os.path.join(OUT_DIR_COUNTRIES, exposure)
            os.makedirs(out_path, exist_ok=True)
            litpop.write_hdf5(os.path.join(out_path, OUT_FILE_COUNTRY.format(
                exposure=EXP_STR[exposure], country=country.alpha_3)))

            log_msg(f"Country {country.alpha_3} processed.\n", LOG_FILE)
            litpop_list.append(litpop)

        except Exception as e:
            missing_country.append(country.alpha_3)
            log_msg(f"Country {country.alpha_3} failed. Error: {e}\n", LOG_FILE)

    if litpop_list:
        log_msg(f"Start creating global exposure.\n", LOG_FILE)
        litpop_concat = LitPop.concat(litpop_list)

        out_path = os.path.join(OUT_DIR, exposure)
        os.makedirs(out_path, exist_ok=True)
        litpop_concat.write_hdf5(os.path.join(out_path, OUT_FILE.format(exposure=EXP_STR[exposure])))
        log_msg(f"Global file saved.\n", LOG_FILE)
    else:
        log_msg("No successful country data to concatenate.\n", LOG_FILE)

    log_msg(f"The following countries were not successful: {missing_country}.\n", LOG_FILE)

if __name__ == "__main__":
    for exposure in ['assets']:
        make_litpop(exposure, use_aligned_grid=True)  # Set to False to skip target_grid
