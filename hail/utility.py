# -*- coding: utf-8 -*-
"""
Created on Thu Apr 20 11:49:23 2023

Utility functions for Paper:
Portmann R., Schmid T., Villiger L., Bresch D., Calanca P. Modelling crop hail damage footprints
with single-polarization radar: The roles of spatial resolution, hail intensity,
and cropland density, submitted to Natural Hazards and Earth System Sciences.

@authors: Raphael Portmann, Timo Schmid, Leonie Villiger
"""
import pickle
import pandas as pd
import numpy as np
import matplotlib
import geopandas
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
from cartopy.io import shapereader
import cartopy.feature as cf
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import sys
import xarray as xr
from climada.entity import Exposures
from climada.hazard import Hazard, Centroids
from climada.engine import Impact

import shapely.geometry as sg

import geopandas as gpd
from pyproj import CRS
from scipy import sparse
import copy
import warnings

#define translations of names
en_names={'Weizen_Mais_Gerste_Raps': 'field crops',
          'Weizen_Mais_Raps_Gerste': 'field crops',
          'wheat_maize_rapeseed_barley': 'field crops',
          'wheat_maize_barley_rapeseed': 'field crops',
          'Weizen': 'wheat',
          'Mais': 'maize',
          'Raps': 'rapeseed',
          'Gerste':'barley',
          'Reben': 'grapevine'}

#data directory
data_dir='C:/Users/F80840370/projects/scClim/climada/scClim/subproj_D/papers/NHESS/code_and_data/data/'


# Hazard
def hazard_from_radar(files, varname='MESHS', time_dim='time', forecast_init=None,
                      ensemble_dim=None, spatial_dims = None, country_code=None,
                      extent=None, subdaily = False, month=None, ignore_date=False,
                      n_year_input=None, get_xarray=False):
    """Create a new Hail hazard from MeteoCH radar data
    or COSMO HAILCAST ouput (single- or multi-member)

    Parameters
    ----------
    files : list of str or xarray Dataset
        list of netcdf filenames (string) or xarray Dataset object
    varname : string
        the netcdf variable name to be read from the file
    time_dim : str
        Name of time dimension, default: 'time'
    forecast_init : datetime object
        List with datetimes of forecast initializations,
        needs to have same length as time, default: None
    ensemble_dim : str
        Name of ensemble dimension, default: None
    spatial_dims : list of str
        Names of spatial dimensions
    country_code : int
        ISO 3166 country code to filter the data
    extent : list / array
        [lon_min, lon_max, lat_min, lat_max]
    ignore_date : boolean
        If True: ignores netcdf dates (e.g. for synthetic data).
    n_year_input : int
        Number of years: will only be used if ignore_date=True
    Returns
    -------
    haz : Hazard object
        Hazard object containing radar data with hail intensity (MESHS)
    """

    #Initialize default values
    if spatial_dims is None: spatial_dims = ['chy','chx']

    #read netcdf if it is given as a path
    if type(files) == xr.core.dataset.Dataset:
        netcdf = files
    else:
        netcdf = xr.open_mfdataset(files, concat_dim=time_dim, combine='nested',
                                   coords='minimal')

    #select month of the year if given
    if month:
        grouped=netcdf.groupby("time.month")
        netcdf=grouped[int(month)]

    #Cut data to selected country/area only
    if extent:
        lon_min, lon_max, lat_min, lat_max = extent
        lon_cond = np.logical_and(netcdf.lon >= lon_min, netcdf.lon <= lon_max)
        lat_cond = np.logical_and(netcdf.lat >= lat_min, netcdf.lat <= lat_max)
        netcdf = netcdf.where(np.logical_and(lat_cond,lon_cond),drop=True)

    # #stack data
    # stacked = netcdf.stack(new_dim=spatial_dims)

    # if country_code:
    #     c_code = util.coordinates.get_country_code(stacked.lat,stacked.lon)
    #     stacked = stacked.assign_coords(country_code=("new_dim",c_code))
    #     stacked = stacked.where(stacked.country_code==country_code,drop=True)

    #Select variable and set units
    varname_xr = varname #by default the varname corresponds to the xr name
    if varname == 'MESHS' or varname == 'MESHS_4km':
        varname_xr = 'MZC'
        unit = 'mm'
    elif varname == 'MESHSdBZ' or varname == 'MESHSdBZ_p3':
        varname_xr = 'MESHSdBZ'
        unit = 'mm'
    elif varname == 'POH':
        varname_xr = 'BZC'
        unit = '%'
    elif 'DHAIL' in varname:
        unit = 'mm'
    elif varname == 'dBZ' or varname =='dBZfiltered':
        varname_xr = 'CZC'
        unit = 'dBZ'
        # Filter values for efficient calculation. dBZ<40 are set to zero
        netcdf = netcdf.where(netcdf[varname_xr]>40,0)
    elif varname == 'possible_hail':
        unit = '[ ](boolean)'
    elif varname == 'durPOH':
        varname_xr = 'BZC80_dur'
        netcdf[varname_xr] = netcdf[varname_xr]*5 #times 5 to get minutes
        unit = '[min]'
    elif varname == 'MESHSweigh':
        unit = 'mm (scaled by duration)'
    elif varname == 'HKE':
        unit = 'Jm-2'
    elif varname == 'crowd' or varname=='crowdFiltered':
        warnings.warn('use smoothed data for crowd-sourced data')
        varname_xr = 'h_smooth'
        unit = 'mm'
    elif varname == 'E_kin' or varname=='E_kinCC': #E_kin from Waldvogel 1978, or Cecchini 2022
        varname_xr = 'E_kin'
        unit = 'Jm-2'
    elif varname == 'VIL':
        unit = 'g/m2'
        varname_xr = 'dLZC'
        # Filter values for efficient calculation. VIL<10g/m2 are set to zero
        netcdf = netcdf.where(netcdf[varname_xr]>10,0).round(0)
    else:
        raise ValueError(f'varname "{varname}" is not implemented at the moment')

    #prepare xarray with ensemble dimension to be read as climada Hazard
    if ensemble_dim:
        # omit extent if ensemble_dim is given
        if extent:
            warnings.warn("Do not use keyword extent in combination with "
                          "ensemble_dim. Plotting will not work.")
        # omit igonore_date if ensemble_dim is given
        if ignore_date:
            warnings.warn('Do not use keyword ignore_date in combination with '
                          'ensemble_dim. Event names are set differently.')
        # stack ensembles along new dimension
        netcdf = netcdf.stack(time_ensemble=(time_dim, ensemble_dim))
        # event names
        if forecast_init: #event_name = ev_YYMMDD_ensXX_init_YYMMDD_HH
            n_member, = np.unique(netcdf[ensemble_dim]).shape
            forecast_init = np.repeat(forecast_init, n_member)
            if netcdf[time_dim].size != len(forecast_init):
                warnings.warn("Length of forecast_init doesn't match time.")
            event_name = np.array([f"{pd.to_datetime(ts).strftime('ev_%y%m%d')}_ens{ens:02d}_{init.strftime('init_%y%m%d_%H')}"
                                   for (ts,ens),init in zip(netcdf.time_ensemble.values, forecast_init)])
        else: #event_name = ev_YYMMDD_ensXX
            event_name = np.array([f"{pd.to_datetime(ts).strftime('ev_%y%m%d')}_ens{ens:02d}"
                                   for ts,ens in netcdf.time_ensemble.values])
        #convert MultiIndex to SingleIndex
        netcdf = netcdf.reset_index('time_ensemble')
        netcdf = netcdf.assign_coords({'time_ensemble':netcdf.time_ensemble.values})
        # remove duplicates along new dimension for variables that are identical across members
        netcdf['lon'] = netcdf['lon'].sel(time_ensemble=0, drop=True)
        netcdf['lat'] = netcdf['lat'].sel(time_ensemble=0, drop=True)

    # get number of events and create event ids
    n_ev = netcdf[time_dim].size
    event_id = np.arange(1, n_ev+1, dtype=int)

    if ignore_date:
        n_years = n_year_input
        if 'year' in netcdf.coords:
            event_name = np.array(['ev_%d_y%d'%i for i in zip(event_id,netcdf.year.values)])
        else:
            event_name = np.array(['ev_%d'%i for i in event_id])
    elif ensemble_dim:
        n_years = netcdf[time_dim].dt.year.max().values-netcdf[time_dim].dt.year.min().values + 1
    else:
        n_years = netcdf[time_dim].dt.year.max().values-netcdf[time_dim].dt.year.min().values + 1
        if subdaily:
            event_name = netcdf[time_dim].dt.strftime("ev_%Y-%m-%d_%H:%M").values
        else:
            event_name = netcdf[time_dim].dt.strftime("ev_%Y-%m-%d").values

    #Create Hazard object
    if ensemble_dim:
        event_dim = 'time_ensemble'
    else:
        event_dim = time_dim
    coord_vars = dict(event=event_dim,longitude='lon',latitude='lat')
    haz = Hazard.from_xarray_raster(netcdf,'HL',unit,intensity=varname_xr,
                                    coordinate_vars=coord_vars)
    #set correct event_name, frequency, date
    haz.event_name = event_name
    haz.frequency = np.ones(n_ev)/n_years
    if ignore_date:
        haz.date = np.array([], int)
    if ensemble_dim:
        haz.date = np.array([pd.to_datetime(ts).toordinal() for ts in netcdf[time_dim].values])

    netcdf.close()
    haz.check()

    if get_xarray:
        return haz,netcdf
    else:
        return haz

