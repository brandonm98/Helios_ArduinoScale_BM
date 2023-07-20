
#include "HX711.h"

HX711 scale;

uint8_t dataPin = 2;
uint8_t clockPin = 3;


void setup()
{
  Serial.begin(9600);
  Serial.println(__FILE__);
  Serial.print("LIBRARY VERSION: ");
  Serial.println(HX711_LIB_VERSION);
  Serial.println();

  scale.begin(dataPin, clockPin);

  // TODO find a nice solution for this calibration..
  // load cell factor 20 KG
  // scale.set_scale(127.15);

  // load cell factor 5 KG
  scale.set_scale(420.0983);       // TODO you need to calibrate this yourself.
  // reset the scale to zero = 0
  scale.tare(20);
}


void loop()
{
  if (scale.is_ready())
  {
    Serial.println(scale.get_units(1));
  }
}