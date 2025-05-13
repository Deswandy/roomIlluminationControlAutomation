#include <AccelStepper.h>

// Define motor interface type (4 pins)
#define MOTOR_INTERFACE_TYPE 4

// Create a stepper instance (IN1, IN3, IN2, IN4 — typical for 28BYJ-48 with ULN2003)
AccelStepper myStepper(MOTOR_INTERFACE_TYPE, 14, 26, 27, 25);

const int ldrOutsidePin = 34; // ADC1_CH6
const int ldrInsidePin = 35;  // ADC1_CH7
const int relayPin = 33;      // Relay control

const int stepsPerRevolution = 2048; // For stepper
const int thresholdOutside = 2500;
const int thresholdInside = 2000;

bool blindsClosed = false;

void setup()
{
  Serial.begin(115200);

  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, LOW);

  myStepper.setMaxSpeed(1000);
  myStepper.setSpeed(200);
}

void loop()
{
  int lightOutside = analogRead(ldrOutsidePin);
  int lightInside = analogRead(ldrInsidePin);

  Serial.print("Outside: ");
  Serial.print(lightOutside);
  Serial.print(" | Inside: ");
  Serial.println(lightInside);

  if (lightOutside > thresholdOutside && !blindsClosed)
  {
    Serial.println("Too bright outside: closing blinds");
    myStepper.moveTo(stepsPerRevolution);
    while (myStepper.distanceToGo() != 0)
    {
      myStepper.run();
    }
    blindsClosed = true;
  }
  else if (lightOutside <= thresholdOutside && blindsClosed)
  {
    Serial.println("Outside OK: opening blinds");
    myStepper.moveTo(0);
    while (myStepper.distanceToGo() != 0)
    {
      myStepper.run();
    }
    blindsClosed = false;
  }

  if (lightInside < thresholdInside)
  {
    digitalWrite(relayPin, HIGH);
  }
  else
  {
    digitalWrite(relayPin, LOW);
  }

  delay(3000);
}
