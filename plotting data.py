import numpy as np
from itom import dataObject, plot

# --- Step 1: Load CSV (skip header) ---
filename = r"C:\Users\emily\OneDrive\Desktop\light_data.csv"
intensity = np.loadtxt(filename, delimiter=",", skiprows=1)

# --- Step 2: Create a column vector dataObject [rows, 1] ---
n = len(intensity)
signalObj = dataObject([n, 1], dtype="float32")  # 2D: n rows, 1 column

# --- Step 3: Copy data into Itom dataObject ---
for i in range(n):
    signalObj[i, 0] = float(intensity[i])  # Use [i, 0] index

# --- Step 4: Plot in Itom ---
plot(signalObj, "plot1D")
