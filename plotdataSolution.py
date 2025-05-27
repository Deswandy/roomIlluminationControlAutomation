import numpy as np

# --- Step 1: Load CSV (skip header) ---
filename = r"C:\Users\emily\OneDrive\Desktop\light_data.csv"
intensity = np.loadtxt(filename, delimiter=",", skiprows=1)

# --- Step 2: Find the peak intensity and its index ---
peak_value = np.max(intensity)
peak_index = np.argmax(intensity)

# --- Step 3: (Optional) Calculate time if needed (assuming 100 Hz sampling) ---
fs = 100.0  # sampling rate
peak_time = peak_index / fs

# --- Step 4: Print result ---
print(f"Peak intensity: {peak_value:.4f} at index {peak_index} (time = {peak_time:.4f} s)")
