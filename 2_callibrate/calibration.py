import asyncio
import matplotlib.pyplot as plt
from matplotlib.widgets import MultiCursor
from bleak import BleakClient, BleakScanner, BleakError
from collections import deque

# BLE config
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "ESP32_LightSensor_BLE"

# Constants for conversion
ADC_RESOLUTION = 4095
VREF = 3.3
R_FIXED = 10000  # ohms
A_COEFF = 500000
B_COEFF = 1

# Plotting data buffer
max_points = 100
time_data = deque(maxlen=max_points)
photo1_data = deque(maxlen=max_points)
photo2_data = deque(maxlen=max_points)

# Shared data for thread-safe communication
latest_values = {"photo1": None, "photo2": None}

# === Conversion Functions ===

def adc_to_voltage(adc_value, adc_resolution=ADC_RESOLUTION, vref=VREF):
    return (adc_value / adc_resolution) * vref

def voltage_to_resistance_swapped(v_out, r_fixed=R_FIXED, v_in=VREF):
    if v_out == 0:
        return float('inf')  # avoid division by zero
    return r_fixed * ((v_in - v_out) / v_out)

def resistance_to_lux(resistance, A=A_COEFF, B=B_COEFF):
    if resistance <= 0:
        return 0
    return (A / resistance) ** (1 / B)

def adc_to_lux(adc_value):
    voltage = adc_to_voltage(adc_value)
    resistance = voltage_to_resistance_swapped(voltage)
    lux = resistance_to_lux(resistance)
    return lux

# === Plotting ===

plt.ion()
fig, ax = plt.subplots()
line1, = ax.plot([], [], label="Photo1 (Lux)")
line2, = ax.plot([], [], label="Photo2 (Lux)")
multi = MultiCursor(fig.canvas, (ax,), color="r", lw=1)
ax.set_title("Live BLE Light Sensor Data (Lux)")
ax.set_xlabel("Sample")
ax.set_ylabel("Lux")
ax.legend()
plt.show()

def safe_update_plot():
    if latest_values["photo1"] is None:
        return

    time_data.append(len(time_data))
    photo1_data.append(latest_values["photo1"])
    photo2_data.append(latest_values["photo2"])

    line1.set_data(range(len(photo1_data)), list(photo1_data))
    line2.set_data(range(len(photo2_data)), list(photo2_data))

    ax.relim()
    ax.autoscale_view()
    fig.canvas.draw()
    fig.canvas.flush_events()

# === BLE ===

def notification_handler(sender, data):
    try:
        if len(data) == 4:
            raw1 = int.from_bytes(data[0:2], 'little')
            raw2 = int.from_bytes(data[2:4], 'little')

            lux1 = adc_to_lux(raw1)
            lux2 = adc_to_lux(raw2)

            print(f"Raw1: {raw1}, Lux1: {lux1:.2f} | Raw2: {raw2}, Lux2: {lux2:.2f}")

            latest_values["photo1"] = lux1
            latest_values["photo2"] = lux2
        else:
            print(f"Unexpected data length: {len(data)}")
    except Exception as e:
        print(f"Error processing notification data: {e}")

async def find_device(name, timeout=10):
    print("Scanning for BLE devices...")
    try:
        devices = await BleakScanner.discover(timeout=timeout)
    except BleakError as e:
        print(f"Scanner error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected scanning error: {e}")
        return None

    for device in devices:
        if device.name == name:
            print(f"Found device: {device.name} ({device.address})")
            return device
    print(f"Device '{name}' not found during scan.")
    return None

async def connect_and_listen():
    while True:
        device = await find_device(DEVICE_NAME)
        if not device:
            print("Retrying scan in 5 seconds...")
            await asyncio.sleep(5)
            continue

        try:
            async with BleakClient(device.address) as client:
                if not await client.is_connected():
                    print("Failed to connect to device.")
                    await asyncio.sleep(5)
                    continue

                print("Connected to ESP32!")

                try:
                    await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
                except BleakError as e:
                    print(f"Failed to start notifications: {e}")
                    continue

                print("Listening for notifications. Press Ctrl+C to stop.")
                while await client.is_connected():
                    safe_update_plot()
                    await asyncio.sleep(0.1)

                print("Device disconnected.")

        except BleakError as e:
            print(f"BLE Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        print("Reconnecting in 5 seconds...")
        await asyncio.sleep(5)

# === Main ===

if __name__ == "__main__":
    try:
        asyncio.run(connect_and_listen())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting gracefully.")
