#!/usr/bin/env python
# coding: utf-8

# # Setting up

# ## load modules

# In[1]:

get_ipython().run_cell_magic('capture', '', '%load_ext autoreload\n%autoreload 2\nimport sys\nimport os\nos.environ["OMP_NUM_THREADS"] = "1"\nos.environ["MKL_NUM_THREADS"] = "1"\nos.environ["OPENBLAS_NUM_THREADS"] = "1"\nos.environ["NUMBA_NUM_THREADS"] = "1"\nimport gc\nimport psutil\nimport numpy as np\nimport xarray as xr\nimport holoviews as hv\nimport matplotlib.pyplot as plt\nimport bokeh.plotting as bpl\nimport dask.array as da\nimport pandas as pd\nimport dask\nimport datashader as ds\nimport itertools as itt\nimport papermill as pm\nimport ast\nimport functools as fct\nfrom holoviews.operation.datashader import datashade, regrid, dynspread\nfrom datashader.colors import Sets1to3\nfrom dask.diagnostics import ProgressBar\nfrom IPython.core.display import display, HTML')

## import config
import minian.config
from minian.config import minian_path, dpath, subset, interactive, output_size, param_save_minian, param_load_videos, param_denoise, param_background_removal, subset_mc, param_estimate_shift, param_seeds_init, param_pnr_refine, param_ks_refine, param_seeds_merge, param_initialize, param_get_noise, param_first_spatial, param_first_temporal, param_first_merge, param_second_spatial, param_second_temporal

# ## import minian

# In[3]:

get_ipython().run_cell_magic('capture', '', 'sys.path.append(minian_path)\nfrom minian.utilities import load_params, load_videos, scale_varr, scale_varr_da, save_variable, open_minian, save_minian, handle_crash, get_optimal_chk, rechunk_like\nfrom minian.preprocessing import remove_brightspot, gradient_norm, denoise, remove_background, stripe_correction\nfrom minian.motion_correction import estimate_shifts, apply_shifts\nfrom minian.initialization import seeds_init, gmm_refine, pnr_refine, intensity_refine, ks_refine, seeds_merge, initialize\nfrom minian.cnmf import get_noise_fft, update_spatial, compute_trace, update_temporal, unit_merge, smooth_sig\nfrom minian.visualization import VArrayViewer, CNMFViewer, generate_videos, visualize_preprocess, visualize_seeds, visualize_gmm_fit, visualize_spatial_update, visualize_temporal_update, roi_draw, write_video')

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

# ## loading videos and visualization

# In[5]:


get_ipython().run_cell_magic('time', '', "varr = load_videos(dpath, **param_load_videos)\nchk = get_optimal_chk(varr.astype(float), dim_grp=[('frame',), ('height', 'width')])")


# In[6]:


hv.output(size=output_size)
if interactive:
    vaviewer = VArrayViewer(varr, framerate=5, summary=None)
    display(vaviewer.show())


# ## set roi for motion correction

# In[7]:


if interactive:
    try:
        subset_mc = list(vaviewer.mask.values())[0]
    except IndexError:
        pass


# ## subset part of video

# In[8]:


varr_ref = varr.sel(subset)


# ## glow removal and visualization

# In[9]:


get_ipython().run_cell_magic('time', '', "varr_min = varr_ref.min('frame').compute()\nvarr_ref = varr_ref - varr_min")


# In[10]:


hv.output(size=output_size)
if interactive:
    vaviewer = VArrayViewer(
        [varr.rename('original'), varr_ref.rename('glow_removed')],
        framerate=5,
        summary=None,
        layout=True)
    display(vaviewer.show())


# ## denoise

# In[11]:


hv.output(size=output_size)
if interactive:
    display(visualize_preprocess(varr_ref.isel(frame=0), denoise, method=['median'], ksize=[5, 7, 9]))


# In[12]:


varr_ref = denoise(varr_ref, **param_denoise)


# ## backgroun removal

