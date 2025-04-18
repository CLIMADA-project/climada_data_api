from climada.hazard import TCTracks
import sys
import os

# Add parent directory to sys.path to access config and utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import DATA_DIR
from create_log_file import log_msg

LOG_FILE = "progress_make_tc_tracks.txt"

def main(basin='EP', n_tracks=10, min_year=1980, max_year=2020, time_step_h=1):
    year_range = (min_year, max_year)
    nb_syn_tracks = int(n_tracks)
    path = os.path.join(DATA_DIR, f"tracks_{str(min_year)}_{str(max_year)}_{str(time_step_h)}_{str(n_tracks)}_{basin}")
    
    if os.path.exists(path) and os.listdir(path):  # If directory exists AND is not empty
        msg = f"Directory {path} already contains files. Skipping computation.\n"
        print(f"Warning: {msg}")
        log_msg(msg, LOG_FILE)
        return  # Exit early to avoid overwriting existing data

    log_msg(f"Starting track generation for basin {basin}, years {min_year}-{max_year}, "
            f"{n_tracks} synthetic tracks, timestep {time_step_h}h\n", LOG_FILE)

    tc_tracks = TCTracks.from_ibtracs_netcdf(genesis_basin=basin, year_range=year_range)
    
    if not tc_tracks.data:
        msg = f"No tracks found for basin {basin} in years {year_range}. Skipping.\n"
        print(f"Warning: {msg}")
        log_msg(msg, LOG_FILE)
        return

    tc_tracks.equal_timestep(time_step_h=time_step_h)

    if nb_syn_tracks > 0:
        tc_tracks.calc_perturbed_trajectories(nb_synth_tracks=nb_syn_tracks)

    if not os.path.exists(path):
        os.makedirs(path)

    tc_tracks.write_netcdf(path)
    log_msg(f"Finished track generation for basin {basin}. Output saved to {path}\n", LOG_FILE)


if __name__ == "__main__":
    main(basin=sys.argv[1], n_tracks=sys.argv[2])
