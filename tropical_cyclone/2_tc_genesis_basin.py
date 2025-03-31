import os
import sys
from datetime import datetime
from pathlib import Path

from climada.hazard import Centroids, TropCyclone, TCTracks
from pathos.pools import ProcessPool as Pool

# Add parent directory to sys.path to access config and utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import DATA_DIR
from create_log_file import log_msg

# Path to precomputed centroids
CENT_FILE_PATH = os.path.join(
    DATA_DIR,
    "centroids",
    "08_2022",  # You can update this if using new centroids
    "earth_centroids_150asland_1800asoceans_distcoast_region.hdf5"
)

def main(basin='EP', n_tracks=10, min_year=1980, max_year=2020, time_step_h=1):
    LOG_FILE = "progress_make_tc_basin.txt"
    log_msg(f"Starting computing TC for basin {basin}.\n", LOG_FILE)

    current_ym = datetime.now().strftime("%m_%Y")  

    # Define output directory (genesis files)
    output_dir = os.path.join(
        DATA_DIR,
        "tropical_cyclones",
        current_ym,
        "genesis_basin",
        f"{n_tracks}synth_tracks",
        basin,
        "historical"
    )
    os.makedirs(output_dir, exist_ok=True)

    # Define input directory (tracks)
    path_tracks = os.path.join(
        DATA_DIR,
        "tropical_cyclones",
        current_ym,
        "tracks",
        f"{min_year}_{max_year}",
        f"{n_tracks}synth_tracks",
        basin
    )

    all_tracks = TCTracks.from_netcdf(path_tracks)

    # Load centroids and restrict to extent of track data
    centroids = Centroids.from_hdf5(CENT_FILE_PATH)
    centroids = centroids.select(extent=all_tracks.get_extent(5))

    pool = Pool()
    chunk_size = 10  # Number of tracks per parallel job

    for n in range(0, all_tracks.size, chunk_size):
        subset_data = all_tracks.data[n:n + chunk_size]
        if not subset_data:
            continue

        file_name = f"tropical_cyclone_{n_tracks}synth_tracks_150arcsec_genesis_{basin}_{min_year}_{max_year}_{n}.hdf5"
        file_path = Path(output_dir) / file_name

        if file_path.exists():
            continue

        # Create a new TCTracks object and assign the selected subset
        tracks = TCTracks()
        tracks.data = subset_data

        # Copy required attributes
        for attr in [
            "time_step", "max_sustained_wind_unit", "central_pressure_unit",
            "name", "sid", "orig_event_flag", "data_provider", "id_no", "category"
        ]:
            if hasattr(all_tracks, attr):
                setattr(tracks, attr, getattr(all_tracks, attr))

        # Generate hazard and save
        tc = TropCyclone.from_tracks(tracks, centroids=centroids, pool=pool)
        tc.write_hdf5(file_path)

    pool.close()
    pool.join()

    log_msg(f"Finished computing TC for basin {basin}.\n", LOG_FILE)

if __name__ == "__main__":
    basin = sys.argv[1] if len(sys.argv) > 1 else 'EP'
    n_tracks = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    min_year = int(sys.argv[3]) if len(sys.argv) > 3 else 1980
    max_year = int(sys.argv[4]) if len(sys.argv) > 4 else 2020

    main(basin, n_tracks, min_year, max_year)
