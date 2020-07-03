### VASSAR URSI 2020 MINISCOPE PARAMETERS ###
# -*- coding: utf-8 -*-

import numpy as np
# Path that contains the minian folder (should be "." if working in minian env)
minian_path = "."

# Directory to location of videos
dpath = "./videos/Animal_14/Day_4_FC"

# Determines how videos are cropped in terms of height, width, and length
subset = dict(frame=slice(0,None))

# Determines if you want visual output
interactive = False
output_size = 100

# This is where you specify where resulting data is saved. 'dpath' is the
# folder where you want the data (which is by default set to the folder you
# are calling the data from). 'fname' is the name of the folder where the
# output of the run will be saved. 'meta_dict' labels the data structure
# (where 1 is nested in 2 which is nested in 3). Lastly, 'overwrite' should
# be set to True for exploration, but be careful during data processing
# as you don't want to accidentally lose anything.
param_save_minian = {
    'dpath': dpath,
    'fname': 'pipeline_output',
    'backend': 'zarr',
    'meta_dict': dict(session=-1, animal=-2),
    'overwrite': True}

### PRE-PROCESSING PARAMETERS ###

# Many of these parameters call methods and functions that are described in
# more detail in the original noted pipeline. The ones here are all the
# defaults.

# Describes how videos are called into the program. 'pattern' is a regex
# that in this case calls any .avi file, but you can change it to be more
# specific. 'downsample' downsamples the video by a factor of frame = x.
param_load_videos = {
    'pattern': '\.avi$',
    'dtype': np.uint8,
    'downsample': dict(frame=2,height=1,width=1),
    'downsample_strategy': 'subset'}

# Describes how the denoising is accomplished.'ksize' should be set to about
# the radius of an average cell in the video in pixels. Note 'ksize' can only
# be set to odd numbers.
## CELL SIZE NEEDED
param_denoise = {
    'method': 'median',
    'ksize': 19}

# Describes how background noise is removed. 'wnd' should be set to the
# expected size of the largest cell diameter in pixels.
## CELL SIZE NEEDED
param_background_removal = {
    'method': 'tophat',
    'wnd': 40}

# Describes some parameters for motion correction. 'max_shift' is how many
# pixels are trimmed around the edge while 'on' determines which frame is
# being used as the template.
subset_mc = None
param_estimate_shift = {
    'dim': 'frame',
    'max_sh': 20}

### INITIALIZATION PARAMETERS ###

# This function defines how seeds (local maxima of luminescence) are
# initially identified. 'wnd_size' is the number of frames in each subset video
# and should not be larger than the total number of frames. 'method'
# determines if the process is done sequentially (rolling) or randomly
# (random). 'stp_size' is the size of the window in the rolling method.
# 'nchunk' is the number of chunks used in the random method. max_wnd should
# be the radius of the largest cell you want to detect. 'diff_thres' is a
# minimal difference across frames to determine if an object is a seed
# or artifact. Note that in deep brain regions, increasing 'wnd_size' and
# 'stp_size' will make the process faster and cleaner.
## CELL SIZE NEEDED
param_seeds_init = {
    'wnd_size': 1000,
    'method': 'rolling',
    'stp_size': 500,
    'nchunk': 100,
    'max_wnd': 19,
    'diff_thres': 2}

# Defines the peak-to-noise ratio. This is put in 'noise_freq' once it is
# determined by examination of the initial seeds (you'll probably come back
# and tweak this).
param_pnr_refine = {
    'noise_freq': 0.35,
    'thres': 1,
    'med_wnd': None}

# Defines the significance value ('sig') of a Kolmogorov-Smirnov test that takes
# the remaining seeds and elminates those with a normal distribution of
# flourescence (as it should be somewhat bimodal).
param_ks_refine = {
    'sig': 0.05}

