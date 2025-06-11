import asyncio
from bleak import BleakClient, BleakScanner

# UUIDs (must match ESP32's)
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHAR_IO_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

def decode_light_data(data: bytearray) -> int:
    """Decode 2-byte light sensor value from ESP32."""
    return int.from_bytes(data, byteorder='little')

def notification_handler(sender, data):
    """Handle incoming BLE notifications (light sensor readings)."""
    light_value = decode_light_data(data)
    print(f"Light Sensor: {light_value} (Raw bytes: {list(data)})")

async def main():
    print("Scanning for ESP32...")
    devices = await BleakScanner.discover()

    esp32 = None
    for d in devices:
        if d.name and "ESP32_SensorServo_BLE" in d.name:
            esp32 = d
            break

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

        print("Receiving data for 30 seconds...")
        await asyncio.sleep(30)

        await client.stop_notify(CHAR_IO_UUID)
        print("Stopped notifications.")

# Run the async event loop
if __name__ == "__main__":
    asyncio.run(main())
