# LitPop Exposure Generator

This script generates country-level and global LitPop exposure files using the [CLIMADA](https://github.com/CLIMADA-project/climada_python) platform. It runs for three exposure types (population, assets, or lit and pop) and either keeps the default grid or aligns the data to a standard climate data grid.

It uses the `LitPop.from_countries` function to generate exposures for each country individually, and then merges them using `LitPop.concat` to produce a global exposure file.

**Note:** To use the `target_grid` functionality for aligned outputs, you currently need to use the following development branch of CLIMADA:  
[`feature/costum_grid_litpop`](https://github.com/CLIMADA-project/climada_python/tree/feature/costum_grid_litpop)