# In[13]:


hv.output(size=output_size)
if interactive:
    display(visualize_preprocess(varr_ref.isel(frame=0), remove_background, method=['tophat'], wnd=[10, 15, 20]))


# In[14]:


varr_ref = remove_background(varr_ref, **param_background_removal)


# ## save result

# In[15]:


get_ipython().run_cell_magic('time', '', "varr_ref = varr_ref.chunk(chk)\nvarr_ref = save_minian(varr_ref.rename('org'), **param_save_minian)")


# # motion correction

# ## load in from disk

# In[16]:


varr_ref = open_minian(dpath,
                      fname=param_save_minian['fname'],
                      backend=param_save_minian['backend'])['org']


# ## estimate shifts

# In[17]:


get_ipython().run_cell_magic('time', '', 'shifts = estimate_shifts(varr_ref.sel(subset_mc), **param_estimate_shift)')


# ## save shifts

# In[18]:


get_ipython().run_cell_magic('time', '', "shifts = shifts.chunk(dict(frame=chk['frame'])).rename('shifts')\nshifts = save_minian(shifts, **param_save_minian)")


# ## visualization of shifts

# In[19]:


get_ipython().run_cell_magic('opts', "Curve [frame_width=500, tools=['hover'], aspect=2]", "hv.output(size=output_size)\nif interactive:\n    display(hv.NdOverlay(dict(width=hv.Curve(shifts.sel(variable='width')),\n                              height=hv.Curve(shifts.sel(variable='height')))))")


# ## apply shifts

# In[20]:


Y = apply_shifts(varr_ref, shifts)
Y = Y.fillna(0).astype(varr_ref.dtype)


# ## visualization of motion-correction

# In[21]:


hv.output(size=output_size)
if interactive:
    vaviewer = VArrayViewer(
        [varr_ref.rename('before_mc'), Y.rename('after_mc')],
        framerate=5,
        summary=None,
        layout=True)
    display(vaviewer.show())


# ## save result

# In[22]:


get_ipython().run_cell_magic('time', '', "Y = Y.chunk(chk)\nY = save_minian(Y.rename('Y'), **param_save_minian)")


# # initialization

# ## load in from disk

# In[23]:


get_ipython().run_cell_magic('time', '', "minian = open_minian(dpath,\n                     fname=param_save_minian['fname'],\n                     backend=param_save_minian['backend'])")


# In[24]:


Y = minian['Y'].astype(np.float)
max_proj = Y.max('frame').compute()
Y_flt = Y.stack(spatial=['height', 'width'])


# ## generating over-complete set of seeds

# In[25]:


get_ipython().run_cell_magic('time', '', 'seeds = seeds_init(Y, **param_seeds_init)')


# In[26]:


hv.output(size=output_size)
visualize_seeds(max_proj, seeds)


# ## peak-noise-ratio refine

# In[27]:


get_ipython().run_cell_magic('time', '', "if interactive:\n    noise_freq_list = [0.005, 0.01, 0.02, 0.06, 0.1, 0.2, 0.3, 0.45]\n    example_seeds = seeds.sample(6, axis='rows')\n    example_trace = (Y_flt\n                     .sel(spatial=[tuple(hw) for hw in example_seeds[['height', 'width']].values])\n                     .assign_coords(spatial=np.arange(6))\n                     .rename(dict(spatial='seed')))\n    smooth_dict = dict()\n    for freq in noise_freq_list:\n        trace_smth_low = smooth_sig(example_trace, freq)\n        trace_smth_high = smooth_sig(example_trace, freq, btype='high')\n        trace_smth_low = trace_smth_low.compute()\n        trace_smth_high = trace_smth_high.compute()\n        hv_trace = hv.HoloMap({\n            'signal': (hv.Dataset(trace_smth_low)\n                       .to(hv.Curve, kdims=['frame'])\n                       .opts(frame_width=300, aspect=2, ylabel='Signal (A.U.)')),\n            'noise': (hv.Dataset(trace_smth_high)\n                      .to(hv.Curve, kdims=['frame'])\n                      .opts(frame_width=300, aspect=2, ylabel='Signal (A.U.)'))\n        }, kdims='trace').collate()\n        smooth_dict[freq] = hv_trace")


