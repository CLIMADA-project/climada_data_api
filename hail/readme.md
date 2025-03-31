This script shows how the MeteoSwiss Probability of Hail (POH) and Maximum expected severe hail size (MESHS) were converted into climada hazard objects for the publication Portmann et al. (2024).
The full code of the paper is available at https://doi.org/10.5281/zenodo.12784190

Note that some paths in the scripts refer to locally stored MeteoSwiss data of the lead author. The source data is currently not openly available.

# aggregate_hazard_main.py
Main Skript to aggregate radar hazard data (MESHS, POH) to a larger regular grid (2 and 4km). Uses an aggregation method from the main scClim module.

# untility.py
Folder containing utility functions (subset of internal package used by the scClim project https://scclim.ethz.ch)
