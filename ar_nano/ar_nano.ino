
#include <EEPROM.h>
#include "hx711_bm.h"

static boolean newDataReady = 0;
const int serialPrintInterval = 100; // increase value to slow down serial print activity
byte rx_bt;
const int calVal_eepromAdress = 0;
float newCalibrationValue;
unsigned long t;
char buffer[50];
HX711_ADC LoadCell(4, 5); // DT, SCK

void reset()
{
    rx_bt = 13;
}

void sensores()
{
    if (newDataReady && millis() > t + 100)
    {
        float i = LoadCell.getData();
        sprintf(buffer, "peso:%ld", (long)i);
        Serial.println(buffer);
        t = millis();
    }
}

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
    long stabilisingtime = 10000;
    LoadCell.start(stabilisingtime);
    while (!Serial)
    {
        ;
    }
    Serial.println("Cal val:");
    Serial.println(newCalibrationValue);
    Serial.print("HX711 measured settlingtime ms: ");
    Serial.println(LoadCell.getSettlingTime());
    Serial.print("HX711 measured sampling rate HZ: ");
    Serial.println(LoadCell.getSPS());
    LoadCell.setCalFactor(newCalibrationValue); // user set calibration factor (float)
    LoadCell.setSamplesInUse(3);
    Serial.println("Startup + calibration is complete");
}

void loop()
{
    if (LoadCell.update())
        newDataReady = true;

    sensores();

    if (Serial.available())
    {
        byte rx_bt = Serial.read();
        if (rx_bt == 116)
        {
            LoadCell.tareNoDelay();
            if (LoadCell.getTareStatus())
            {
                Serial.println("Tare complete");
            }
        }
        else
        {
            if (rx_bt == 99)
            {
                calibrate();
            }
        }
        reset();
    }
}