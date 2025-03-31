"""
compute_centroids.py

This script generates a global set of centroids for use in climate risk modelling, 
distinguishing between land and ocean areas at different spatial resolutions.
It uses Natural Earth shapefiles to define land boundaries, applies coastal buffers,
assigns region IDs and land/ocean classifications, and saves the resulting centroids 
in HDF5 format compatible with CLIMADA.

It runs 4 variants by default:
- LitPop-aligned grid (with and without poles)
- Standard grid (with and without poles)
"""

import os
import sys
from datetime import datetime

# Add parent directory of the current script to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import DATA_DIR

import cartopy.io.shapereader as shpreader
from shapely.ops import unary_union
import shapely.vectorized
from climada.hazard import Centroids


def make_base_centroids(out_file_path, bounds=(-180, -60, 180, 60), res_land_arcsec=150, res_ocean_arcsec=1800,
                        land_buffer=0.1, on_land_buffer=0.02, litpop_aligned=False):
    """Create and save a centroid grid with optional LitPop alignment and polar inclusion."""
    res_land = res_land_arcsec / 3600
    res_ocean = res_ocean_arcsec / 3600

    # Create land centroids
    if litpop_aligned:
        cent_land = Centroids.from_pnt_bounds(
            (-180 + res_land / 2, -90 + res_land / 2, 180 - res_land / 2, 90 - res_land / 2), res_land
        )
    else:
        cent_land = Centroids.from_pnt_bounds(bounds, res_land)

    # Create ocean centroids
    cent_ocean = Centroids.from_pnt_bounds(bounds, res_ocean)

    # Load and merge land polygons
    shpfilename = shpreader.natural_earth(category='physical', name='land', resolution='10m')
    land = shpreader.Reader(shpfilename)
    land_union = unary_union([x.geometry for x in land.records()])

    # Apply land and coastal buffers
    land_buffered = land_union.buffer(land_buffer, resolution=10)
    land_on_land_buffered = land_union.buffer(on_land_buffer, resolution=10)

    # Filter and label land/ocean centroids
    cent_ocean = cent_ocean.select(sel_cen=~shapely.vectorized.contains(land_buffered, cent_ocean.lon, cent_ocean.lat))
    cent_land = cent_land.select(sel_cen=shapely.vectorized.contains(land_buffered, cent_land.lon, cent_land.lat))

    cent_ocean.set_on_land()
    cent_land.set_on_land()
    mask_on_land = shapely.vectorized.contains(land_on_land_buffered, cent_land.lon, cent_land.lat)
    cent_land.gdf["on_land"] = mask_on_land.astype(bool)

    # Combine centroids
    cent = cent_land
    cent.append(cent_ocean)

    # Add region ID and crop to bounds
    cent.set_region_id()
    cent = cent.select(extent=(bounds[0], bounds[2], bounds[1], bounds[3]))
    cent.write_hdf5(out_file_path)


# === Auto-run all 4 variants ===
if __name__ == "__main__":
    date_str = datetime.today().strftime('%m_%Y')
    out_dir = os.path.join(DATA_DIR, 'centroids', date_str)
    os.makedirs(out_dir, exist_ok=True)

    variants = [
        {"litpop_aligned": True,  "include_poles": False},
        {"litpop_aligned": True,  "include_poles": True},
        {"litpop_aligned": False, "include_poles": False},
        {"litpop_aligned": False, "include_poles": True},
    ]

    for variant in variants:
        aligned_str = "litpop_aligned_" if variant["litpop_aligned"] else ""
        poles_str = "" if variant["include_poles"] else "nopoles_"
        file_name = f"earth_centroids_150asland_1800asoceans_distcoast_region_{poles_str}{aligned_str}.hdf5"
        out_file = os.path.join(out_dir, file_name)

        bounds = (-180, -90, 180, 90) if variant["include_poles"] else (-180, -60, 180, 60)
        make_base_centroids(out_file, bounds=bounds, litpop_aligned=variant["litpop_aligned"])

        print(f"✓ Created: {file_name}")
