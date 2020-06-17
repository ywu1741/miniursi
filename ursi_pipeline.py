#!/usr/bin/env python
# coding: utf-8

# # Setting up

# ## load modules

# In[1]:

get_ipython().run_cell_magic('capture', '', '%load_ext autoreload\n%autoreload 2')
import sys
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMBA_NUM_THREADS"] = "1"
import gc
import psutil
import numpy as np
import xarray as xr
import holoviews as hv
import matplotlib.pyplot as plt
import bokeh.plotting as bpl
import dask.array as da
import pandas as pd
import dask
import datashader as ds
import itertools as itt
import papermill as pm
import ast
import functools as fct
from holoviews.operation.datashader import datashade, regrid, dynspread
from datashader.colors import Sets1to3
from dask.diagnostics import ProgressBar
from IPython.core.display import display, HTML

## import config
from minian.config import minian_path, dpath, subset, interactive, output_size, param_save_minian, param_load_videos, param_denoise, param_background_removal, subset_mc, param_estimate_shift, param_seeds_init, param_pnr_refine, param_ks_refine, param_seeds_merge, param_initialize, param_get_noise, param_first_spatial, param_first_temporal, param_first_merge, param_second_spatial, param_second_temporal

# ## import minian

# In[3]:

from minian.utilities import load_params, load_videos, scale_varr, scale_varr_da, save_variable, open_minian, save_minian, handle_crash, get_optimal_chk, rechunk_like
from minian.preprocessing import remove_brightspot, gradient_norm, denoise, remove_background, stripe_correction
from minian.motion_correction import estimate_shifts, apply_shifts
from minian.initialization import seeds_init, gmm_refine, pnr_refine, intensity_refine, ks_refine, seeds_merge, initialize
from minian.cnmf import get_noise_fft, update_spatial, compute_trace, update_temporal, unit_merge, smooth_sig
from minian.visualization import VArrayViewer, CNMFViewer, generate_videos, visualize_preprocess, visualize_seeds, visualize_gmm_fit, visualize_spatial_update, visualize_temporal_update, roi_draw, write_video

# ## module initialization

# In[4]:

dpath = os.path.abspath(dpath)
if interactive:
    hv.notebook_extension('bokeh')
    pbar = ProgressBar(minimum=2)
    pbar.register()
else:
    hv.notebook_extension('matplotlib')

# # Pre-processing

# ## loading videos

get_ipython().run_cell_magic('time', '', "varr = load_videos(dpath, **param_load_videos)\nchk = get_optimal_chk(varr.astype(float), dim_grp=[('frame',), ('height', 'width')])")

# ## set roi for motion correction

if interactive:
    try:
        subset_mc = list(vaviewer.mask.values())[0]
    except IndexError:
        pass

# ## subset part of video

varr_ref = varr.sel(subset)

# ## glow removal

get_ipython().run_cell_magic('time', '', "varr_min = varr_ref.min('frame').compute()\nvarr_ref = varr_ref - varr_min")

# ## denoise

varr_ref = denoise(varr_ref, **param_denoise)

# ## background removal

varr_ref = remove_background(varr_ref, **param_background_removal)

# ## save result

get_ipython().run_cell_magic('time', '', "varr_ref = varr_ref.chunk(chk)\nvarr_ref = save_minian(varr_ref.rename('org'), **param_save_minian)")

# # motion correction

# ## load in from disk

varr_ref = open_minian(dpath,
                      fname=param_save_minian['fname'],
                      backend=param_save_minian['backend'])['org']

# ## estimate shifts

get_ipython().run_cell_magic('time', '', 'shifts = estimate_shifts(varr_ref.sel(subset_mc), **param_estimate_shift)')

# ## save shifts

get_ipython().run_cell_magic('time', '', "shifts = shifts.chunk(dict(frame=chk['frame'])).rename('shifts')\nshifts = save_minian(shifts, **param_save_minian)")

# ## apply shifts

Y = apply_shifts(varr_ref, shifts)
Y = Y.fillna(0).astype(varr_ref.dtype)

# ## save result

get_ipython().run_cell_magic('time', '', "Y = Y.chunk(chk)\nY = save_minian(Y.rename('Y'), **param_save_minian)")

# # initialization

# ## load in from disk

get_ipython().run_cell_magic('time', '', "minian = open_minian(dpath,\n                     fname=param_save_minian['fname'],\n                     backend=param_save_minian['backend'])")

Y = minian['Y'].astype(np.float)
max_proj = Y.max('frame').compute()
Y_flt = Y.stack(spatial=['height', 'width'])

# ## generating over-complete set of seeds

get_ipython().run_cell_magic('time', '', 'seeds = seeds_init(Y, **param_seeds_init)')

# ## peak-noise-ratio refine

get_ipython().run_cell_magic('time', '', "if interactive:\n    noise_freq_list = [0.005, 0.01, 0.02, 0.06, 0.1, 0.2, 0.3, 0.45]\n    example_seeds = seeds.sample(6, axis='rows')\n    example_trace = (Y_flt\n                     .sel(spatial=[tuple(hw) for hw in example_seeds[['height', 'width']].values])\n                     .assign_coords(spatial=np.arange(6))\n                     .rename(dict(spatial='seed')))\n    smooth_dict = dict()\n    for freq in noise_freq_list:\n        trace_smth_low = smooth_sig(example_trace, freq)\n        trace_smth_high = smooth_sig(example_trace, freq, btype='high')\n        trace_smth_low = trace_smth_low.compute()\n        trace_smth_high = trace_smth_high.compute()\n        hv_trace = hv.HoloMap({\n            'signal': (hv.Dataset(trace_smth_low)\n                       .to(hv.Curve, kdims=['frame'])\n                       .opts(frame_width=300, aspect=2, ylabel='Signal (A.U.)')),\n            'noise': (hv.Dataset(trace_smth_high)\n                      .to(hv.Curve, kdims=['frame'])\n                      .opts(frame_width=300, aspect=2, ylabel='Signal (A.U.)'))\n        }, kdims='trace').collate()\n        smooth_dict[freq] = hv_trace")