#%% Regridding
def add_zero_values(merged):
    """ Add for each grid cell of output grid, specified by 'index_right'
    in merged, rows with intensity zero such that the total number
    values for the aggregation is equal to n=gridsize_output**2/gridsize_input**2


    Parameters
    ----------
    merged : geopandas.GeoDataframe
        merged dataframe of input data and output grid, with m values per grid cell

    Returns
    -------
    new_merged : geopandas.GEoDataframe
        merged datafarame with n-m zero values added for each grid cell
    """
    dates = []
    indices_right = []
    x = []
    y = []
    intensity = []

    nmax=np.nanmax(merged.groupby(['date','index_right']).size())
    print(nmax)
    for (date, index), count in merged.groupby(['date','index_right']).size().loc[merged.groupby(['date','index_right']).size()<16].iteritems():

        dates = dates + list(np.ones(nmax-count)*date)
        indices_right = indices_right + list(np.ones(nmax-count)*index)
        intensity = intensity + list(np.zeros(nmax-count))

        #geometry
        geometry = merged.loc[merged['index_right'] == index]['geometry']
        x = x + list(np.ones(nmax-count)*geometry.x.values[0])
        y = y + list(np.ones(nmax-count)*geometry.y.values[0])

    gdf=gpd.GeoDataFrame({'intensity': intensity,
                        'date': dates, 'index_right': indices_right},
                        geometry = gpd.points_from_xy(x,y), crs=merged.crs)

    new_merged = pd.concat([merged, gdf])

    return new_merged

def aggregate_hazard(hazard_in, original_grid_epsg = 2056, extent_new = None, cell_size_new = 2000,
                     projection_new_epsg = 4326, aggfunc = 'max', treat_zeros_as_nans = True,
                     return_xr=False,dates_xr=None):
    """Aggregating a hazard object to a coarser grid


    Parameters
    ----------
    hazard_in : climada.hazard
        Climada hazard to aggregate to coarser grid
    original_grid_epsg : int, optional
        EPSG number of the original coordinate reference sytem
        of the hazard. The default is 2056.
    extent_new : list of ints, optional if original_grid_epsg is 2056.
        Extent of the new grid (xmin,ymin,xmax,ymax). The default is None.
    cell_size_new : float, optional
        Cell size of the new grid (in units of the original CRS). The default is 2000.
    projection_new_epsg : int, optional
        projection of the centroid coordinates of the new hazard. The default is 4326.
    aggfunc : str, optional
        Function to be used for aggregation. The default is 'mean'.
    treat_zeros_as_nans : boolean, optional
        If True, treat zero values as nans and neglect for aggregation
        If False, treat zero values as zeros and include for aggregation (time consuming).
        The default is True.
    return_xr: boolean, optional
        If True, return the aggregated hazard also as xarray.Dataset
        If False, only return hazard

    Raises
    ------
    ValueError
        If aggregation function is 'max' and treat_zeros_as_nans is False,
        an error is raised to avoid unnecessary time consuming computation.

    Returns
    -------
    hazard_out : climada.hazazrd
        Climada hazard on an aggregated grid

    """


    original_grid_epsg = int(original_grid_epsg)
    original_crs = CRS.from_epsg(original_grid_epsg)
    projection_new_epsg = int(projection_new_epsg)
    proj_new_crs=CRS.from_epsg(projection_new_epsg)

    intensities=[] #list to store new intensity values
    xr_out_list=[] #list to store xarray; only needed if return_xr=True
    if dates_xr is None:
        dates_xr=hazard_in.date

    if aggfunc == 'max' and treat_zeros_as_nans == False:
        raise ValueError('Set treat_zeros_as_nans for aggfunc = "max" to avoid uneccesary slow down of the code')

    if treat_zeros_as_nans == False:
        warnings.warn('treat_zeros_as_nans = False is currently very slow.')

    # create empty output grid
    print(f'create empty grid with extent {extent_new}, cell size: {cell_size_new}')
    cell, crs, extent = create_empty_grid(epsg = original_grid_epsg,
                                             cell_size = cell_size_new, extent = extent_new)

    # create a geodataframe with all nonzero values of the hazard intensity over all dates
    # project grid back to original data if not the same
    gdf = gdf_from_hazard(hazard_in)

    # reproject geometry to original grid if hazard grid and original grid are not of identical projection
    if hazard_in.centroids.crs.to_epsg() != original_grid_epsg:
            gdf = gdf.to_crs(crs=original_crs)

    print('Merge hazard with output grid...')
    # merge hazard intensity data with output grid
    merged = gpd.sjoin(gdf, cell, how='left')

    # if missing values have to be treated as zeros add required columns to the dataframe
    if treat_zeros_as_nans == False:
        merged = add_zero_values(merged)

    print(f'Dissolve hazard intensity in output grid using the following aggregation function: {aggfunc}')
    # dissolve orignal intensity data in the new grid using the user specified aggfunc
    dissolve = merged.dissolve(by=['event_id','index_right'], aggfunc={
                "intensity": aggfunc})

    # loop over events and create sparse matrix of hazard intensities for the new grid
    year_now = 0 # counter to catch year changes
    if hazard_in.event_id.shape != hazard_in.date.shape:
        sys.exit("Number of events and dates in hazard are not equal. Abort hazard aggregation.")
    for event, date in zip(hazard_in.event_id, hazard_in.date):
        # print year first time it appears
        year = pd.Timestamp.fromordinal(date).year
        if year > year_now:
            year_now = year
            print(f"Aggregating hazard data from {year}.")

        # since gdf is produced from hazard_in it should always contain the event_id
        # instead, check if event still exists after dissolve (events with zero intensity
        # in the domain of extent_new are lost through the aggregation)
        if event in dissolve.index.get_level_values(0):

            #create deep copy of output grid
            cell_now=cell.copy(deep = True)

            #select the event subset of the dissolved gdf
            dissolve_now=dissolve.loc[event, :] # multi-index, thus two indices given

            #fill output cell with new intensities
            cell_now.loc[dissolve_now.index, 'intensity'] = dissolve_now['intensity'].values

            #create intensity sparse matrix
            cell_now=cell_now.fillna(0)
            intensities.append(sparse.csr_matrix(cell_now['intensity'].values))

            if return_xr == True:

                if date in dates_xr:
                    print(pd.Timestamp.fromordinal(date))
                    #create deep copy of data
                    cell_xr=cell_now.copy(deep = True)
                    cell_xr['geometry'] = cell_now.geometry.centroid
                    cell_xr["chx"] = cell_xr.geometry.x
                    cell_xr["chy"] = cell_xr.geometry.y
                    cell_xr = cell_xr.round({'chx': 0, 'chy': 0})
                    cell_xr['geometry'] = gpd.points_from_xy(cell_xr.chx, cell_xr.chy)

                    #get lat lon values
                    geometry_latlon=cell_xr['geometry'].to_crs(crs=CRS.from_epsg(int(4326)))
                    cell_xr["lon"]=geometry_latlon.geometry.x
                    cell_xr["lat"]=geometry_latlon.geometry.y

                    cell_multiindex = cell_xr.drop(columns='geometry').set_index(['chy','chx'])
                    cell_xarray=cell_multiindex.to_xarray().set_coords(('chy','chx'))
                    cell_xarray = cell_xarray.expand_dims(time=[pd.Timestamp.fromordinal(date)])
                    xr_out_list.append(cell_xarray)
        else:
            intensities.append(sparse.csr_matrix(np.zeros(len(cell))))

    #stack sparse matrices together
    intensities_all = sparse.vstack(intensities)

    #compute hazard centroids
    cell.geometry = cell.geometry.centroid

    # if projection of the new centroids is not the same as coordinate reference
    # system of the original grid, project centroids to new crs
    if projection_new_epsg != original_grid_epsg:
        cell = cell.to_crs(crs=proj_new_crs)
    centroids = Centroids(lat=cell.geometry.y.to_numpy(copy=True),
                          lon=cell.geometry.x.to_numpy(copy=True),
                          geometry=cell.geometry)
    #centroids=Centroids.from_geodataframe(cell)

    # get new hazard with aggregated intensity and new centroids
    hazard_out = copy.deepcopy(hazard_in)
    hazard_out.centroids = centroids
    hazard_out.intensity = intensities_all

    # adjust shape of hazard.fraction (to make hazard.check() pass) in case it contains no data
    if hazard_in.fraction.data.shape[0] == 0:
        hazard_out.fraction = sparse.csr_matrix(np.zeros(hazard_out.intensity.shape))
    else:
        print("Shape of aggregated hazard's intensity and fraction disagree. Hazard.check() will fail.")

    if return_xr==True:
        xr_out = xr.concat(xr_out_list, dim = 'time')
    else:
        xr_out = None
    return hazard_out, xr_out