# Defines how initial seeds are merged together into spatial objects based
# on spatial and temporal correlation. 'thres_dist' is the threshold for
# Euclidean distnace between pairs of seeds. 'thres_corr' is the threshold
# for Pearson correlations between pairs of seeds (should be relatively high)
# 'noise_freq' should be the same as defined in param_pnr_refine.
param_seeds_merge = {
    'thres_dist': 5,
    'thres_corr': 0.7,
    'noise_freq': 0.35}

# Defines how pixels are included or excluded from objects created around
# the found seeds. "wnd" determines the window size for calculating
# correlation with other pixels for efficiency, ‘thres_corr’ determines
# which pixels are not part of the cell. ‘noise_freq’ should again be the
# same as previous functions.
param_initialize = {
    'thres_corr': 0.8,
    'wnd': 19,
    'noise_freq': 0.35}

### CNMF PARAMETERS ###

# These parameters actually determine what is counted as a neuron.
# MAKE SURE YOU'RE CHECKING THE PLOTS ALONG THE WAY WHILE OPTIMIZING.
# The cited methods are again best described in the original annotated pipeline.

# Estimates noise to provide noise parameter for CNMF. The upper bound of
# 'noise_range' should be left at 0.5, but the lower can be determined by
# PSD plots.
param_get_noise = {
    'noise_range': (0.1, 0.5),
    'noise_method': 'logmexp'}

# Provides the parameters for the spatial update. 'sparse_panel' is the
# sparsity penalty that should optimzie the binary spatial matrix. 'd1_wnd'
# determines the window size in which units are updated, should be set to
# the radius of the largest cell.
## CELL SIZE NEEDED
param_first_spatial = {
    'dl_wnd': 19,
    'sparse_penal': 0.2,
    'update_background': True,
    'normalize': True,
    'zero_thres': 'eps'}

# Provides parameters for the temporal update, which are all specified in
# detail in the original notebook. 'add_lag' should be set to the approximate
# decay time of the signal in frames. 'use_spatial' should be left alone,
# as turning it to TRUE is very computationally demanding. 'jac_thres'
# determines what proportion of a cell's spatial footprint needs to be covered
# to be considered "overlapping": the default is good for data that is compact
# in cells. 'p' should be set to 2 if the calcium transients have an observable
# rise time and should be set to 1 id the rise-time is faster than the sampling
# rate. 'sparse_penal' can be tweaked to adjust the balance between fidelity
# and sparsity. 'noise_freq' is the threshold for determining noise in the
# 'update_temporal' function. 'use_smooth' determines if noise is accounted
# for in the first place. 'max_iters' determines how many times the compute
# tries to solve a small issue before throwing up a warning while 'scs_fallback'
# controls whether an scs attempt should be made (you shouldn't need to tweak
# these). Lastly, the 'zero_thres' is set to eliminate small values.
param_first_temporal = {
    'noise_freq': 0.35,
    'sparse_penal': 0.25,
    'p': 1,
    'add_lag': 20,
    'use_spatial': False,
    'jac_thres': 0.2,
    'zero_thres': 1e-8,
    'max_iters': 200,
    'use_smooth': True,
    'scs_fallback': False,
    'post_scal': True}

# Again merges components into the same cell. ‘thres_corr’ is the pearson
# threshold to determine which units belong in the same cell.
param_first_merge = {
    'thres_corr': 0.8}

# Same concepts as first spatial update and first temporal update.
param_second_spatial = {
    'dl_wnd': 19,
    'sparse_penal': 0.2,
    'update_background': True,
    'normalize': True,
    'zero_thres': 'eps'}

param_second_temporal = {
    'noise_freq': 0.35,
    'sparse_penal': 0.25,
    'p': 1,
    'add_lag': 20,
    'use_spatial': False,
    'jac_thres': 0.2,
    'zero_thres': 1e-8,
    'max_iters': 500,
    'use_smooth': True,
    'scs_fallback': False,
    'post_scal': True}
