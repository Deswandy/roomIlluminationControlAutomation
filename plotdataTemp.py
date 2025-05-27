import numpy as np

# --- Step 1: Load the light intensity data from CSV ---
# The CSV file has one column of intensity values, and the first row is a header.
filename = r"C:\Users\emily\OneDrive\Desktop\light_data.csv"
intensity = np.loadtxt(filename, delimiter=",", skiprows=1)

# TODO: Step 2 - Find the maximum intensity value
# Use a NumPy function to get the highest number in the 'intensity' array
peak_value = ...  # ← your code here

# TODO: Step 3 - Find the index (position) where the peak occurs
# Use another NumPy function to find the index of the maximum value
peak_index = ...  # ← your code here

# TODO: Step 4 (optional) - Convert index to time (assume sampling rate = 100 Hz)
# time = index / sample rate
fs = 100.0  # sample rate in Hz
peak_time = ...  # ← your code here

# TODO: Step 5 - Print the result
# Use print() to show the peak value, index, and time
print("Peak intensity:", ...)       # ← fill in
print("At index:", ...)             # ← fill in
print("Which is at time:", ..., "seconds")  # ← fill in