# In[28]:


hv.output(size=output_size)
if interactive:
    hv_res = (hv.HoloMap(smooth_dict, kdims=['noise_freq']).collate().opts(aspect=2)
              .overlay('trace').layout('seed').cols(3))
    display(hv_res)


# In[29]:


seeds, pnr, gmm = pnr_refine(Y_flt, seeds.copy(), **param_pnr_refine)


# In[30]:


if gmm:
    display(visualize_gmm_fit(pnr, gmm, 100))


# In[31]:


hv.output(size=output_size)
visualize_seeds(max_proj, seeds, 'mask_pnr')


# ## ks refine

# In[32]:


get_ipython().run_cell_magic('time', '', "seeds = ks_refine(Y_flt, seeds[seeds['mask_pnr']], **param_ks_refine)")


# In[33]:


hv.output(size=output_size)
visualize_seeds(max_proj, seeds, 'mask_ks')


# ## merge seeds

# In[34]:


get_ipython().run_cell_magic('time', '', "seeds_final = seeds[seeds['mask_ks']].reset_index(drop=True)\nseeds_mrg = seeds_merge(Y_flt, seeds_final, **param_seeds_merge)")


# In[35]:


hv.output(size=output_size)
visualize_seeds(max_proj, seeds_mrg, 'mask_mrg')


# ## initialize spatial and temporal matrices from seeds

# In[36]:


get_ipython().run_cell_magic('time', '', "A, C, b, f = initialize(Y, seeds_mrg[seeds_mrg['mask_mrg']], **param_initialize)")


# In[37]:


im_opts = dict(frame_width=500, aspect=A.sizes['width']/A.sizes['height'], cmap='Viridis', colorbar=True)
cr_opts = dict(frame_width=750, aspect=1.5*A.sizes['width']/A.sizes['height'])
(regrid(hv.Image(A.sum('unit_id').rename('A').compute(), kdims=['width', 'height'])).opts(**im_opts)
 + regrid(hv.Image(C.rename('C').compute(), kdims=['frame', 'unit_id'])).opts(cmap='viridis', colorbar=True, **cr_opts)
  + regrid(hv.Image(b.rename('b').compute(), kdims=['width', 'height'])).opts(**im_opts)
 + datashade(hv.Curve(f.rename('f').compute(), kdims=['frame']), min_alpha=200).opts(**cr_opts)
).cols(2)


# ## save results

# In[38]:


get_ipython().run_cell_magic('time', '', "A = save_minian(A.rename('A_init').rename(unit_id='unit_id_init'), **param_save_minian)\nC = save_minian(C.rename('C_init').rename(unit_id='unit_id_init'), **param_save_minian)\nb = save_minian(b.rename('b_init'), **param_save_minian)\nf = save_minian(f.rename('f_init'), **param_save_minian)")


# # CNMF

# ## loading data

# In[39]:


get_ipython().run_cell_magic('time', '', "minian = open_minian(dpath,\n                     fname=param_save_minian['fname'],\n                     backend=param_save_minian['backend'])\nY = minian['Y'].astype(np.float)\nA_init = minian['A_init'].rename(unit_id_init='unit_id')\nC_init = minian['C_init'].rename(unit_id_init='unit_id')\nb_init = minian['b_init']\nf_init = minian['f_init']")


# ## estimate spatial noise

# In[40]:


get_ipython().run_cell_magic('time', '', 'sn_spatial = get_noise_fft(Y, **param_get_noise).persist()')


# ## test parameters for spatial update

# In[41]:


if interactive:
    units = np.random.choice(A_init.coords['unit_id'], 10, replace=False)
    units.sort()
    A_sub = A_init.sel(unit_id=units).persist()
    C_sub = C_init.sel(unit_id=units).persist()


# In[42]:


get_ipython().run_cell_magic('time', '', "if interactive:\n    sprs_ls = [0.05, 0.1, 0.5]\n    A_dict = dict()\n    C_dict = dict()\n    for cur_sprs in sprs_ls:\n        cur_A, cur_b, cur_C, cur_f = update_spatial(\n            Y, A_sub, b_init, C_sub, f_init,\n            sn_spatial, dl_wnd=param_first_spatial['dl_wnd'], sparse_penal=cur_sprs)\n        if cur_A.sizes['unit_id']:\n            A_dict[cur_sprs] = cur_A.compute()\n            C_dict[cur_sprs] = cur_C.compute()\n    hv_res = visualize_spatial_update(A_dict, C_dict, kdims=['sparse penalty'])")


# In[43]:


hv.output(size=output_size)
if interactive:
    display(hv_res)


# ## first spatial update

# In[44]:


get_ipython().run_cell_magic('time', '', 'A_spatial, b_spatial, C_spatial, f_spatial = update_spatial(\n    Y, A_init, b_init, C_init, f_init, sn_spatial, **param_first_spatial)')


# In[45]:


hv.output(size=output_size)
opts = dict(plot=dict(height=A_init.sizes['height'], width=A_init.sizes['width'], colorbar=True), style=dict(cmap='Viridis'))
(regrid(hv.Image(A_init.sum('unit_id').compute().rename('A'), kdims=['width', 'height'])).opts(**opts).relabel("Spatial Footprints Initial")
+ regrid(hv.Image((A_init.fillna(0) > 0).sum('unit_id').compute().rename('A'), kdims=['width', 'height']), aggregator='max').opts(**opts).relabel("Binary Spatial Footprints Initial")
+ regrid(hv.Image(A_spatial.sum('unit_id').compute().rename('A'), kdims=['width', 'height'])).opts(**opts).relabel("Spatial Footprints First Update")
+ regrid(hv.Image((A_spatial > 0).sum('unit_id').compute().rename('A'), kdims=['width', 'height']), aggregator='max').opts(**opts).relabel("Binary Spatial Footprints First Update")).cols(2)


# In[46]:


hv.output(size=output_size)
opts_im = dict(plot=dict(height=b_init.sizes['height'], width=b_init.sizes['width'], colorbar=True), style=dict(cmap='Viridis'))
opts_cr = dict(plot=dict(height=b_init.sizes['height'], width=b_init.sizes['height'] * 2))
(regrid(hv.Image(b_init.compute(), kdims=['width', 'height'])).opts(**opts_im).relabel('Background Spatial Initial')
 + datashade(hv.Curve(f_init.compute(), kdims=['frame'])).opts(**opts_cr).relabel('Background Temporal Initial')
 + regrid(hv.Image(b_spatial.compute(), kdims=['width', 'height'])).opts(**opts_im).relabel('Background Spatial First Update')
 + datashade(hv.Curve(f_spatial.compute(), kdims=['frame'])).opts(**opts_cr).relabel('Background Temporal First Update')
).cols(2)


# ## test parameters for temporal update

# In[47]:


if interactive:
    units = np.random.choice(A_spatial.coords['unit_id'], 10, replace=False)
    units.sort()
    A_sub = A_spatial.sel(unit_id=units).persist()
    C_sub = C_spatial.sel(unit_id=units).persist()


# In[48]:


get_ipython().run_cell_magic('time', '', 'if interactive:\n    p_ls = [1]\n    sprs_ls = [0.01, 0.05, 0.1, 2]\n    add_ls = [20]\n    noise_ls = [0.06]\n    YA_dict, C_dict, S_dict, g_dict, sig_dict, A_dict = [dict() for _ in range(6)]\n    YrA = compute_trace(Y, A_sub, b_spatial, C_sub, f_spatial).persist()\n    for cur_p, cur_sprs, cur_add, cur_noise in itt.product(p_ls, sprs_ls, add_ls, noise_ls):\n        ks = (cur_p, cur_sprs, cur_add, cur_noise)\n        print("p:{}, sparse penalty:{}, additional lag:{}, noise frequency:{}"\n            .format(cur_p, cur_sprs, cur_add, cur_noise))\n        YrA, cur_C, cur_S, cur_B, cur_C0, cur_sig, cur_g, cur_scal = update_temporal(\n            Y, A_sub, b_spatial, C_sub, f_spatial, sn_spatial, YrA=YrA,\n            sparse_penal=cur_sprs, p=cur_p, use_spatial=False, use_smooth=True,\n            add_lag = cur_add, noise_freq=cur_noise)\n        YA_dict[ks], C_dict[ks], S_dict[ks], g_dict[ks], sig_dict[ks], A_dict[ks] = (\n            YrA.compute(), cur_C.compute(), cur_S.compute(), cur_g.compute(), cur_sig.compute(), A_sub.compute())\n    hv_res = visualize_temporal_update(\n        YA_dict, C_dict, S_dict, g_dict, sig_dict, A_dict,\n        kdims=[\'p\', \'sparse penalty\', \'additional lag\', \'noise frequency\'])')


# In[49]:


hv.output(size=output_size)
if interactive:
    display(hv_res)


# ## first temporal update

# In[50]:


get_ipython().run_cell_magic('time', '', "YrA, C_temporal, S_temporal, B_temporal, C0_temporal, sig_temporal, g_temporal, scale = update_temporal(\n    Y, A_spatial, b_spatial, C_spatial, f_spatial, sn_spatial, **param_first_temporal)\nA_temporal = A_spatial.sel(unit_id = C_temporal.coords['unit_id'])")


# In[51]:


hv.output(size=output_size)
opts_im = dict(frame_width=500, aspect=2, colorbar=True, cmap='Viridis', logz=True)
(regrid(hv.Image(C_init.rename('ci').compute(), kdims=['frame', 'unit_id'])).opts(**opts_im).relabel("Temporal Trace Initial")
 + hv.Div('')
 + regrid(hv.Image(C_temporal.rename('c1').compute(), kdims=['frame', 'unit_id'])).opts(**opts_im).relabel("Temporal Trace First Update")
 + regrid(hv.Image(S_temporal.rename('s1').compute(), kdims=['frame', 'unit_id'])).opts(**opts_im).relabel("Spikes First Update")
).cols(2)


# In[52]:


hv.output(size=output_size)
if interactive:
    h, w = A_spatial.sizes['height'], A_spatial.sizes['width']
    im_opts = dict(aspect=w/h, frame_width=500, cmap='Viridis')
    cr_opts = dict(aspect=3, frame_width=1000)
    bad_units = list(set(A_spatial.coords['unit_id'].values) - set(A_temporal.coords['unit_id'].values))
    bad_units.sort()
    if len(bad_units)>0:
        hv_res = (hv.NdLayout({
            "Spatial Footprint": regrid(hv.Dataset(A_spatial.sel(unit_id=bad_units).compute().rename('A'))
                                       .to(hv.Image, kdims=['width', 'height'])).opts(**im_opts),
            "Spatial Footprints of Accepted Units": regrid(hv.Image(A_temporal.sum('unit_id').compute().rename('A'), kdims=['width', 'height'])).opts(**im_opts)
        })
                  + datashade(hv.Dataset(YrA.sel(unit_id=bad_units).compute().rename('raw'))
                              .to(hv.Curve, kdims=['frame'])).opts(**cr_opts).relabel("Temporal Trace")).cols(1)
        display(hv_res)
    else:
        print("No rejected units to display")


# In[53]:


hv.output(size=output_size)
if interactive:
    display(visualize_temporal_update(YrA.compute(), C_temporal.compute(), S_temporal.compute(), g_temporal.compute(), sig_temporal.compute(), A_temporal.compute()))


