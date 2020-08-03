# DLC Instructions

This file works through the necessary steps of running DLC GUI on personal computer before the project is ready to be uploaded and trained on Hopper. For a more comprehensive view of all the steps and their corresponding command line scripts, please reference the *dlc_functions.md* file borrowed from AlexEMG.
You might encounter some errors when following through these steps, please check https://github.com/DeepLabCut/DeepLabCut/wiki/Troubleshooting-Tips for some easy fixes.

## Open DLC GUI
1) Activate the DLC environment:  
<code> conda activate dlc </code>
2) Open an iPython session: 
<code> ipython </code> or
<code> pythonw </code> if you are using MacOS
3) Import deeplabcut within the session:  
<code> import deeplabcut </code>
4) Launch the GUI:  
<code> deeplabcut.launch_dlc() </code>

## Create a new project
1) Go to the Manage Project tab on the GUI, and fill in name of the project and name of the experimenter.
2) Click on the Choose Videos button to select the videos you want to train the network on.
3) Check off the two optional attributes. Click the Browse button to select the specific directory you want to put this project in.
4) Click the OK button on the bottom right corner to create the project.

## Load an existing project
1) Select the load existing project option on the top of the Manage Project tab.
2) Click on the Browse button to select the *config.yaml* file of the project you want to open.
3) Click the OK button to load the project.

## Edit configuration
1) Click the Edit config file button to open the *config.yaml* file in a text editor (Atom is recommended but any text editor would work).
2) Under bodyparts, name the body parts you want to extract. You can add body parts by simply adding a new line and write:
<code> - bodypart4 </code>
3) Under skeleton, connect the body parts listed above to form a skeleton. This connects skeleton by drawing lines between pairs of points. Make sure that the pairs are all written in this format:  
<code> - - bodypart1 </code>  
<code>   - bodypart2 </code>  
4) (Optional) The default value for dotsize (12) is usually too big for visualization and would sometimes cover up the image in the resulting videos. You can change the size in the labelling frames step, but only changing the dotsize parameter in the *config.yaml* file will affect what you see in the generated videos.

## Extract and label frames
1) Go to the Extract frames tab and click the OK button on the bottom right.
2) Go to the Label frames tab and click on the Label Frames button. This will open a separate window.
3) Click the Load frames button on the bottom right to select the folder you want to label (frames for each video will be in a separate folder)
4) Right click on the image will add the label to the image (showing up as a dot). Left click to move the label position. You can change the body parts you are labeling on the Select a bodypart to label panel on the right. Click on the Zoom button to select an area of the image to zoom in.
5) Click the Next button when you are ready to label the next frame.
6) When you are done with all the frames in the folder, click on the Save button to save the labels and click on Quit to quit this window or start another folder.
7) When you are done with all the frames, click on the Check Labeled Frames button the verify that all frames are labeled.

## Create training dataset
1) Go to the Create training dataset tab and click on the OK button.

**Once finished, upload the entire folder to Hopper and do the rest on Hopper.**
