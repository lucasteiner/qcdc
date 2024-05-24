#!/usr/bin/env python3
import pandas as pd
import numpy as np
import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
#from energydiagram import ED
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA

# Print the file location of the energydiagram module
# print(energydiagram.__file__)

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
fphthal_svp = data[spe]['./qcdc_test_data/f2omef/censo/CONF1/pbe0-d4/control']
#print(fphthal_svp)

fphthal_xyz = data[xyz]['./qcdc_test_data/f2omef/censo/CONF1/pbe0-d4/control']
#print(fphthal_xyz)

# Set index to data of one conformer
fphthal_index = data.index[data.index.str.contains('./qcdc_test_data/f2omef/censo/')]
fphthal_index = fphthal_index[fphthal_index.str.contains('/part0_sp/control')]
fphthal = data.loc[fphthal_index]
lst = []
for index in fphthal_index:
    lst.append(fphthal[xyz][index])
arr = np.asarray(lst)
print(arr)
shape = arr.shape
pca_input = arr.reshape(shape[0], shape[1]*shape[2])
pca_input.shape

pca = PCA(n_components=3)
xyz_pca = pca.fit_transform(pca_input)
xyz_pca.shape

# Plotting
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')
ax.scatter(xyz_pca[:, 0], xyz_pca[:, 1], xyz_pca[:, 2], color='c')

# Add title and labels
ax.set_title('3D PCA Scatter Plot')
ax.set_xlabel('PCA Component 1')
ax.set_ylabel('PCA Component 2')
ax.set_zlabel('PCA Component 3')

plt.show()