# ## merge units

# In[54]:


get_ipython().run_cell_magic('time', '', 'A_mrg, sig_mrg, add_list = unit_merge(A_temporal, sig_temporal, [S_temporal, C_temporal], **param_first_merge)\nS_mrg, C_mrg = add_list[:]')


# In[55]:


hv.output(size=output_size)
opts_im = dict(frame_width=500, aspect=2, colorbar=True, cmap='Viridis', logz=True)
(regrid(hv.Image(sig_temporal.compute().rename('c1'), kdims=['frame', 'unit_id'])).relabel("Temporal Signals Before Merge").opts(**opts_im) +
regrid(hv.Image(sig_mrg.compute().rename('c2'), kdims=['frame', 'unit_id'])).relabel("Temporal Signals After Merge").opts(**opts_im))


# ## test parameters for spatial update

# In[56]:


if interactive:
    units = np.random.choice(A_mrg.coords['unit_id'], 10, replace=False)
    units.sort()
    A_sub = A_mrg.sel(unit_id=units).persist()
    sig_sub = sig_mrg.sel(unit_id=units).persist()


# In[57]:


get_ipython().run_cell_magic('time', '', "if interactive:\n    sprs_ls = [0.001, 0.005, 0.01]\n    A_dict = dict()\n    C_dict = dict()\n    for cur_sprs in sprs_ls:\n        cur_A, cur_b, cur_C, cur_f = update_spatial(\n            Y, A_sub, b_init, sig_sub, f_init,\n            sn_spatial, dl_wnd=param_second_spatial['dl_wnd'], sparse_penal=cur_sprs)\n        if cur_A.sizes['unit_id']:\n            A_dict[cur_sprs] = cur_A.compute()\n            C_dict[cur_sprs] = cur_C.compute()\n    hv_res = visualize_spatial_update(A_dict, C_dict, kdims=['sparse penalty'])")


# In[58]:


hv.output(size=output_size)
if interactive:
    display(hv_res)


# ## second spatial update

# In[59]:


get_ipython().run_cell_magic('time', '', 'A_spatial_it2, b_spatial_it2, C_spatial_it2, f_spatial_it2 = update_spatial(\n    Y, A_mrg, b_spatial, sig_mrg, f_spatial, sn_spatial, **param_second_spatial)')


# In[60]:


hv.output(size=output_size)
opts = dict(aspect=A_spatial_it2.sizes['width']/A_spatial_it2.sizes['height'], frame_width=500, colorbar=True, cmap='Viridis')
(regrid(hv.Image(A_mrg.sum('unit_id').compute().rename('A'), kdims=['width', 'height'])).opts(**opts).relabel("Spatial Footprints First Update")
+ regrid(hv.Image((A_mrg.fillna(0) > 0).sum('unit_id').compute().rename('A'), kdims=['width', 'height']), aggregator='max').opts(**opts).relabel("Binary Spatial Footprints First Update")
+ regrid(hv.Image(A_spatial_it2.sum('unit_id').compute().rename('A'), kdims=['width', 'height'])).opts(**opts).relabel("Spatial Footprints Second Update")
+ regrid(hv.Image((A_spatial_it2 > 0).sum('unit_id').compute().rename('A'), kdims=['width', 'height']), aggregator='max').opts(**opts).relabel("Binary Spatial Footprints Second Update")).cols(2)


# In[61]:


hv.output(size=output_size)
opts_im = dict(aspect=b_spatial_it2.sizes['width'] / b_spatial_it2.sizes['height'], frame_width=500, colorbar=True, cmap='Viridis')
opts_cr = dict(aspect=2, frame_height=int(500 * b_spatial_it2.sizes['height'] / b_spatial_it2.sizes['width']))
(regrid(hv.Image(b_spatial.compute(), kdims=['width', 'height'])).opts(**opts_im).relabel('Background Spatial First Update')
 + datashade(hv.Curve(f_spatial.compute(), kdims=['frame'])).opts(**opts_cr).relabel('Background Temporal First Update')
 + regrid(hv.Image(b_spatial_it2.compute(), kdims=['width', 'height'])).opts(**opts_im).relabel('Background Spatial Second Update')
 + datashade(hv.Curve(f_spatial_it2.compute(), kdims=['frame'])).opts(**opts_cr).relabel('Background Temporal Second Update')
).cols(2)


