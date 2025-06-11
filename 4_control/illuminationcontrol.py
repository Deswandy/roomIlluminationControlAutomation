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

# BLE Configuration
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "ESP32_SensorServo_BLE"

# Lux Conversion Constants
ADC_RESOLUTION = 4095
VREF = 3.3
R_FIXED = 10000
A_COEFF = 500000
B_COEFF = 1

# Control & Data Buffers
target_lux = 350
servo_angle = 90
angle_step = 1
time_data = deque(maxlen=100)
lux_data = deque(maxlen=100)
latest_lux = None
shutdown_event = threading.Event()

# PID Controller for gradual correction
class PIDController:
    def __init__(self, kp, ki, kd, output_limits=(0, 180)):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limits = output_limits
        self.setpoint = target_lux
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

# === Conversion Functions ===
def adc_to_voltage(adc_value):
    return (adc_value / ADC_RESOLUTION) * VREF

def voltage_to_resistance(v_out):
    if v_out <= 0.01 or v_out >= VREF - 0.01:
        return float('inf')
    return R_FIXED * ((VREF - v_out) / v_out)

def resistance_to_lux(resistance):
    if resistance <= 0 or resistance == float('inf'):
        return 0
    lux = (A_COEFF / resistance) ** (1 / B_COEFF)
    return max(0, min(lux, 5000))

def adc_to_lux(adc_value):
    voltage = adc_to_voltage(adc_value)
    resistance = voltage_to_resistance(voltage)
    return resistance_to_lux(resistance)

def apply_lowpass(data, cutoff=2.0, fs=10.0, order=2):
    if len(data) < order * 3:
        return data
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data)

# === BLE Notification Handler ===
def decode_light_data(data: bytearray) -> int:
    return int.from_bytes(data[:2], byteorder='little')

def notification_handler(sender, data):
    global latest_lux
    raw = decode_light_data(data)
    lux = adc_to_lux(raw)
    latest_lux = lux
    print(f"Raw: {raw} | Lux: {lux:.2f}")

# === BLE Connection Logic ===
async def find_device(name, timeout=10):
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=timeout)
    for device in devices:
        if device.name == name:
            print(f"Found device: {device.name} ({device.address})")
            return device
    return None

async def connect_and_listen(pid):
    global servo_angle

    while not shutdown_event.is_set():
        device = await find_device(DEVICE_NAME)
        if not device:
            await asyncio.sleep(5)
            continue

        try:
            async with BleakClient(device.address) as client:
                if not await client.is_connected():
                    continue

                print("Connected to ESP32!")
                await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

                while await client.is_connected() and not shutdown_event.is_set():
                    if latest_lux is not None:
                        if latest_lux < 200 or latest_lux > 500:
                            target_angle = int(pid.compute(latest_lux))
                            if abs(target_angle - servo_angle) > 0:
                                if target_angle > servo_angle:
                                    servo_angle += min(angle_step, target_angle - servo_angle)
                                else:
                                    servo_angle -= min(angle_step, servo_angle - target_angle)
                                servo_angle = max(0, min(180, servo_angle))
                                await client.write_gatt_char(CHARACTERISTIC_UUID, bytes([servo_angle]))
                                print(f"Adjusted Servo to: {servo_angle} (Lux: {latest_lux:.2f})")
                        else:
                            print(f"Lux within acceptable range: {latest_lux:.2f} lux")


                    await asyncio.sleep(0.1)

                print("Disconnected.")
        except Exception as e:
            print(f"BLE error: {e}")
        await asyncio.sleep(5)

# === GUI App ===
class BLEPlotApp:
    def __init__(self, master):
        self.master = master
        master.title("Single Light Sensor with PID-controlled Blinds")

        self.cutoff = tk.DoubleVar(value=2.0)
        tk.Label(master, text="Cutoff Frequency (Hz)").pack()
        tk.Scale(master, variable=self.cutoff, from_=0.1, to=10.0,
                 resolution=0.1, orient=tk.HORIZONTAL, length=300).pack()

        self.fig, self.ax = plt.subplots()
        plt.close(self.fig)
        self.canvas = FigureCanvasTkAgg(self.fig, master)
        self.canvas.get_tk_widget().pack()

        self.line_raw, = self.ax.plot([], [], 'k--', label="Raw Lux")
        self.line_filtered, = self.ax.plot([], [], 'b-', label="Filtered Lux")
        self.multi = MultiCursor(self.fig.canvas, (self.ax,), color="red", lw=1)
        self.ax.set_title("Real-Time Light Sensor Data (Lux)")
        self.ax.set_xlabel("Sample")
        self.ax.set_ylabel("Lux")
        self.ax.set_ylim(0, 2000)
        self.ax.grid(True)
        self.ax.legend()

        self.update_plot_loop()

    def update_plot_loop(self):
        if latest_lux is not None:
            time_data.append(len(time_data))
            lux_data.append(latest_lux)

            y = np.array(lux_data)
            try:
                y_filtered = apply_lowpass(y, cutoff=self.cutoff.get(), fs=10.0)
            except ValueError:
                y_filtered = y

            self.line_raw.set_data(range(len(y)), y)
            self.line_filtered.set_data(range(len(y_filtered)), y_filtered)
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()

        self.master.after(100, self.update_plot_loop)

# === Main Entry Point ===
def main():
    root = tk.Tk()
    app = BLEPlotApp(root)
    pid = PIDController(kp=0.8, ki=0.02, kd=0.1)

    def on_closing():
        print("Shutting down...")
        shutdown_event.set()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    def ble_thread():
        asyncio.run(connect_and_listen(pid))

    threading.Thread(target=ble_thread, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    main()
