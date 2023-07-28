#ifndef ADS1232_h
#define ADS1232_h

#include "Arduino.h"

class ADS1232
{
  public:
    byte PDWN;         // power down pin
    byte SCLK;         // serial clock pin
    byte DOUT;         // serial data out pin
    long OFFSET = 0;   
    float SCALE = 1.0; // used to scale weight to grams/kg/ounces
    long tare_of = 0; // used for tare

    ADS1232(byte pdwn, byte sclk, byte dout);
    ~ADS1232();
    bool is_ready();
    void power_up();
    void power_down();
    void set_offset(long offset = 0);
    void set_scale(float scale = 1.0f);
    long _raw_read();
    long raw_read(byte times = 1);
    float units_read(byte times = 1);
    void set_tare_offset();
    void start(unsigned long t);
};

#endif