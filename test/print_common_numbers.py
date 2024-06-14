#!/usr/bin/env python3
import pandas as pd
import numpy as np
import sys

# Set the name of the script
thisname = sys.argv[0][:-3]

# Load data from JSON file and set 'RootFile' as the index
data = pd.read_json("data.json")
data = data.set_index('RootFile')

# Define column names for easier access
dg = 'Chemical Potential for Liquids'
spe = 'Single Point Energy'
xyz = 'xyz Coordinates'
xyz_name = 'xyz File Name'

# Test accessing data
#fphthal_svp = data[spe]['./censo_benzene/censo/CONF1/pbe0-d4/control']
#print(fphthal_svp)

#fphthal_xyz = data[xyz]['./censo_benzene/censo/CONF1/pbe0-d4/control']
#print(fphthal_xyz)

# Set index to data of one conformer
censo_files = data[data.index.str.contains('censo.out')]
censo_files = censo_files.dropna(axis=1, how='all')
print(censo_files['values'])
best_conformers = censo_files['conf']

print(censo_files.loc['./qcdc_test_data/meo/censo/censo.out'])

censo_files.loc['./qcdc_test_data/meo/censo/censo.out']


#fphthal_index = data.index[data.index.str.contains('./censo-benzene/')]
#fphthal_index = fphthal_index[fphthal_index.str.contains('/control')]
#fphthal = data.loc[fphthal_index]
#print(fphthal)
#lst = []
#for index in fphthal_index:
#    lst.append(fphthal[xyz][index])
#arr = np.asarray(lst)
#print(arr)
#shape = arr.shape
#print(shape)