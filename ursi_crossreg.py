#!/usr/bin/env python
# coding: utf-8

# # load config

from minian.config_crossreg import dpath, minian_path, f_pattern, id_dims, param_t_dist, output_size

# # Load Modules

# In[3]:

import os
import sys
import warnings
sys.path.append(minian_path)
import itertools as itt
import numpy as np
import xarray as xr
import holoviews as hv
import pandas as pd
from holoviews.operation.datashader import datashade, regrid
from minian.cross_registration import (calculate_centroids, calculate_centroid_distance, calculate_mapping,
                                       group_by_session, resolve_mapping, fill_mapping)
from minian.motion_correction import estimate_shifts, apply_shifts
from minian.utilities import open_minian, open_minian_mf
from minian.visualization import AlignViewer
hv.notebook_extension('bokeh', width=100)



# # Allign Videos

# ## open datasets

# In[4]:


minian_ds = open_minian_mf(
    dpath, id_dims, pattern=f_pattern, backend='zarr')


# ## estimate shifts

# In[5]:

temps = minian_ds['Y'].max('frame').compute().rename('temps')
shifts = estimate_shifts(temps, max_sh=param_t_dist, dim='session').compute()
shifts = shifts.rename('shifts')
temps_sh = apply_shifts(temps, shifts).compute().rename('temps_shifted')
shiftds = xr.merge([temps, shifts, temps_sh])


hv.output(size=output_size)
opts_im = {
    'aspect': shiftds.sizes['width'] / shiftds.sizes['height'],
    'frame_width': 500, 'cmap': 'viridis'}
hv_temps = (hv.Dataset(temps).to(hv.Image, kdims=['width', 'height'])
            .opts(**opts_im).layout('session').cols(1))
hv_temps_sh = (hv.Dataset(temps_sh).to(hv.Image, kdims=['width', 'height'])
            .opts(**opts_im).layout('session').cols(1))

hv.output(size=output_size)
opts_im = {
    'aspect': shiftds.sizes['width'] / shiftds.sizes['height'],
    'frame_width': 500, 'cmap': 'viridis'}
window = shiftds['temps_shifted'].isnull().sum('session')
window, temps_sh = xr.broadcast(window, shiftds['temps_shifted'])
hv_wnd = hv.Dataset(window, kdims=list(window.dims)).to(hv.Image, ['width', 'height'])
hv_temps = hv.Dataset(temps_sh, kdims=list(temps_sh.dims)).to(hv.Image, ['width', 'height'])
hv_wnd.opts(**opts_im).relabel("Window") + hv_temps.opts(**opts_im).relabel("Shifted Templates")

# ## apply shifts and set window

# In[8]:

A_shifted = apply_shifts(minian_ds['A'].chunk(dict(height=-1, width=-1)), shiftds['shifts'])


# In[9]:

def set_window(wnd):
    return wnd == wnd.min()
window = xr.apply_ufunc(
    set_window,
    window,
    input_core_dims=[['height', 'width']],
    output_core_dims=[['height', 'width']],
    vectorize=True)


# # Calculate Centroid Distance

# ## calculate centroids

# In[10]:

cents = calculate_centroids(A_shifted, window)

# ## calculate centroid distance

# In[11]:

dist = calculate_centroid_distance(cents, index_dim=None)

# # Get Overlap Across Sessions

# ### threshold overlap based upon centroid distance and generate overlap mappings

# In[12]:

dist_ft = dist[dist['variable', 'distance'] < param_t_dist]
dist_ft = group_by_session(dist_ft)


# In[13]:

mappings = calculate_mapping(dist_ft)
mappings_meta = resolve_mapping(mappings)
mappings_meta_fill = fill_mapping(mappings_meta, cents)
mappings_meta_fill.head()

# ### save overlap mappings to pkl and csv files

# In[14]:

mappings_meta_fill.to_pickle(os.path.join(dpath, "mappings.pkl"))
mappings_meta_fill.to_csv(os.path.join(dpath, "mappings.csv"))


# # View Overlap Across Any 2 Sessions

# ### define session names to be compared in list

# In[15]:

