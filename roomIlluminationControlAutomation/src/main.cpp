#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include <ESP32Servo.h>

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHAR_SENSOR_UUID    "beb5483e-36e1-4688-b7f5-ea07361b26a8"  // Notify (ADC data)
#define CHAR_CONTROL_UUID   "5c8c1a8e-5b69-4d68-bc2c-8d36b1f67270"  // Write (Servo angle override)

#define PHOTO_PIN_1   26
#define PHOTO_PIN_2   25
#define SERVO_PIN     13

BLECharacteristic *pSensorCharacteristic;
BLECharacteristic *pControlCharacteristic;

Servo servo;
int currentServoAngle = 90;
bool overrideMode = false; // True if ITOM writes servo angle

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

  // Attach servo
  servo.attach(SERVO_PIN, 500, 2400);
  servo.write(currentServoAngle);

  // BLE setup
  BLEDevice::init("ESP32_LightSensor_BLE");
  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);

  pSensorCharacteristic = pService->createCharacteristic(
                            CHAR_SENSOR_UUID,
                            BLECharacteristic::PROPERTY_NOTIFY
                          );
  pSensorCharacteristic->addDescriptor(new BLE2902());

  pControlCharacteristic = pService->createCharacteristic(
                             CHAR_CONTROL_UUID,
                             BLECharacteristic::PROPERTY_WRITE
                           );
  pControlCharacteristic->setCallbacks(new ControlCallback());

  pService->start();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  BLEDevice::startAdvertising();

  Serial.println("BLE Sensor + Servo ready");
}

void loop() {
  // Read light levels
  uint16_t adc1 = analogRead(PHOTO_PIN_1);
  uint16_t adc2 = analogRead(PHOTO_PIN_2);

  // Send to ITOM (ADC values)
  uint8_t buffer[4];
  buffer[0] = adc1 & 0xFF;
  buffer[1] = (adc1 >> 8) & 0xFF;
  buffer[2] = adc2 & 0xFF;
  buffer[3] = (adc2 >> 8) & 0xFF;
  pSensorCharacteristic->setValue(buffer, sizeof(buffer));
  pSensorCharacteristic->notify();

  // Auto-servo control (only if not overridden)
  if (!overrideMode) {
    // Average light
    uint16_t avgADC = (adc1 + adc2) / 2;

    // Convert light (dark = 0°, bright = 180°)
    int angle = map(avgADC, 0, 4095, 0, 180);
    angle = constrain(angle, 0, 180);

    if (angle != currentServoAngle) {
      servo.write(angle);
      currentServoAngle = angle;
      Serial.printf("Auto angle from light: %d (ADC avg: %d)\n", angle, avgADC);
    }
  }

  delay(100); // 10 Hz
}
