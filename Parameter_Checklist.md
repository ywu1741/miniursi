# MINISCOPE PARAMETER CHECKLIST (unfinished)

Note that this series of steps is based on the config template. Variables that are not mentioned in the checklist for the most part *SHOULD NOT BE CHANGED*. There are descriptions of those variables within the config file and they can be altered if necessary, however they should not need to be for most datasets. Most parameters required looking at interactive plots using the provided jupyter notebook. For more details, see the pipeline_noted jupyter notebook provided in the minian package.

## Basic Parameters
1. Specify the dpath variable to the directory containing the videos to be analyzed.
2. If you need to crop the videos, edit the subset variable to describe the frame boundaries you wish to work within. For example, to only use frames 100-500, set subset = dict(frame=slice(100,500))
3. Specify the meta_dict and fname variables in param_save_minian. fname should be set to the name you want for the output folder and the meta_dict should define the preferred way to construct meta data for the final data structure and most importantly should be CONSISTENT WITH THE HOPPER FOLDER STRUCTURE. So, it should not be changed unless the folder structure is changed.

## Pre-Processing Parameters
1. Specify the regex pattern variable in the param_load_videos section to call videos within the directory you previously specified. This may be important if you have behavior and neural videos in the same folder for one session. Most neural video data is saved as .avi files with the title ‘msCam’, hence the default value.
2. If needed, specify the subset before running the subset part of video step to include only the needed portion of the videos. For example, if only the first 800 frames, and the height and width from 100 to 200 are relevant, the subset dictionary should be defined as follows before running the varr_ref line.
  subset = {
    'frame': slice(0, 800),
    'height': slice(100, 200),
    'width': slice(100, 200)
  }
If kept in default setting, there will be no selection, and the whole video will be processed.
3. Specify the ksize variable in param_first_denoise. This should be set to roughly half the diameter of the largest cell in the video and has to be odd number. For the better results, a good image after should clarify the cells/bright spots without blurring the image too much. The contours after should be clear of excessive lines and adhere close to the image after.
4. Specify the wnd variable within param_background_removal. It should be set to the expected size of the largest cell diameter. The background removal step only counts elements larger than a disk with radius wnd as background elements. Thus, if wnd is set too low, some cells will be counted as background and get removed; if wnd is set too high, some background will be counted as cells. For better results, compare the graphical outputs for different wnd. A good image after should keep the visible bright features while removing the large-size background elements. A good contours after graph should outline the bright features closely without introducing many excessive lines.

## Initialization Parameters
1. Set the max_wnd variable in param_sees_init to be the same as the ksize variable in param_first_denoise.
2. Determine the noise_freq variable in param_pnr_refine from the interative plots. This value is the ratio between the peak-to-valley values of the real signal and the noise signal given the assumption that real cell activity is of lower frequency while noise if of higher frequency. The best noise_freq would be one that separates the signal from the noise pretty well (i.e. the noise should be clustering around y=0 without outstanding peaks or valleys while the signal should include most of the peaks) without the signal bands being too thick.
3. Set the noise_freq variable in param_seeds_merge to be the same as the noise_freq variable in param_refine_pnr.
4. Set the wnd variable in param_initialize to be the same as the wnd variable in param_background_removal.
5. Set the noise_freq varialbe in param_initialize to be the same as the noise_freq variable in param_pnr_refine.

## CNMF PARAMETERS
1. Set the dl_wnd variable in param_first_spatial to be the same as the ksize variable in param_first_denoise.
2. Determine the sparse_penal variable in param_first_spatial from the interactive plots in the test parameters for spatial update section. For better results, the binary matrix graph should mimic the spatial matrix graph. Increasing sparse_penal will generally decrease the size of the binary footprints but may remove some parts of the real spatial footprints. Decreasing sparse_penal will do the reverse.
3. Set the p variable in param_first_temporal to 2 if the calcium traces have a visible rise time; set it to 1 if the rise time is faster than the sampling rate (i.e. not visible).
4. Determine the sparse_penal variable in param_first_temporal from the interactive plots in the test parameters for temporal update section. For better results, the tempoeral traces should have one fitted spike (the green line) for each spike in the raw signal (the red line). Setting it too low will result in many small fitted spikes at the bottom where there aren't spikes in the raw signal; setting it too high will result in the absence of fitted spikes where there are spikes in the raw signal.
5. Set the dl_wnd variable in param_second_spatial to be the same as the ksize variable in param_first_denoise.
6. Determine the sparse_penal variable in param_second_spatial in the same way as in step 2 above.
7. Set the p variable in param_second_temporal to 2 if the calcium traces have a visible rise time; set it to 1 if the rise time is faster than the sampling rate (i.e. not visible).
8. Determine the sparse_penal variable in param_second_temporal in the same way as in step 4 above.