seeds, pnr, gmm = pnr_refine(Y_flt, seeds.copy(), **param_pnr_refine)

if gmm:
    display(visualize_gmm_fit(pnr, gmm, 100))

# ## ks refine

get_ipython().run_cell_magic('time', '', "seeds = ks_refine(Y_flt, seeds[seeds['mask_pnr']], **param_ks_refine)")

# ## merge seeds

get_ipython().run_cell_magic('time', '', "seeds_final = seeds[seeds['mask_ks']].reset_index(drop=True)\nseeds_mrg = seeds_merge(Y_flt, seeds_final, **param_seeds_merge)")

# ## initialize spatial and temporal matrices from seeds

get_ipython().run_cell_magic('time', '', "A, C, b, f = initialize(Y, seeds_mrg[seeds_mrg['mask_mrg']], **param_initialize)")

# ## save results

get_ipython().run_cell_magic('time', '', "A = save_minian(A.rename('A_init').rename(unit_id='unit_id_init'), **param_save_minian)\nC = save_minian(C.rename('C_init').rename(unit_id='unit_id_init'), **param_save_minian)\nb = save_minian(b.rename('b_init'), **param_save_minian)\nf = save_minian(f.rename('f_init'), **param_save_minian)")

# # CNMF

# ## loading data

get_ipython().run_cell_magic('time', '', "minian = open_minian(dpath,\n                     fname=param_save_minian['fname'],\n                     backend=param_save_minian['backend'])\nY = minian['Y'].astype(np.float)\nA_init = minian['A_init'].rename(unit_id_init='unit_id')\nC_init = minian['C_init'].rename(unit_id_init='unit_id')\nb_init = minian['b_init']\nf_init = minian['f_init']")

# ## estimate spatial noise

get_ipython().run_cell_magic('time', '', 'sn_spatial = get_noise_fft(Y, **param_get_noise).persist()')

# ## first spatial update

get_ipython().run_cell_magic('time', '', 'A_spatial, b_spatial, C_spatial, f_spatial = update_spatial(\n    Y, A_init, b_init, C_init, f_init, sn_spatial, **param_first_spatial)')

# ## first temporal update

get_ipython().run_cell_magic('time', '', "YrA, C_temporal, S_temporal, B_temporal, C0_temporal, sig_temporal, g_temporal, scale = update_temporal(\n    Y, A_spatial, b_spatial, C_spatial, f_spatial, sn_spatial, **param_first_temporal)\nA_temporal = A_spatial.sel(unit_id = C_temporal.coords['unit_id'])")

# ## merge units

get_ipython().run_cell_magic('time', '', 'A_mrg, sig_mrg, add_list = unit_merge(A_temporal, sig_temporal, [S_temporal, C_temporal], **param_first_merge)\nS_mrg, C_mrg = add_list[:]')

# ## second spatial update

get_ipython().run_cell_magic('time', '', 'A_spatial_it2, b_spatial_it2, C_spatial_it2, f_spatial_it2 = update_spatial(\n    Y, A_mrg, b_spatial, sig_mrg, f_spatial, sn_spatial, **param_second_spatial)')

# ## second temporal update

get_ipython().run_cell_magic('time', '', "YrA, C_temporal_it2, S_temporal_it2, B_temporal_it2, C0_temporal_it2, sig_temporal_it2, g_temporal_it2, scale_temporal_it2 = update_temporal(\n    Y, A_spatial_it2, b_spatial_it2, C_spatial_it2, f_spatial_it2, sn_spatial, **param_second_temporal)\nA_temporal_it2 = A_spatial_it2.sel(unit_id=C_temporal_it2.coords['unit_id'])\ng_temporal_it2 = g_temporal_it2.sel(unit_id=C_temporal_it2.coords['unit_id'])\nA_temporal_it2 = rechunk_like(A_temporal_it2, A_spatial_it2)\ng_temporal_it2 = rechunk_like(g_temporal_it2, C_temporal_it2)")

# ## save results

get_ipython().run_cell_magic('time', '', "A_temporal_it2 = save_minian(A_temporal_it2.rename('A'), **param_save_minian)\nC_temporal_it2 = save_minian(C_temporal_it2.rename('C'), **param_save_minian)\nS_temporal_it2 = save_minian(S_temporal_it2.rename('S'), **param_save_minian)\ng_temporal_it2 = save_minian(g_temporal_it2.rename('g'), **param_save_minian)\nC0_temporal_it2 = save_minian(C0_temporal_it2.rename('C0'), **param_save_minian)\nB_temporal_it2 = save_minian(B_temporal_it2.rename('bl'), **param_save_minian)\nb_spatial_it2 = save_minian(b_spatial_it2.rename('b'), **param_save_minian)\nf_spatial_it2 = save_minian(f_spatial_it2.rename('f'), **param_save_minian)")

# ## visualization output

minian = open_minian(dpath,
                     fname=param_save_minian['fname'],
                     backend=param_save_minian['backend'])
varr = load_videos(dpath, **param_load_videos)
chk = get_optimal_chk(varr.astype(float), dim_grp=[('frame',), ('height', 'width')])
varr = varr.chunk(dict(frame=chk['frame']))

get_ipython().run_cell_magic('time', '', 'generate_videos(\n    minian, varr, dpath, param_save_minian[\'fname\'] + ".mp4", scale=\'auto\')')
