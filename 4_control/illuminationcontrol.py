import asyncio
import threading
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.widgets import MultiCursor
from bleak import BleakClient, BleakScanner
from collections import deque
import numpy as np
from scipy.signal import butter, filtfilt
import time

# BLE Config
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
CHARACTERISTIC_SERVO_UUID ="5c8c1a8e-5b69-4d68-bc2c-8d36b1f67270"
DEVICE_NAME = "ESP32_LightSensor_BLE"

# Constants
ADC_RESOLUTION = 4095
VREF = 3.3
R_FIXED = 10000
A_COEFF = 500000
B_COEFF = 1

# Buffers
max_points = 100
time_data = deque(maxlen=max_points)
photo1_data = deque(maxlen=max_points)
photo2_data = deque(maxlen=max_points)
latest_values = {"photo1": None, "photo2": None}

shutdown_event = threading.Event()

# --- PID Controller ---
class PIDController:
    def __init__(self, kp, ki, kd, setpoint=350, output_limits=(0, 90)):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        self._last_error = 0
        self._integral = 0
        self._last_time = None

    def compute(self, measurement):
        current_time = time.time()
        error = self.setpoint - measurement
        delta_time = current_time - self._last_time if self._last_time else 0
        delta_error = error - self._last_error if self._last_time else 0

        if delta_time > 0:
            self._integral += error * delta_time
            derivative = delta_error / delta_time
        else:
            derivative = 0

        output = (self.kp * error) + (self.ki * self._integral) + (self.kd * derivative)
        output = max(self.output_limits[0], min(self.output_limits[1], output))

        self._last_error = error
        self._last_time = current_time
        return output

# --- Conversion Functions ---
def adc_to_voltage(adc_value):
    return (adc_value / ADC_RESOLUTION) * VREF

def voltage_to_resistance_swapped(v_out):
    if v_out == 0:
        return float('inf')
    return R_FIXED * ((VREF - v_out) / v_out)

def resistance_to_lux(resistance):
    if resistance <= 0:
        return 0
    return (A_COEFF / resistance) ** (1 / B_COEFF)

def adc_to_lux(adc_value):
    voltage = adc_to_voltage(adc_value)
    resistance = voltage_to_resistance_swapped(voltage)
    return resistance_to_lux(resistance)

def apply_lowpass(data, cutoff=2.0, fs=50.0, order=2):
    if len(data) < order * 3:
        return data
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data)

# --- BLE Handler ---
def notification_handler(sender, data):
    try:
        if len(data) == 4:
            raw1 = int.from_bytes(data[0:2], 'little')
            raw2 = int.from_bytes(data[2:4], 'little')
            lux1 = adc_to_lux(raw1)
            lux2 = adc_to_lux(raw2)
            latest_values["photo1"] = lux1
            latest_values["photo2"] = lux2
            print(f"Raw1: {raw1}, Lux1: {lux1:.2f} | Raw2: {raw2}, Lux2: {lux2:.2f}")
    except Exception as e:
        print(f"Notification handler error: {e}")

async def find_device(name, timeout=10):
    print("Scanning for BLE devices...")
    try:
        devices = await BleakScanner.discover(timeout=timeout)
        for device in devices:
            if device.name == name:
                print(f"Found device: {device.name} ({device.address})")
                return device
    except Exception as e:
        print(f"BLE scan error: {e}")
    return None

async def connect_and_listen(pid_controller):
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
                    if latest_values["photo1"] is not None:
                        lux = latest_values["photo1"]
                        if lux < 200 or lux > 500:
                            angle = int(pid_controller.compute(lux))
                            angle = max(0, min(90, angle))
                            await client.write_gatt_char(CHARACTERISTIC_SERVO_UUID, bytes([angle]))
                            print(f"Sent servo angle: {angle}")
                    await asyncio.sleep(0.1)

                print("Disconnected from device.")
        except Exception as e:
            print(f"BLE error: {e}")
        await asyncio.sleep(5)

# --- GUI ---
class BLEPlotApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Live BLE Light Sensor with PID Control")

        self.cutoff = tk.DoubleVar(value=2.0)
        tk.Label(master, text="Cutoff Frequency (Hz)").pack()
        tk.Scale(master, variable=self.cutoff, from_=0.1, to=10.0,
                 resolution=0.1, orient=tk.HORIZONTAL, length=300).pack()

        self.fig, self.ax = plt.subplots()
        plt.close(self.fig)
        self.canvas = FigureCanvasTkAgg(self.fig, master)
        self.canvas.get_tk_widget().pack()

        self.line1, = self.ax.plot([], [], label="Photo1 (Lux)")
        self.line2, = self.ax.plot([], [], label="Photo2 (Lux)")
        self.multi = MultiCursor(self.fig.canvas, (self.ax,), color="r", lw=1)
        self.ax.set_title("Live BLE Light Sensor Data")
        self.ax.set_xlabel("Sample")
        self.ax.set_ylabel("Lux")
        self.ax.set_ylim(0, 1500)
        self.ax.legend()
        self.ax.grid(True)

        self.update_plot_loop()

    def update_plot_loop(self):
        if latest_values["photo1"] is not None:
            time_data.append(len(time_data))
            photo1_data.append(latest_values["photo1"])
            photo2_data.append(latest_values["photo2"])

            y1 = np.array(photo1_data)
            y2 = np.array(photo2_data)

            try:
                filtered1 = apply_lowpass(y1, cutoff=self.cutoff.get(), fs=10.0)
                filtered2 = apply_lowpass(y2, cutoff=self.cutoff.get(), fs=10.0)
            except ValueError:
                filtered1 = y1
                filtered2 = y2

            self.line1.set_data(range(len(filtered1)), filtered1)
            self.line2.set_data(range(len(filtered2)), filtered2)
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()
        self.master.after(100, self.update_plot_loop)

# --- Main ---
def main():
    root = tk.Tk()
    app = BLEPlotApp(root)
    pid = PIDController(kp=0.5, ki=0.05, kd=0.1)

    def on_closing():
        print("Shutting down...")
        shutdown_event.set()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    def run_ble():
        asyncio.run(connect_and_listen(pid))

    threading.Thread(target=run_ble, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    main()
