import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("C:/Users/MAGRANA/Desktop/Arnau/GPS/points.txt", delim_whitespace=True)

mymap = plt.imread("C:/Users/MAGRANA/Desktop/Arnau/GPS/map.png")


BBox = (df.longitude.min(),   df.longitude.max(),      
         df.latitude.min(), df.latitude.max())


fig, ax = plt.subplots(8,7)

ax.scatter(df.longitude, df.latitude, zorder=1, alpha= 0.2, c='b', s=10)

ax.set_title('Plotting Spatial Data on Riyadh Map')
ax.set_xlim(BBox[0],BBox[1])
ax.set_ylim(BBox[2],BBox[3])

ax.imshow(mymap, zorder=0, extent = BBox, aspect= 'equal')