# ## test parameters for temporal update

# In[62]:


if interactive:
    units = np.random.choice(A_spatial_it2.coords['unit_id'], 10, replace=False)
    units.sort()
    A_sub = A_spatial_it2.sel(unit_id=units).persist()
    C_sub = C_spatial_it2.sel(unit_id=units).persist()


# In[63]:


get_ipython().run_cell_magic('time', '', 'if interactive:\n    p_ls = [1]\n    sprs_ls = [0.01, 0.05, 0.1]\n    add_ls = [20]\n    noise_ls = [0.06,0.1]\n    YA_dict, C_dict, S_dict, g_dict, sig_dict, A_dict = [dict() for _ in range(6)]\n    YrA = compute_trace(Y, A_sub, b_spatial, C_sub, f_spatial).persist()\n    for cur_p, cur_sprs, cur_add, cur_noise in itt.product(p_ls, sprs_ls, add_ls, noise_ls):\n        ks = (cur_p, cur_sprs, cur_add, cur_noise)\n        print("p:{}, sparse penalty:{}, additional lag:{}, noise frequency:{}"\n              .format(cur_p, cur_sprs, cur_add, cur_noise))\n        YrA, cur_C, cur_S, cur_B, cur_C0, cur_sig, cur_g, cur_scal = update_temporal(\n            Y, A_sub, b_spatial, C_sub, f_spatial, sn_spatial, YrA=YrA,\n            sparse_penal=cur_sprs, p=cur_p, use_spatial=False, use_smooth=True,\n            add_lag = cur_add, noise_freq=cur_noise)\n        YA_dict[ks], C_dict[ks], S_dict[ks], g_dict[ks], sig_dict[ks], A_dict[ks] = (\n            YrA.compute(), cur_C.compute(), cur_S.compute(), cur_g.compute(), cur_sig.compute(), A_sub.compute())\n    hv_res = visualize_temporal_update(\n        YA_dict, C_dict, S_dict, g_dict, sig_dict, A_dict,\n        kdims=[\'p\', \'sparse penalty\', \'additional lag\', \'noise frequency\'])')


# In[64]:


hv.output(size=output_size)
if interactive:
    display(hv_res)


# ## second temporal update

# In[65]:


get_ipython().run_cell_magic('time', '', "YrA, C_temporal_it2, S_temporal_it2, B_temporal_it2, C0_temporal_it2, sig_temporal_it2, g_temporal_it2, scale_temporal_it2 = update_temporal(\n    Y, A_spatial_it2, b_spatial_it2, C_spatial_it2, f_spatial_it2, sn_spatial, **param_second_temporal)\nA_temporal_it2 = A_spatial_it2.sel(unit_id=C_temporal_it2.coords['unit_id'])\ng_temporal_it2 = g_temporal_it2.sel(unit_id=C_temporal_it2.coords['unit_id'])\nA_temporal_it2 = rechunk_like(A_temporal_it2, A_spatial_it2)\ng_temporal_it2 = rechunk_like(g_temporal_it2, C_temporal_it2)")


# In[66]:


