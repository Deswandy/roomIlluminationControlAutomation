from itom import plot1, dataObject, ui
import numpy as np
from collections import deque
import asyncio
from bleak import BleakClient, BleakScanner

SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "ESP32_LightSensor_BLE"

BUFFER_SIZE = 500
photo1_buf = deque(maxlen=BUFFER_SIZE)
photo2_buf = deque(maxlen=BUFFER_SIZE)

# Initialize empty data object
data = dataObject([2, BUFFER_SIZE], 'uint16')

# Open plot window and get a valid uiItem handle
winID = plot1(data)  # Returns int (plot window ID)
plotHandle = ui.getFigure(winID)  # Get full UI handle from window ID

# Set plot title
plotHandle.call("setTitle", "Real-Time Light Sensor Data")

def update_plot():
    if len(photo1_buf) > 0:
        new_data = dataObject([2, len(photo1_buf)], 'uint16')
        for i, val in enumerate(photo1_buf):
            new_data[0, i] = val
        for i, val in enumerate(photo2_buf):
            new_data[1, i] = val
        plotHandle.call("setSource", new_data)

def notification_handler(sender, data):
    if len(data) == 4:
        photo1 = int.from_bytes(data[0:2], 'little')
        photo2 = int.from_bytes(data[2:4], 'little')
        photo1_buf.append(photo1)
        photo2_buf.append(photo2)
        update_plot()

async def find_device(name):
    devices = await BleakScanner.discover(timeout=5.0)
    for device in devices:
        if device.name == name:
            return device
    return None

async def main():
    device = await find_device(DEVICE_NAME)
    if not device:
        print("Device not found.")
        return

    async with BleakClient(device.address) as client:
        if await client.is_connected():
            await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
            print("Connected and receiving data...")
            while await client.is_connected():
                await asyncio.sleep(0.05)

# Start asyncio BLE handling in background
import threading
threading.Thread(target=lambda: asyncio.run(main()), daemon=True).start()
