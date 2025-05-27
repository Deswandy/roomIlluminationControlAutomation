import asyncio
import numpy as np
import matplotlib.pyplot as plt
from bleak import BleakClient, BleakScanner, BleakError

# === CONFIG ===
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "ESP32_LightSensor_BLE"
NUM_SAMPLES = 100

# === Global Buffers ===
photo1_values = []
photo2_values = []

# === Calibration ===
def calibrate_values(raw_values):
    min_val = np.min(raw_values)
    max_val = np.max(raw_values)
    if max_val == min_val:
        print("Warning: constant data")
        return raw_values
    return 1000 * (raw_values - min_val) / (max_val - min_val)

def plot_light_data(photo1, photo2):
    x_axis = np.arange(len(photo1))
    plt.figure()
    plt.plot(x_axis, photo1, label="Photoresistor 1")
    plt.plot(x_axis, photo2, label="Photoresistor 2")
    plt.title("Calibrated Light Intensity Over Time")
    plt.xlabel("Sample Index")
    plt.ylabel("Light Value (Calibrated)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# === BLE Handler ===
def notification_handler(sender, data):
    global photo1_values, photo2_values

    if len(data) == 4:
        photo1 = int.from_bytes(data[0:2], 'little')
        photo2 = int.from_bytes(data[2:4], 'little')
        print(f"Received -> Photo1: {photo1}, Photo2: {photo2}")

        photo1_values.append(photo1)
        photo2_values.append(photo2)

        if len(photo1_values) >= NUM_SAMPLES:
            asyncio.create_task(process_and_exit())
    else:
        print("Unexpected data length:", len(data))

async def process_and_exit():
    print("Collected enough samples. Calibrating and plotting...")

    # Stop event loop after plotting
    loop = asyncio.get_event_loop()
    loop.stop()

    raw1 = np.array(photo1_values)
    raw2 = np.array(photo2_values)
    cal1 = calibrate_values(raw1)
    cal2 = calibrate_values(raw2)
    plot_light_data(cal1, cal2)

async def find_device():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover()
    for d in devices:
        if d.name == DEVICE_NAME:
            return d
    return None

async def connect_and_listen():
    while True:
        try:
            device = await find_device()
            if not device:
                print(f"Device '{DEVICE_NAME}' not found. Retrying in 5 seconds...")
                await asyncio.sleep(5)
                continue

            print(f"Found device: {device.address}, connecting...")
            async with BleakClient(device.address) as client:
                if await client.is_connected():
                    print("Connected to ESP32!")
                    await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
                    
                    while len(photo1_values) < NUM_SAMPLES:
                        await asyncio.sleep(1)

                    await client.stop_notify(CHARACTERISTIC_UUID)
                    break  # Exit after getting enough samples

        except BleakError as e:
            print(f"BLE Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        print("Reconnecting in 5 seconds...")
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(connect_and_listen())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
