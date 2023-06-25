#include <HX711_ADC.h>
#include <EEPROM.h>

int i;
int flag4 = 0; // SERIAL COM
byte tara;
const int calVal_eepromAdress = 0;
float newCalibrationValue;
long t;
char buffer[100];
unsigned long w;

HX711_ADC LoadCell(4, 5); // DT, SCK
String incomingString;
////////////////////////////////////////////
void reset()
{
    flag4 = 0; // SERIAL COM
    tara = 13;
    incomingString = "";
    delay(120);
}
////////////////////////////////////////////
void sensores()
{
    if (millis() > t + 100)
    {
        LoadCell.update();
        w = LoadCell.getData();
        sprintf(buffer, "peso:%ld", w);
        Serial.println(buffer);
        t = millis();
    }
}
////////////////////////////////////////////
void calibrate()
{
    Serial.println("***");
    Serial.println("Start calibration:");
    Serial.println("Place the load cell an a level stable surface.");
    Serial.println("Remove any load applied to the load cell.");
    LoadCell.update();
    LoadCell.tare();
    Serial.println("Tare complete");
    boolean _resume = false;
    Serial.println("Now, place your known mass on the loadcell.");
    Serial.println("Then send the weight of this mass (i.e. 100.0) from serial monitor.");
    float known_mass = 0;
    _resume = false;
    while (_resume == false)
    {
        LoadCell.update();
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
    LoadCell.refreshDataSet();                                    // refresh the dataset to be sure that the known mass is measured correct
    newCalibrationValue = LoadCell.getNewCalibration(known_mass); // get the new calibration value
    delay(150);
    EEPROM.put(calVal_eepromAdress, newCalibrationValue);
    EEPROM.get(calVal_eepromAdress, newCalibrationValue);
    LoadCell.setCalFactor(newCalibrationValue);
    Serial.print("Value ");
    Serial.print(newCalibrationValue);
    Serial.print(" saved to EEPROM address: ");
    Serial.println(calVal_eepromAdress);
    Serial.println("End calibration");
}
///////////////////////////////////////////////////////////////////////////////////////////////////////
void setup()
{
    Serial.begin(9600);
    EEPROM.get(calVal_eepromAdress, newCalibrationValue);
    if (isnan(newCalibrationValue))
    {
        newCalibrationValue = -20.15;
    }
    LoadCell.begin();
    // time to calibrate load cell
    long stabilisingtime = 5000;
    LoadCell.start(stabilisingtime);
    Serial.println("Cal val:");
    Serial.println(newCalibrationValue);
    LoadCell.setCalFactor(newCalibrationValue); // user set calibration factor (float)
    LoadCell.setSamplesInUse(4);
    Serial.println("Startup + calibration is complete");
}
/////////////////////////////////////////////////////////////////////////////////////////////////////
void loop()
{
    if (flag4 == 0)
    {
        sensores();
    }

    ///////////////TARA

    if (Serial.available())
    {
        byte tara = Serial.read();
        // tara == 't' in ascii code
        if (tara == 116)
        {
            int i = 0;
            LoadCell.tareNoDelay();
            while (LoadCell.getTareStatus())
            {
            }
            Serial.println("Tare complete");
        }
        else
        {
            if (tara == 99)
            {
                calibrate();
            }
        }
        reset();
    }
}