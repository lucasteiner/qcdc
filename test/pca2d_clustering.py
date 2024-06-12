#!/usr/bin/env python3
import pandas as pd
import numpy as np
import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
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
#fphthal_svp = data[spe]['./censo_benzene/censo/CONF1/pbe0-d4/control']
#print(fphthal_svp)

#fphthal_xyz = data[xyz]['./censo_benzene/censo/CONF1/pbe0-d4/control']
#print(fphthal_xyz)

# Set index to data of one conformer
fphthal_index = data.index[data.index.str.contains('./censo-benzene/')]
fphthal_index = fphthal_index[fphthal_index.str.contains('/control')]
fphthal = data.loc[fphthal_index]
print(fphthal)
lst = []
for index in fphthal_index:
    lst.append(fphthal[xyz][index])
arr = np.asarray(lst)
print(arr)
shape = arr.shape
print(shape)
pca_input = arr.reshape(shape[0], shape[1]*shape[2])
pca_input.shape

pca = PCA(n_components=2)
xyz_pca = pca.fit_transform(pca_input)
xyz_pca.shape



clustering = DBSCAN(eps=1.0, min_samples=3)
labels = clustering.fit(xyz_pca).labels_

# Create a scatter plot
plt.figure(figsize=(10, 6))

# Get unique labels
unique_labels = np.unique(labels)

# Plot each cluster with a different color
for label in unique_labels:
    if label == -1:
        # Noise points
        color = 'k'
        marker = 'x'
    else:
        # Cluster points
        color = plt.cm.nipy_spectral(float(label) / len(unique_labels))
        marker = 'o'
    
    class_member_mask = (labels == label)
    
    xy = xyz_pca[class_member_mask]
    plt.scatter(xy[:, 0], xy[:, 1], c=[color], marker=marker, label=f'Cluster {label}' if label != -1 else 'Noise')

# Add title and labels
plt.title('DBSCAN Clustering on PCA-transformed Data')
plt.xlabel('PCA Component 1')
plt.ylabel('PCA Component 2')
plt.legend()
plt.show()
