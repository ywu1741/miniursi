# miniursi

A Miniscope and behavioral data analysis pipeline from Vassar College based upon MiniAn and DeepLabCut.

## Getting Started  
Welcome to the Vassar Miniscope Project! If you are new to the project please read through this section as it will direct you through this Github repository and also direct you to some other important resources for familiarizing yourself with the miniscope as well as the programs we are using here to process its data.  
  
Generally, all the files you need to understand our pipeline can be found in the instruct folder. This includes various markdown and jupyter files describing how to tune the pipeline and DeepLabCut to the data as well as how to run everything on the Hopper computer cluster. The minian folder holds all the specific groups of functions necessary to run the miniscope pipeline while the drive folder holds the functions necessary to upload your video data from Google Drive onto Hopper. Lastly, the Rfiles folder holds R scripts for post-processing analysis.   

To familiarize yourself with the pipeline part of the process, the following sources are recommended:  
1) Check out the Resendez et al. (2016) paper to get to know the miniscope itself including the procedure for using it in a laboratory setting as well as the data that it produces.  
2) Read through the *pipeline_noted.ipynb* jupyter notebook. It is very dense but contains the exact step-by-step reasoning that went into the original pipeline from the DeniseCaiLab including all of the math and an explanation of the transition from video data to the array that the pipeline uses to manipulate that video.  
  
To familiarize yourself with the DeepLabCut part of the process, the following sources are recommended:  
1) Read the DeepLabCut_User_Guide.pdf file. This contains an entry-level explanation of how DeepLabCut works and what you can accomplish with it.  
2) Look at the dlc_functions.md file to get a closer look at the actual code behind DeepLabCut. This list should contain everything you need as specified in the dlc_instructions.md file to successfully process behavioral data.  

## Run Instructions
### MINISCOPE
1) Run the install.sh bash file in the cloned environment once you have cloned this repository (if you have any trouble with this, follow the install instructions at https://github.com/DeniseCaiLab/minian. Make sure to install the dev branch rather than the master.)
2) Examine your data using the *pipeline_configuration.ipynb* jupyter notebook. This will be critical for setting up you parameters in your config file. For futher information on the variables within the pipeline than that supplied in the *pipeline_configuration.ipynb* notebook, please reference the *pipeline_noted.ipynb* notebook borrowed from DeniseCaiLab.
3) Once you have those variables, see the *Hopper_Instructions.md* file for how to implement them into the file structure as well as how to execute the Miniscope pipeline on the Hopper computer cluster.

### DLC
1) Open Anaconda Prompt and clone the DLC repository
<code>git clone https://github.com/AlexEMG/DeepLabCut.git </code>
2) cd to the folder named conda-environments and type:
<code>conda env create -n dlc -f DLC-CPU.yaml </code>
3) Follow the steps in the *dlc_instructions.md* file for how to use DeepLabCut GUI on computer to create a project and label the frames and variables to change for each step. For further information on each function and all the parameters used, please reference the *dlc_functions.md* file borrowed from AlexEMG.
4) Once the frames are labeled, and the training dataset is created, see the *Hopper_Instructions.md* file for how to complete the steps and extract body part positions on the Hopper computer cluster.
