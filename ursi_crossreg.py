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

# ## visualize alignment

# In[6]:


hv.output(size=output_size)
opts_im = {
    'aspect': shiftds.sizes['width'] / shiftds.sizes['height'],
    'frame_width': 500, 'cmap': 'viridis'}
hv_temps = (hv.Dataset(temps).to(hv.Image, kdims=['width', 'height'])
            .opts(**opts_im).layout('session').cols(1))
hv_temps_sh = (hv.Dataset(temps_sh).to(hv.Image, kdims=['width', 'height'])
            .opts(**opts_im).layout('session').cols(1))


# ## visualize overlap of field of view across all sessions

# In[7]:


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


sess = ['Day1', 'Day2']


# ### view overlapping/non-overlapping cells

# In[16]:


def subset_by_session(sessions, mappings):
    mappings_ma = mappings[mappings['session'][sessions].notnull().all(axis='columns')]
    mappings_non = mappings[
        mappings['group', 'group'].isnull()
        & mappings['session'][sess].notnull().any(axis='columns')]
    return mappings_ma, mappings_non


# In[17]:


mappings_match, mappings_nonmatch = subset_by_session(sess, mappings_meta_fill)
opts_im = {
    'frame_width': 500,
    'aspect': A_shifted.sizes['width'] / A_shifted.sizes['height'],
    'cmap': 'viridis'}
A_dict = dict()
for ss in sess:
    uid_ma = mappings_match[('session', ss)].values
    uid_nm = mappings_nonmatch[('session', ss)].dropna().values
    cent_ma = cents[(cents['session'] == ss) & (cents['unit_id'].isin(uid_ma))]
    cent_nm = cents[(cents['session'] == ss) & (cents['unit_id'].isin(uid_nm))]
    hv_A_ma = hv.Image(
        A_shifted.sel(session=ss, unit_id=uid_ma).sum('unit_id').compute(),
        ['width', 'height']).opts(**opts_im)
    hv_A_nm = hv.Image(
        A_shifted.sel(session=ss, unit_id=uid_nm).sum('unit_id').compute(),
        ['width', 'height']).opts(**opts_im)
    A_dict[(ss, 'matching')] = hv_A_ma
    A_dict[(ss, 'non-matching')] = hv_A_nm


# In[18]:


hv.NdLayout(A_dict, kdims=['session', 'ma']).cols(2)


# In[19]:


mappings_match, mappings_nonmatch = subset_by_session(sess, mappings_meta_fill)
A_dict = dict()
cent_dict = dict()
for cur_ss in sess:
    cur_uid_ma = mappings_match[[('meta', d) for d in group_dim] + [('session', cur_ss)]]
    cur_uid_nm = mappings_nonmatch[[('meta', d) for d in group_dim] + [('session', cur_ss)]].dropna()
    cur_uid_ma.columns = cur_uid_ma.columns.droplevel()
    cur_uid_nm.columns = cur_uid_nm.columns.droplevel()
    cur_uid_ma = cur_uid_ma.rename(columns={cur_ss:'unit_id'})
    cur_uid_nm = cur_uid_nm.rename(columns={cur_ss:'unit_id'})
    cur_uid_ma['session'] = cur_ss
    cur_uid_nm['session'] = cur_ss
    cur_cents_ma = cur_uid_ma.merge(cents)
    cur_cents_nm = cur_uid_nm.merge(cents)
    A_ma_dict = dict()
    A_nm_dict = dict()
    for igrp, grp_ma in cur_uid_ma.groupby(group_dim + ['session']):
        cur_keys = {d: k for d, k in zip(group_dim + ['session'], igrp)}
        A_sub = A_shifted.sel(**cur_keys)
        A_ma = A_sub.sel(unit_id=grp_ma['unit_id'].values)
        grp_nm = cur_uid_nm.query(" and ".join(["==".join((d, "'{}'".format(k))) for d, k in cur_keys.items()]))
        A_nm = A_sub.sel(unit_id=grp_nm['unit_id'].values)
        A_ma_dict[igrp] = hv.Image(A_ma.sum('unit_id').compute(), kdims=['width', 'height'])
        A_nm_dict[igrp] = hv.Image(A_nm.sum('unit_id').compute(), kdims=['width', 'height'])
    hv_A_ma = hv.HoloMap(A_ma_dict, kdims=group_dim + ['session'])
    hv_A_nm = hv.HoloMap(A_nm_dict, kdims=group_dim + ['session'])
    hv_cent_ma = hv.Dataset(cur_cents_ma).to(hv.Points, kdims=['width', 'height'])
    hv_cent_nm = hv.Dataset(cur_cents_nm).to(hv.Points, kdims=['width', 'height'])
    hv_A = hv.HoloMap(dict(match=hv_A_ma, nonmatch=hv_A_nm), kdims=['matching']).collate()
    hv_cent = hv.HoloMap(dict(match=hv_cent_ma, nonmatch=hv_cent_nm), kdims=['matching']).collate()
    A_dict[cur_ss] = hv_A
    cent_dict[cur_ss] = hv_cent
hv_A = hv.HoloMap(A_dict, kdims=['session']).collate()
hv_cent = hv.HoloMap(cent_dict, kdims=['session']).collate()


# In[ ]:


from holoviews.operation.datashader import regrid
(regrid(hv_A).opts(plot=dict(width=752, height=480), style=dict(cmap='Viridis'))).layout(['animal', 'matching']).cols(2)

# In[ ]:
