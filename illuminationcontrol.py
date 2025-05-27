import time
import numpy as np
from itom import dataIO, dataObject

# Dummy function to simulate getting filtered light data
def get_filtered_light_intensity():
    # For demo: generate a random value between 100 and 600
    return np.random.randint(100, 600)

# Dummy function to adjust light
def adjust_light(intensity):
    print(f"Adjusting light... Current intensity: {intensity}")
    # Place your control code here (e.g., send command to LED driver)

# Main control loop
def control_light_loop():
    print("=== START CONTROL ===")

    while True:
        # Step 1: Monitor filtered data
        light_intensity = get_filtered_light_intensity()
        print(f"Monitored Light Intensity: {light_intensity}")

        # Step 2: Check condition
        if 200 < light_intensity < 500:
            print("Light intensity in acceptable range.")
            time.sleep(1)  # Delay before next check
            continue  # Go back to monitoring
        else:
            # Step 3: Adjust light
            adjust_light(light_intensity)
            time.sleep(1)  # Delay before next check

# Run the control loop
control_light_loop()
