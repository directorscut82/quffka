#!/usr/bin/env python3
#   encoding: utf-8
#   cook_datasets.py

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

with open('datasets/letter/letter-recognition.data', 'r') as f:
    lines = f.readlines()
    
data = np.empty([len(lines), 16])
labels = np.empty(len(lines))
for i,line in enumerate(lines):
    line = line.strip()
    line = line.split(',')
    data[i, :] = np.array(line[1:])
    labels[i] = ord(line[0]) - 65

np.save('datasets/letter/data', data)
np.save('datasets/letter/labels', labels)

data = pd.read_excel('datasets/CCPP/Folds5x2_pp.xlsx')
x = data.loc[:, ['AT', 'V', 'AP', 'RH']].values
y = data.PE.values
x = StandardScaler().fit_transform(x)

np.save('datasets/CCPP/data', x)
np.save('datasets/CCPP/labels', y)
