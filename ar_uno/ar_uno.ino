#define _dout 6
#define _sclk 7
#define _pdwn 8
#define _gain1 9
#define _gain2 10

#include <EEPROM.h>
#include "ADS1232.h"

ADS1232 weight = ADS1232(_pdwn, _sclk, _dout);
unsigned long t;
char buffer[50];
byte rx_bt;
const int calVal_eepromAdress = 0;
float newCalibrationValue;

void sensores()
{
    if (millis() > t + 100)
    {
        float i = weight.units_read(4);
        sprintf(buffer, "peso:%ld", (long)i);
        Serial.println(buffer);
        t = millis();
    }
}

void get_offset(){
  long t_new_offset = 0;
  t_new_offset = weight.raw_read(128);
  weight.OFFSET = t_new_offset;
  Serial.print("Calibration offset = ");Serial.println(weight.OFFSET);
}

void calibrate(){
  weight.SCALE = 1.0;
  weight.tare_of = 0;
  get_offset();
  Serial.println("Then send the weight of this mass (i.e. 100.0) from serial monitor.");
  float known_mass = 0;
  long t_raw_read = 0;
  float t_weight = 0;
  bool _resume = false;
  while (_resume == false)
  {
      if (Serial.available() > 0)
      {
          known_mass = Serial.parseFloat();
          if (known_mass != 0)
          {
              Serial.print("Known mass is: ");
              Serial.println(known_mass);
              _resume = true;
          }
      }
  }
  // do calibration based on a known weight
  t_raw_read = weight.raw_read(128);
  Serial.print("Units read = ");Serial.println(t_raw_read);
  newCalibrationValue = t_raw_read / known_mass;  // divide it to the weight of a CocaCola bottle
  EEPROM.put(calVal_eepromAdress, newCalibrationValue);
  EEPROM.get(calVal_eepromAdress, newCalibrationValue);
  weight.SCALE = newCalibrationValue;
  Serial.print("Calibration scale value = ");Serial.println(weight.SCALE);
}

void setup() {
  EEPROM.get(calVal_eepromAdress, newCalibrationValue);
  if (isnan(newCalibrationValue))
  {
      newCalibrationValue = -20.15;
  }
  Serial.begin(9600);
  pinMode(_gain1, OUTPUT);
  pinMode(_gain2, OUTPUT);
  digitalWrite(_gain1, HIGH);
  digitalWrite(_gain2, HIGH);
  delay(100);
  weight.power_up();
  weight.start(10000);
  get_offset();
  weight.SCALE = newCalibrationValue;
  while (!Serial)
    {
        weight._raw_read();
    }
}

void loop()
{
  sensores();
  if (Serial.available())
  {
    byte rx_bt = Serial.read();
    if (rx_bt == 116)
    {
      weight.set_tare_offset();
      Serial.println("Tare complete");
    }
    else
    {
        if (rx_bt == 99)
        {
            calibrate();
        }
    }
    rx_bt = 13;
  }
}