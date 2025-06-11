import asyncio
import matplotlib.pyplot as plt
from matplotlib.widgets import MultiCursor
from bleak import BleakClient, BleakScanner
from collections import deque

# BLE UUIDs
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHAR_IO_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "ESP32_SensorServo_BLE"

# Conversion constants
ADC_RESOLUTION = 4095
VREF = 3.3
R_FIXED = 10000  # 10k?
A_COEFF = 500000  # Empirical fit constant
B_COEFF = 1       # Empirical fit exponent

# Safe voltage limits to avoid math breakdowns
VOLTAGE_MIN = 0.05
VOLTAGE_MAX = VREF - 0.05

# Lux output limit
LUX_MAX = 10000

# Data buffers
max_points = 100
time_data = deque(maxlen=max_points)
lux_data = deque(maxlen=max_points)
latest_lux = None

# === Conversion Functions ===

def adc_to_voltage(adc_value):
    adc_value = min(max(adc_value, 1), ADC_RESOLUTION - 1)
    return (adc_value / ADC_RESOLUTION) * VREF

def voltage_to_resistance(v_out):
    v_out = min(max(v_out, VOLTAGE_MIN), VOLTAGE_MAX)
    try:
        return R_FIXED * ((VREF - v_out) / v_out)
    except ZeroDivisionError:
        return 1e-6  # Extremely low resistance
       
def resistance_to_lux(resistance):
    if resistance <= 0:
        return 0
    lux = (A_COEFF / resistance) ** (1 / B_COEFF)
    return min(lux, LUX_MAX)

def adc_to_lux(adc_value):
    voltage = adc_to_voltage(adc_value)
    resistance = voltage_to_resistance(voltage)
    return resistance_to_lux(resistance)

# === Plot Setup ===

plt.ion()
fig, ax = plt.subplots()
line, = ax.plot([], [], label="Lux")
multi = MultiCursor(fig.canvas, (ax,), color="red", lw=1)
ax.set_title("Real-Time Light Sensor Data (Lux)")
ax.set_xlabel("Sample")
ax.set_ylabel("Lux")
ax.set_ylim(0, 3000)
ax.legend()
plt.show()

def update_plot():
    if latest_lux is None:
        return

    time_data.append(len(time_data))
    lux_data.append(latest_lux)

    line.set_data(range(len(lux_data)), list(lux_data))
    ax.relim()
    ax.autoscale_view()
    fig.canvas.draw()
    fig.canvas.flush_events()

# === BLE Notification Handler ===

def decode_light_data(data: bytearray) -> int:
    return int.from_bytes(data, byteorder='little')

def notification_handler(sender, data):
    global latest_lux
    raw_value = decode_light_data(data)
    lux = adc_to_lux(raw_value)
    latest_lux = lux
    print(f"Raw: {raw_value} | Lux: {lux:.2f}")

# === Main Async Logic ===

async def main():
    print("Scanning for ESP32...")
    devices = await BleakScanner.discover()

    esp32 = next((d for d in devices if d.name and DEVICE_NAME in d.name), None)
    if not esp32:
        print("ESP32 device not found.")
        return

    print(f"Connecting to {esp32.name} ({esp32.address})")
    async with BleakClient(esp32.address) as client:
        if not await client.is_connected():
            print("Failed to connect.")
            return

        print("Connected! Subscribing to notifications...")
        await client.start_notify(CHAR_IO_UUID, notification_handler)

        print("Receiving data (press Ctrl+C to stop)...")
        try:
            while await client.is_connected():
                update_plot()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            await client.stop_notify(CHAR_IO_UUID)
            print("Stopped notifications.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
