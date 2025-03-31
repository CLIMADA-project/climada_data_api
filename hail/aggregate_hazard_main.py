# -*- coding: utf-8 -*-
"""
Main script to aggregate hazard to new grid

@author: Raphael Portmann

"""
import numpy as np
import sys
from climada import CONFIG
from climada.util.save import save,load

#from climada.hazard import Hazard
sys.path.append(str(CONFIG.local_data.func_dir))
from utility import hazard_from_radar,aggregate_hazard
import time
import pandas as pd
#%%
hazard_filedir = f"{CONFIG.local_data.data_dir}/hazard/radar/v5/"

#%%

""" AGGREGATE HAZARD DATA MESHS"""

#read hazard data MESHS

# set directory
MESHS_dir = hazard_filedir+'MZC/'

#define start and endyear
startyear = 2017
endyear = 2021

#define aggregations (in km)
kms=[1,2,4,8,16,32]

#define aggfunc
aggfunc='max'

#dmgdates
dates=['2017-06-27','2017-07-08','2017-08-01','2019-06-15','30-06-2019','2019-07-01','2021-06-20','2021-06-21','2021-06-28','2021-07-12','2021-07-13','2021-07-24']

#create list of files
filenames_MESH = [MESHS_dir+'MZC_X1d66_'+str(yyyy)+'.nc' for yyyy in np.arange(startyear,endyear+1,1)]

#read data
MESHS_rad, MESHS_xarray = hazard_from_radar(filenames_MESH,varname='MESHS',time_dim = 'time',spatial_dims = ['chy','chx'],country_code=None,month=None,get_xarray=True) # extent=[5.5,10.5,45.5,48])
outfile = f'{MESHS_dir}MZC_2002_2021_1km.p'
#save(outfile, MESHS_rad)
# Aggregate data
for km in kms:
    gridsize = km*1000
    MESHS_agg,MESHS_agg_xr=aggregate_hazard(MESHS_rad, original_grid_epsg = 2056,
                                  extent_new = None,
                                  cell_size_new = gridsize,
                                  projection_new_epsg = 4326,
                                  aggfunc = aggfunc,
                                  treat_zeros_as_nans = True,
                                  return_xr=True,
                                  dates_xr=[pd.Timestamp(d).toordinal() for d in dates])
    outfile = f'{MESHS_dir}MZC_2002_2021_{aggfunc}_{km}km.p'
    # save output
    save(outfile, MESHS_agg)
    outfile_xr = f'{MESHS_dir}MZC_12_events_2017_2021_{aggfunc}_{km}km.nc'
    MESHS_agg_xr=MESHS_agg_xr.rename({'intensity': 'MZC'})
    MESHS_agg_xr.to_netcdf(outfile_xr)

#%%
""" AGGREGATE HAZARD DATA POH """

""" read hazard data"""
# set directory
POH_dir = hazard_filedir+'BZC/'

#define start and endyear
startyear = 2002
endyear = 2021

#define aggregations (in km)
kms=[1,2,4,8,16,32]

#define aggfunc
aggfunc='max'

#create list of files
filenames = [POH_dir+'BZC_X1d66_'+str(yyyy)+'.nc' for yyyy in np.arange(startyear,endyear+1,1)]

POH_rad, POH_xarray = hazard_from_radar(filenames,varname='POH',time_dim = 'time',spatial_dims = ['chy','chx'],country_code=None,month=None,get_xarray=True) # extent=[5.5,10.5,45.5,48])
outfile = f'{POH_dir}BZC_2002_2021_1km.p'
save(outfile, POH_rad)
# Aggregate
for km in kms:
    gridsize = km*1000
    POH_agg,POH_agg_xr=aggregate_hazard(POH_rad, original_grid_epsg = 2056,
                                  extent_new = None,
                                  cell_size_new = gridsize,
                                  projection_new_epsg = 4326,
                                  aggfunc = aggfunc,
                                  treat_zeros_as_nans = True,
                                  return_xr=True,
                                  dates_xr=[pd.Timestamp(d).toordinal() for d in dates])
    outfile = f'{POH_dir}BZC_2002_2021_{aggfunc}_{km}km.p'
    # save output
    save(outfile, POH_agg)
    outfile_xr = f'{POH_dir}BZC_12_events_2017_2021_{aggfunc}_{km}km.nc'
    POH_agg_xr=POH_agg_xr.rename({'intensity': 'BZC'})
    POH_agg_xr.to_netcdf(outfile_xr)

