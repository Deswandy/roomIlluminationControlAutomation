import time
import numpy as np
import matplotlib.pyplot as plt
from itom import dataObject
import serial

# === CONFIG ===
SERIAL_PORT = "COM6"         # Change this to match your actual port
BAUD_RATE = 115200
NUM_SAMPLES = 100            # Number of readings to collect

# === STEP 1: Receive Data from ESP32 via Bluetooth ===
def read_esp32_data():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for ESP32 BT to settle

    photo1_values = []
    photo2_values = []

    print("Receiving Bluetooth data from ESP32...")
    while len(photo1_values) < NUM_SAMPLES:
        try:
            line1 = ser.readline().decode().strip()
            line2 = ser.readline().decode().strip()
            
            if line1.isdigit() and line2.isdigit():
                photo1_values.append(int(line1))
                photo2_values.append(int(line2))
                print(f"Received -> Photo1: {line1}, Photo2: {line2}")
        except Exception as e:
            print("Error:", e)
            continue

    ser.close()
    return np.array(photo1_values), np.array(photo2_values)


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
    
    raw_data1, raw_data2 = read_esp32_data()
    calibrated1 = calibrate_values(raw_data1)
    calibrated2 = calibrate_values(raw_data2)
    
    print("Light values acquired.")
    
    x_axis = np.arange(len(calibrated1))  # Index as x-axis
    plt.figure()
    plt.plot(x_axis, calibrated1, label="Photoresistor 1")
    plt.plot(x_axis, calibrated2, label="Photoresistor 2")
    plt.title("Calibrated Light Intensity Over Time")
    plt.xlabel("Sample Index")
    plt.ylabel("Light Value (Calibrated)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    print("=== CALIBRATION COMPLETE ===")


# === RUN ===
run_calibration()
