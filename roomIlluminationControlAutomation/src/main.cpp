#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

#define LED_PIN 2
#define PHOTO_PIN_1 13
#define PHOTO_PIN_2 12

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
  int photoValue1 = analogRead(PHOTO_PIN_1);
  int photoValue2 = analogRead(PHOTO_PIN_2);

  // Format readings
  String data = "Photo1: " + String(photoValue1) + " | Photo2: " + String(photoValue2);
  Serial.println(data);

  // Send over BLE
  pCharacteristic->setValue(data.c_str());
  pCharacteristic->notify();

  delay(1000);  // Send every 1 second
}
