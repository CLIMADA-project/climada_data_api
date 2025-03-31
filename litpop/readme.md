Centroid files are stored in subdirectories named by date (e.g., `03_2025`, `11_2023`) to indicate when they were generated.

Each subdirectory contains:

- `earth_centroids_150asland_1800asoceans_distcoast_region.hdf5`:  
  Full global coverage, with standard land/ocean grid.

- `earth_centroids_150asland_1800asoceans_distcoast_region_nopoles.hdf5`:  
  Same as above, but excluding polar regions (latitudes beyond ±60°).

The latest version (03_2025) also contains:
- `earth_centroids_150asland_1800asoceans_distcoast_region_litpop_aligned.hdf5`:  
  Grid aligned to the default LitPop resolution (for land only), using a slightly different cell definition.

- `earth_centroids_150asland_1800asoceans_distcoast_region_nopoles_litpop_aligned.hdf5`:  
  LitPop-aligned grid excluding polar regions.

---

## 🆕 Updates in `03_2025`

Compared to the previous version, the current release includes two key improvements:

### 1. **Improved `on_land` Classification**
- In older versions, the `on_land` attribute was computed with no buffer, which caused some land points—especially in regions with complex coastlines—to be classified as ocean.
- The new version uses a small buffer to improve the accuracy of this classification near coasts.

### 2. **LitPop-Aligned Grid (Land Only)**
- This is mainly useful for the river flood hazard as the input netcdf4 are on the same grid as the default litpop gird
- **Key difference**: the LitPop grid defines each cell based on its **center**, whereas the standard CLIMADA centroids use **upper-left corner**.
- This shift avoids misalignment when resampling or merging datasets across different sources.
