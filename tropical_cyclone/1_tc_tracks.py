from climada.hazard import TCTracks
import sys
import os
# Add parent directory to sys.path to access config and utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import DATA_DIR
from create_log_file import log_msg

def main(basin='EP', n_tracks=10, min_year=1980, max_year=2020, time_step_h=1):
    year_range = (min_year, max_year)
    nb_syn_tracks = int(n_tracks)
    path = os.path.join(DATA_DIR, f"tracks_{str(min_year)}_{str(max_year)}_{str(time_step_h)}_{str(n_tracks)}_{basin}")
    if os.path.exists(path) and os.listdir(path):  # If directory exists AND is not empty
        print(f"Warning: Directory {path} already contains files. Skipping computation.")
        return  # Exit early to avoid overwriting existing data

    tc_tracks = TCTracks.from_ibtracs_netcdf(genesis_basin=basin, year_range=year_range)
    if not tc_tracks.data:
        print(f"Warning: No tracks found for basin {basin} in years {year_range}. Skipping.")
    tc_tracks.equal_timestep(time_step_h=time_step_h)
    if nb_syn_tracks>0:
        tc_tracks.calc_perturbed_trajectories(nb_synth_tracks=nb_syn_tracks)
    isExist = os.path.exists(path)
    print(path)
    if not isExist:
        os.makedirs(path)
    tc_tracks.write_netcdf(path)


if __name__ == "__main__":
    basin = sys.argv[1] if len(sys.argv) > 1 else 'EP'
    n_tracks = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    min_year = int(sys.argv[3]) if len(sys.argv) > 3 else 1980
    max_year = int(sys.argv[4]) if len(sys.argv) > 4 else 2020

    main(basin, n_tracks, min_year, max_year)