def gdf_from_hazard(hazard):
    """Create GeoDataFrame from hazard object with columns 'intensity', 'date', 'event_id', and hazard centroids as geometry

    Parameters
    ----------
    hazard : climada.hazard
        Climada hazard
    Returns
    -------
    gdf : pandas.GeoDataFrame
        geodataframe with hazard information

    """

    #select date and centroid indices
    i_dates,i_centr=hazard.intensity.nonzero()

    #create gdf of geometry
    geometry = gpd.points_from_xy(hazard.centroids.lon[i_centr], hazard.centroids.lat[i_centr])


    gdf=gpd.GeoDataFrame({'intensity': np.squeeze(np.asarray(hazard.intensity[i_dates,i_centr])),
                              'date': hazard.date[i_dates],
                              'event_id': hazard.event_id[i_dates]},
                             geometry = geometry, crs=hazard.centroids.crs)

    return gdf


def create_empty_grid(epsg=2056, cell_size = 1000, extent = None):
   """ get an empty grid as geopandas dataframe based on passed epsg, resolution, and grid size

   Parameters
   ----------
       epsg: int
           String denoting the required coordinate system (EPSG format)
       cell_size: float or int
           size of the grid cells either in the unit of the specified coordinate system
       extent: list or tuple
           extent of the grid (xmin, ymin, xmax, ymax)
   Returns
   ----------
       cell: geopandas.GeoDataFrame
           a GeoDataFrame with each grid cell of the 1x1km regular grid represented as polygon.
   """

   # specify extent of the grid (here: LV95 bounds)
   if epsg == 2056:
       xmin, ymin, xmax, ymax = (2255000, 840000, 2964000, 1479000)
       if extent is not None:
           warnings.warn('Extent of grid EPSG 2056 is predefined. Argument extent is ignored.')
   else:
       xmin, ymin, xmax, ymax = extent

   # create the cells in a loop
   grid_cells = []
   for x0 in np.arange(xmin, xmax+cell_size, cell_size ):
       for y0 in np.arange(ymin, ymax+cell_size, cell_size):
           #bounds
           x1 = x0+cell_size
           y1 = y0+cell_size
           grid_cells.append(sg.box(x0, y0, x1, y1)  )


   crs=CRS.from_epsg(int(epsg))

   #create geopandas.GeoDataFrame
   cell = gpd.GeoDataFrame(grid_cells, columns=['geometry'],
                                    crs = crs) #"EPSG:2056")

   return cell, crs, extent
