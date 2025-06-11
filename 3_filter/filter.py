import asyncio
import threading
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.widgets import MultiCursor
from bleak import BleakClient, BleakScanner
from collections import deque
import numpy as np
import time
from scipy.signal import butter, filtfilt

start_time = time.time()

def apply_lowpass(data, cutoff=2.0, fs=10.0, order=2):
    if len(data) < (order * 3):
        return data
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data)


# BLE config
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "ESP32_SensorServo_BLE"

# Conversion constants
ADC_RESOLUTION = 4095
VREF = 3.3
R_FIXED = 10000
A_COEFF = 500000
B_COEFF = 1

# Data buffer
max_points = 100
time_data = deque(maxlen=max_points)
lux_data = deque(maxlen=max_points)
latest_lux = None

shutdown_event = threading.Event()

# === Conversion Functions ===
def adc_to_voltage(adc_value):
    # Clamp to avoid 0 or full-scale
    adc_value = max(1, min(adc_value, ADC_RESOLUTION - 1))
    return (adc_value / ADC_RESOLUTION) * VREF

def voltage_to_resistance(v_out):
    # Avoid singularity near 0 or VREF
    margin = 0.01
    if v_out <= margin or v_out >= VREF - margin:
        return float('inf')
    return R_FIXED * ((VREF - v_out) / v_out)

def resistance_to_lux(resistance):
    # Smooth nonlinear behavior
    if resistance <= 0 or resistance == float('inf'):
        return 0
    lux = (A_COEFF / resistance) ** (1 / B_COEFF)
    return max(0, min(lux, 5000))  # Limit lux to 0?5000 realistically

def adc_to_lux(adc_value):
    voltage = adc_to_voltage(adc_value)
    resistance = voltage_to_resistance(voltage)

    if resistance == float('inf'):
        # Near ADC max or min, handle gracefully
        if adc_value > ADC_RESOLUTION * 0.98:
            return 0  # sensor saturated
        elif adc_value < ADC_RESOLUTION * 0.02:
            return 0  # sensor dark
        else:
            return 0

    return resistance_to_lux(resistance)


# === BLE Notification Handler ===

def decode_light_data(data: bytearray) -> int:
    return int.from_bytes(data, byteorder='little')

def notification_handler(sender, data):
    global latest_lux
    raw_value = decode_light_data(data)
    lux = adc_to_lux(raw_value)
    latest_lux = lux
    print(f"Raw: {raw_value} | Lux: {lux:.2f}")

# === BLE Connection Logic ===

async def find_device(name, timeout=10):
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=timeout)
    for device in devices:
        if device.name and name in device.name:
            print(f"Found device: {device.name} ({device.address})")
            return device
    print(f"Device '{name}' not found.")
    return None

async def connect_and_listen():
    while not shutdown_event.is_set():
        device = await find_device(DEVICE_NAME)
        if not device:
            await asyncio.sleep(5)
            continue

        try:
            async with BleakClient(device.address) as client:
                if not await client.is_connected():
                    await asyncio.sleep(5)
                    continue

                print("Connected to ESP32!")
                await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

                while await client.is_connected() and not shutdown_event.is_set():
                    await asyncio.sleep(0.1)

                print("Disconnected from device.")
        except Exception as e:
            print(f"BLE error: {e}")

        print("Reconnecting in 5 seconds...")
        await asyncio.sleep(5)

# === GUI App ===

class BLEPlotApp:
    def __init__(self, master):
        self.master = master  # MUST BE FIRST before using `tk` variables
    
        # Cutoff frequency slider
        self.cutoff = tk.DoubleVar(value=2.0)
        tk.Label(master, text="Cutoff Frequency (Hz)").pack()
        tk.Scale(master, variable=self.cutoff, from_=0.1, to=10.0,
                 resolution=0.1, orient=tk.HORIZONTAL, length=300).pack()

        # Setup Matplotlib plot in Tkinter
        self.fig, self.ax = plt.subplots()
        plt.close(self.fig)
        self.canvas = FigureCanvasTkAgg(self.fig, master)
        self.canvas.get_tk_widget().pack()

        self.line_raw, = self.ax.plot([], [], 'k--', label="Raw Lux")        # dashed black
        self.line_filtered, = self.ax.plot([], [], 'b-', label="Filtered Lux")  # solid blue
        self.ax.legend(loc="upper right")
        self.multi = MultiCursor(self.fig.canvas, (self.ax,), color="red", lw=1)
        self.ax.set_title("Real-Time Light Sensor Data (Lux)")
        self.ax.set_xlabel("Sample")
        self.ax.set_ylabel("Lux")
        self.ax.set_ylim(0, 4000)  # Fixed height
        self.ax.grid(True)
        self.ax.legend()

        self.update_plot_loop()
    def update_plot_loop(self):
        if latest_lux is not None:
            timestamp = time.time() - start_time
            time_data.append(timestamp)
            lux_data.append(latest_lux)
    
            y = np.array(lux_data)
            try:
                y_filtered = apply_lowpass(y, cutoff=self.cutoff.get(), fs=10.0)
            except ValueError:
                y_filtered = y
    
            self.line_raw.set_data(range(len(y)), y)
            self.line_filtered.set_data(range(len(y_filtered)), y_filtered)
            self.ax.relim()
            self.ax.autoscale_view(scalex=True, scaley=True)
            self.ax.margins(y=0.1)
            self.canvas.draw()
        self.master.after(100, self.update_plot_loop)

# === Main Entry Point ===

def main():
    root = tk.Tk()
    app = BLEPlotApp(root)

    def on_closing():
        print("Shutting down...")
        shutdown_event.set()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    def run_ble():
        asyncio.run(connect_and_listen())

    threading.Thread(target=run_ble, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    main()
