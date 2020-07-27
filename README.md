# miniursi

Miniscope and behavioral data analysis pipeline from Vassar College based upon MiniAn, CaImAn, and DeepLabCut.

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
