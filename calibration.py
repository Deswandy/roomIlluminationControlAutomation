import time
import numpy as np
import matplotlib.pyplot as plt
from itom import dataObject
import serial

# === CONFIG ===
SERIAL_PORT = "COM6"         # Change this to match your actual port
BAUD_RATE = 115200
NUM_SAMPLES = 100            # Number of readings to collect

# === STEP 1: Receive Data from ESP32 ===
def read_esp32_data():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for ESP32 to reset

    light_values = []

    print("Receiving data from ESP32...")
    while len(light_values) < NUM_SAMPLES:
        try:
            line = ser.readline().decode().strip()
            if line.isdigit():
                light = int(line)
                light_values.append(light)
                print(f"Received: {light}")
        except Exception as e:
            print("Error:", e)
            continue

    ser.close()
    return np.array(light_values)

# === STEP 2: Calibrate Values ===
def calibrate_values(raw_values):
    # Linear normalization: scale to [0, 1000]
    min_val = np.min(raw_values)
    max_val = np.max(raw_values)
    if max_val == min_val:
        print("Warning: constant data")
        return raw_values

    scaled = 1000 * (raw_values - min_val) / (max_val - min_val)
    print("Calibration complete.")
    return scaled

# === STEP 3–5: Acquire Light Value and Plot ===
def plot_light_data(time_axis, light_values):
    plt.figure()
    plt.plot(time_axis, light_values, color='blue', marker='o')
    plt.title("Light Intensity Over Time")
    plt.xlabel("Sample Index")
    plt.ylabel("Calibrated Light Value")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# === MAIN WORKFLOW ===
def run_calibration():
    print("=== START CALIBRATION ===")
    
    raw_data = read_esp32_data()
    calibrated_data = calibrate_values(raw_data)
    
    print("Light value of the room acquired.")
    
    x_axis = np.arange(len(calibrated_data))  # Index as x-axis
    plot_light_data(x_axis, calibrated_data)

    print("=== CALIBRATION COMPLETE ===")

# === RUN ===
run_calibration()
