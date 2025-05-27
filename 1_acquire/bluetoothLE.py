#import pip
# pip.main(['install', 'bleak'])


import asyncio
from bleak import BleakClient, BleakScanner, BleakError

SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "ESP32_LightSensor_BLE"

def notification_handler(sender, data):
    try:
        if len(data) == 4:
            photo1 = int.from_bytes(data[0:2], 'little')
            photo2 = int.from_bytes(data[2:4], 'little')
            print(f"Photo1: {photo1} | Photo2: {photo2}")
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
                connected = await client.is_connected()
                if not connected:
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
                    await asyncio.sleep(1)

                print("Device disconnected.")

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
        print("\nProgram interrupted by user. Exiting gracefully.")