hv.output(size=output_size)
opts_im = dict(frame_width=500, aspect=2, colorbar=True, cmap='Viridis', logz=True)
(regrid(hv.Image(C_mrg.rename('c1').compute(), kdims=['frame', 'unit_id'])).opts(**opts_im).relabel("Temporal Trace First Update")
 + regrid(hv.Image(S_mrg.rename('s1').compute(), kdims=['frame', 'unit_id'])).opts(**opts_im).relabel("Spikes First Update")
 + regrid(hv.Image(C_temporal_it2.rename('c2').rename(unit_id='unit_id_it2').compute(), kdims=['frame', 'unit_id_it2'])).opts(**opts_im).relabel("Temporal Trace Second Update")
 + regrid(hv.Image(S_temporal_it2.rename('s2').rename(unit_id='unit_id_it2').compute(), kdims=['frame', 'unit_id_it2'])).opts(**opts_im).relabel("Spikes Second Update")).cols(2)


# In[67]:


hv.output(size=output_size)
if interactive:
    h, w = A_spatial_it2.sizes['height'], A_spatial_it2.sizes['width']
    im_opts = dict(aspect=w/h, frame_width=500, cmap='Viridis')
    cr_opts = dict(aspect=3, frame_width=1000)
    bad_units = list(set(A_spatial_it2.coords['unit_id'].values) - set(A_temporal_it2.coords['unit_id'].values))
    bad_units.sort()
    if len(bad_units)>0:
        hv_res = (hv.NdLayout({
            "Spatial Footprin": regrid(hv.Dataset(A_spatial_it2.sel(unit_id=bad_units).compute().rename('A'))
                                       .to(hv.Image, kdims=['width', 'height'])).opts(**im_opts),
            "Spatial Footprints of Accepted Units": regrid(hv.Image(A_temporal_it2.sum('unit_id').compute().rename('A'), kdims=['width', 'height'])).opts(**im_opts)
        })
                  + datashade(hv.Dataset(YrA.sel(unit_id=bad_units).compute().rename('raw'))
                              .to(hv.Curve, kdims=['frame'])).opts(**cr_opts).relabel("Temporal Trace")).cols(1)
        display(hv_res)
    else:
        print("No rejected units to display")


# In[68]:


hv.output(size=output_size)
if interactive:
    display(visualize_temporal_update(YrA.compute(), C_temporal_it2.compute(), S_temporal_it2.compute(), g_temporal_it2.compute(), sig_temporal_it2.compute(), A_temporal_it2.compute()))


# ## save results

# In[69]:


get_ipython().run_cell_magic('time', '', "A_temporal_it2 = save_minian(A_temporal_it2.rename('A'), **param_save_minian)\nC_temporal_it2 = save_minian(C_temporal_it2.rename('C'), **param_save_minian)\nS_temporal_it2 = save_minian(S_temporal_it2.rename('S'), **param_save_minian)\ng_temporal_it2 = save_minian(g_temporal_it2.rename('g'), **param_save_minian)\nC0_temporal_it2 = save_minian(C0_temporal_it2.rename('C0'), **param_save_minian)\nB_temporal_it2 = save_minian(B_temporal_it2.rename('bl'), **param_save_minian)\nb_spatial_it2 = save_minian(b_spatial_it2.rename('b'), **param_save_minian)\nf_spatial_it2 = save_minian(f_spatial_it2.rename('f'), **param_save_minian)")


# ## visualization

# In[70]:


minian = open_minian(dpath,
                     fname=param_save_minian['fname'],
                     backend=param_save_minian['backend'])
varr = load_videos(dpath, **param_load_videos)
chk = get_optimal_chk(varr.astype(float), dim_grp=[('frame',), ('height', 'width')])
varr = varr.chunk(dict(frame=chk['frame']))


# In[ ]:


get_ipython().run_cell_magic('time', '', 'generate_videos(\n    minian, varr, dpath, param_save_minian[\'fname\'] + ".mp4", scale=\'auto\')')


# In[ ]:


get_ipython().run_cell_magic('time', '', 'if interactive:\n    cnmfviewer = CNMFViewer(minian)')


# In[ ]:


hv.output(size=output_size)
if interactive:
    display(cnmfviewer.show())


# In[ ]:


if interactive:
    save_minian(cnmfviewer.unit_labels, **param_save_minian)


# In[ ]:
