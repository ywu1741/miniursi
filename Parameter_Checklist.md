# MINISCOPE PARAMETER CHECKLIST (unfinished)

Note that this series of steps is based on the config template. Variables that are not mentioned in the checklist for the most part *SHOULD NOT BE CHANGED*. There are descriptions of those variables within the config file and they can be altered if necessary, however they should not need to be for most datasets. 

1. Specify the dpath variable to the directory containing the videos to be analyzed. 
2. If you need to crop the videos, edit the subset variable to describe the frame boundaries you wish to work within. For example, to only use frames 100-500, set subset = dict(frame=slice(100,500))
3. Specify the meta_dict and fname variables in param_save_minian. fname should be set to the name you want for the output folder and the meta_dict should define the preferred way to construct meta data for the final data structure and most importantly should be CONSISTENT WITH THE HOPPER FOLDER STRUCTURE. So, it should not be changed unless the folder structure is changed. 
4. Specify the regex pattern variable in the param_load_videos section to call videos within the directory you previously specified. This may be important if you have behavior and neural videos in the same folder for one session. Most neural video data is saved as .avi files with the title ‘msCam’, hence the default value. 
5. 
