#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

#define LED_PIN 2
#define PHOTO_PIN_1 26
#define PHOTO_PIN_2 25

BLECharacteristic *pCharacteristic;

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  Serial.println("Starting BLE Light Sensor Service");

  BLEDevice::init("ESP32_LightSensor_BLE");
  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);

  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ |
                      BLECharacteristic::PROPERTY_NOTIFY
                    );

  pCharacteristic->addDescriptor(new BLE2902());

  pCharacteristic->setValue("Starting...");
  pService->start();

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();

  Serial.println("BLE advertising started");
}

void loop() {
  uint16_t photoValue1 = analogRead(PHOTO_PIN_1);
  uint16_t photoValue2 = analogRead(PHOTO_PIN_2);

  uint8_t buffer[4];  // 2 bytes for each sensor
  buffer[0] = photoValue1 & 0xFF;
  buffer[1] = (photoValue1 >> 8) & 0xFF;
  buffer[2] = photoValue2 & 0xFF;
  buffer[3] = (photoValue2 >> 8) & 0xFF;

  pCharacteristic->setValue(buffer, sizeof(buffer));
  pCharacteristic->notify();

  // Optional debug
  Serial.print("Photo1: ");
  Serial.print(photoValue1);
  Serial.print(" | Photo2: ");
  Serial.println(photoValue2);

  delay(10);  // ~100 Hz
}

