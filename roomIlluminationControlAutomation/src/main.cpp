#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include <ESP32Servo.h>

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHAR_SENSOR_UUID    "beb5483e-36e1-4688-b7f5-ea07361b26a8"  // Notify (Lux data)
#define CHAR_CONTROL_UUID   "5c8c1a8e-5b69-4d68-bc2c-8d36b1f67270"  // Write (Servo angle)

#define PHOTO_PIN_1   26
#define PHOTO_PIN_2   25
#define SERVO_PIN     13

BLECharacteristic *pSensorCharacteristic;
BLECharacteristic *pControlCharacteristic;

Servo servo;
int currentServoAngle = 90;

// BLE write callback: update servo angle
class ControlCallback : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {
    std::string value = pCharacteristic->getValue();
    if (value.length() >= 1) {
      int angle = (uint8_t)value[0];
      angle = constrain(angle, 0, 180);
      servo.write(angle);
      currentServoAngle = angle;
      Serial.printf("Received angle from ITOM: %d\n", angle);
    }
  }
};

void setup() {
  Serial.begin(115200);
  servo.attach(SERVO_PIN, 500, 2400);  // Adjust pulse range if needed

  servo.write(0);
  delay(1000);
  servo.write(45);
  delay(1000);
  servo.write(25);
  delay(1000);
  servo.write(0);


  BLEDevice::init("ESP32_LightSensor_BLE");
  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Notify: Send photoresistor data
  pSensorCharacteristic = pService->createCharacteristic(
                            CHAR_SENSOR_UUID,
                            BLECharacteristic::PROPERTY_NOTIFY
                          );
  pSensorCharacteristic->addDescriptor(new BLE2902());

  // Write: Receive servo angle
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
  // Read sensors
  uint16_t photoValue1 = analogRead(PHOTO_PIN_1);
  uint16_t photoValue2 = analogRead(PHOTO_PIN_2);

  // Prepare data
  uint8_t buffer[4];
  buffer[0] = photoValue1 & 0xFF;
  buffer[1] = (photoValue1 >> 8) & 0xFF;
  buffer[2] = photoValue2 & 0xFF;
  buffer[3] = (photoValue2 >> 8) & 0xFF;

  // Send to ITOM
  pSensorCharacteristic->setValue(buffer, sizeof(buffer));
  pSensorCharacteristic->notify();

  delay(50); // ~20 Hz
}
