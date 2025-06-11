#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>        // Descriptor for notifications
#include <ESP32Servo.h>

#define SERVICE_UUID     "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHAR_IO_UUID     "beb5483e-36e1-4688-b7f5-ea07361b26a8"  // Read + Write + Notify

#define PHOTO_PIN_1      26
#define SERVO_PIN        13

BLECharacteristic *pIOCharacteristic;

Servo servo;
int currentServoAngle = 180;
bool overrideMode = false;

// BLE write callback: update servo angle
class ControlCallback : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {
    std::string value = pCharacteristic->getValue();
    if (value.length() >= 1) {
      int angle = (uint8_t)value[0];
      angle = constrain(angle, 0, 180);
      servo.write(angle);
      currentServoAngle = angle;
      overrideMode = true;
      Serial.printf("Received angle from ITOM: %d\n", angle);
    }
  }
};

void setup() {
  Serial.begin(115200);

  // Setup servo
  servo.attach(SERVO_PIN, 500, 2400);
  servo.write(currentServoAngle);

  // BLE init
  BLEDevice::init("ESP32_SensorServo_BLE");
  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);

  pIOCharacteristic = pService->createCharacteristic(
                        CHAR_IO_UUID,
                        BLECharacteristic::PROPERTY_READ |
                        BLECharacteristic::PROPERTY_WRITE |
                        BLECharacteristic::PROPERTY_NOTIFY   // <-- Added notify
                      );
  pIOCharacteristic->setCallbacks(new ControlCallback());
  pIOCharacteristic->addDescriptor(new BLE2902());  // <-- Required for notification clients

  pService->start();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  BLEDevice::startAdvertising();

  Serial.println("BLE ready: one light sensor + servo");
}

void loop() {
  // Read single light sensor
  uint16_t adc = analogRead(PHOTO_PIN_1);

  // Update BLE characteristic for reading
  uint8_t buffer[2];
  buffer[0] = adc & 0xFF;
  buffer[1] = (adc >> 8) & 0xFF;
  pIOCharacteristic->setValue(buffer, sizeof(buffer));
  pIOCharacteristic->notify();  // <-- Send updated value to subscribers

  delay(100); // 10 Hz loop
}
