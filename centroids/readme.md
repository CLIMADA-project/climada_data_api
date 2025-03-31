# `compute_centroids.py`

This script generates global centroid grids for use in hazards generation **CLIMADA**. It distinguishes between land and ocean areas, applies different resolutions, assigns region IDs, and saves the output in `.hdf5` format.

It automatically creates **four versions** of the centroid grid:

1. **LitPop-aligned grid**, without polar regions, aligned to the litpop grid, which places points at the *centre of each grid cell*
2. **LitPop-aligned grid**, full global extent, aligned to the litpop grid
3. **Standard grid**, without polar regions, aligned to a typical climate data grid, which places points at the *edge of each grid cell*
4. **Standard grid**, full global extent

---

## ✅ What It Does

- Creates centroids over a specified geographic bounding box.
- Uses:
  - **High resolution** for land: `150 arcseconds` (~4.2 km)
  - **Low resolution** for ocean: `1800 arcseconds` (~50 km)
- Applies geographic buffers to:
  - Extend the land zone (`land_buffer`)
  - Classify centroids as "on land" (`on_land_buffer`)
- Assigns:
  - `region_id` based on admin boundaries
  - `on_land` flag
- Supports polar filtering

---

## 💡 LitPop Alignment

When `litpop_aligned=True`, land centroids are aligned with the **LitPop grid**. This means grid cells are centered (e.g., 0.02083°, 0.0625°, etc.) rather than beginning at 0°.  
Useful for compatibility with the standard litpop grid, as well as the river flood hazard data

---

## 📁 Output Files

All files are saved to the `centroids/` folder in your `DATA_DIR`, and include the date in the filename. Example outputs:

- `earth_centroids_150asland_1800asoceans_distcoast_region_nopoles_litpop_aligned_20250330.hdf5`
- `earth_centroids_150asland_1800asoceans_distcoast_region_litpop_aligned_20250330.hdf5`
- `earth_centroids_150asland_1800asoceans_distcoast_region_nopoles_20250330.hdf5`
- `earth_centroids_150asland_1800asoceans_distcoast_region_20250330.hdf5`

---


