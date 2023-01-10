# qcdc
"Quantum Chemical Data Collection" is a python3 program 
which walks through the directory tree and collects data from Turbomole files.
Data is saved in dictionaries and written to .json format files.
Pandas is recommended for post processing of the data, 
while it also is possible to import .json files with Excel.

The program is written for Linux based OS.

After downloading the file "qcdc.py" the program can be called via `python3 ~/Downloads/qcdc.py` in the terminal.  

The directories should contain the default files like control, coord, energy, vibspectrum in correct format.  
The program starts in the working directory and walks through *everything* below,
however, Turbomole experience advices to **keep it flat**.


I recommend to install miniconda for beginners:
https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html

Have a look at the link below for installing packages:
(https://packaging.python.org/en/latest/tutorials/installing-packages/)

The following libraries have to be installed:
* pandas
* os
* numpy
* re
* molmass (https://pypi.org/project/molmass/)

##### Best practice is hint:  
`mkdir ~/bin`  
`mv ~/Downloads/qcdc.py ~/bin/.`  
`chmod 744 ~/bin/qcdc.py`  
You should now be able to call the program by typing `qcdc.py` from every location.

### Recently:
Uploaded on Github :man_with_gua_pi_mao:

### Problems
Absent files are no problem but files with non-default format may lead to problems.
If you need certain data, it should be easy to expand the program.
Please let me know if you do so.
Feel free to contact me.

### Please, tell me what you think! :email:
https://www.bcp.fu-berlin.de/en/chemie/chemie/forschung/PhysTheoChem/agpaulus/group-members/phd-students/luca-steiner.html
