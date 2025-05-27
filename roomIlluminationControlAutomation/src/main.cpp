#include <Arduino.h>

#define LED_PIN 2          // Onboard LED (optional)
#define PHOTO_PIN_1 13     // First photoresistor (analog input)
#define PHOTO_PIN_2 12     // Second photoresistor (analog input)

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);  // Optional, in case you use the LED
  Serial.println("Photoresistors activated...");
}

void loop() {
  // Read photoresistors
  int photoValue1 = analogRead(PHOTO_PIN_1);
  int photoValue2 = analogRead(PHOTO_PIN_2);

  Serial.print("Photoresistor 1: ");
  Serial.print(photoValue1);
  Serial.print(" | Photoresistor 2: ");
  Serial.println(photoValue2);

  delay(200);  // Delay for stability
}
