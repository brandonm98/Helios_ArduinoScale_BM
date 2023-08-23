import RPi.GPIO as GPIO
import spidev
import time
import json
from DigitalFilter.DigitalFilter import LPF

filter_s = LPF(1, [1], "lowpass",design="butter", fs=7500)

# Pin definition
RST_PIN = 26
CS_PIN = 27
DRDY_PIN = 22

SPI = spidev.SpiDev(0, 0)

def digital_write(pin, value):
    GPIO.output(pin, value)

def digital_read(pin):
    return GPIO.input(DRDY_PIN)

def delay_ms(delaytime):
    time.sleep(delaytime // 1000.0)

def spi_writebyte(data):
    SPI.writebytes(data)
    
def spi_readbytes(reg):
    return SPI.readbytes(reg)
    
def module_init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RST_PIN, GPIO.OUT)
    GPIO.setup(CS_PIN, GPIO.OUT)
    GPIO.setup(DRDY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    SPI.max_speed_hz = 2000000
    SPI.mode = 0b01
    return 0

# gain channel
ADS1256_GAIN_E = {'ADS1256_GAIN_1' : 0, # GAIN   1
                  'ADS1256_GAIN_2' : 1,	# GAIN   2
                  'ADS1256_GAIN_4' : 2,	# GAIN   4
                  'ADS1256_GAIN_8' : 3,	# GAIN   8
                  'ADS1256_GAIN_16' : 4,# GAIN  16
                  'ADS1256_GAIN_32' : 5,# GAIN  32
                  'ADS1256_GAIN_64' : 6,# GAIN  64
                 }

# data rate
ADS1256_DRATE_E = {'ADS1256_30000SPS' : 0xF0, # reset the default values
                   'ADS1256_15000SPS' : 0xE0,
                   'ADS1256_7500SPS' : 0xD0,
                   'ADS1256_3750SPS' : 0xC0,
                   'ADS1256_2000SPS' : 0xB0,
                   'ADS1256_1000SPS' : 0xA1,
                   'ADS1256_500SPS' : 0x92,
                   'ADS1256_100SPS' : 0x82,
                   'ADS1256_60SPS' : 0x72,
                   'ADS1256_50SPS' : 0x63,
                   'ADS1256_30SPS' : 0x53,
                   'ADS1256_25SPS' : 0x43,
                   'ADS1256_15SPS' : 0x33,
                   'ADS1256_10SPS' : 0x20,
                   'ADS1256_5SPS' : 0x13,
                   'ADS1256_2d5SPS' : 0x03
                  }

# registration definition
REG_E = {'REG_STATUS' : 0,  # x1H
         'REG_MUX' : 1,     # 01H
         'REG_ADCON' : 2,   # 20H
         'REG_DRATE' : 3,   # F0H
         'REG_IO' : 4,      # E0H
         'REG_OFC0' : 5,    # xxH
         'REG_OFC1' : 6,    # xxH
         'REG_OFC2' : 7,    # xxH
         'REG_FSC0' : 8,    # xxH
         'REG_FSC1' : 9,    # xxH
         'REG_FSC2' : 10,   # xxH
        }

# command definition
CMD = {'CMD_WAKEUP' : 0x00,     # Completes SYNC and Exits Standby Mode 0000  0000 (00h)
       'CMD_RDATA' : 0x01,      # Read Data 0000  0001 (01h)
       'CMD_RDATAC' : 0x03,     # Read Data Continuously 0000   0011 (03h)
       'CMD_SDATAC' : 0x0F,     # Stop Read Data Continuously 0000   1111 (0Fh)
       'CMD_RREG' : 0x10,       # Read from REG rrr 0001 rrrr (1xh)
       'CMD_WREG' : 0x50,       # Write to REG rrr 0101 rrrr (5xh)
       'CMD_SELFCAL' : 0xF0,    # Offset and Gain Self-Calibration 1111    0000 (F0h)
       'CMD_SELFOCAL' : 0xF1,   # Offset Self-Calibration 1111    0001 (F1h)
       'CMD_SELFGCAL' : 0xF2,   # Gain Self-Calibration 1111    0010 (F2h)
       'CMD_SYSOCAL' : 0xF3,    # System Offset Calibration 1111   0011 (F3h)
       'CMD_SYSGCAL' : 0xF4,    # System Gain Calibration 1111    0100 (F4h)
       'CMD_SYNC' : 0xFC,       # Synchronize the A/D Conversion 1111   1100 (FCh)
       'CMD_STANDBY' : 0xFD,    # Begin Standby Mode 1111   1101 (FDh)
       'CMD_RESET' : 0xFE,      # Reset to Power-Up Values 1111   1110 (FEh)
      }

class ADS1256:
    def __init__(self):
        self.rst_pin = RST_PIN
        self.cs_pin = CS_PIN
        self.drdy_pin = DRDY_PIN
        self.OFFSET = 0.0
        self.SETPOINT = 0xFFFF
        self.tare_weight = 0
        self.off_count = 0
        self.print_time = time.time()
        self.cal_time = time.time()
        self.DEBUG_SIGNAL = False
        try:
            with open("config.json", "r") as f:
                self.SCALE = float(json.load(f)["calFactor"])
        except:
            print("CONFIG FILE NOT FOUND")
            self.SCALE = 1.0
            

    def ADS1256_reset(self):
        digital_write(self.rst_pin, GPIO.HIGH)
        delay_ms(200)
        digital_write(self.rst_pin, GPIO.LOW)
        delay_ms(200)
        digital_write(self.rst_pin, GPIO.HIGH)
    
    def ADS1256_WriteCmd(self, reg):
        digital_write(self.cs_pin, GPIO.LOW)#cs  0
        spi_writebyte([reg])
        digital_write(self.cs_pin, GPIO.HIGH)#cs 1
    
    def ADS1256_WriteReg(self, reg, data):
        digital_write(self.cs_pin, GPIO.LOW)#cs  0
        spi_writebyte([CMD['CMD_WREG'] | reg, 0x00, data])
        digital_write(self.cs_pin, GPIO.HIGH)#cs 1
        delay_ms(10)
        
    def ADS1256_Read_data(self, reg):
        digital_write(self.cs_pin, GPIO.LOW)#cs  0
        spi_writebyte([CMD['CMD_RREG'] | reg, 0x00])
        data = spi_readbytes(1)
        digital_write(self.cs_pin, GPIO.HIGH)#cs 1
        return data
        
    def ADS1256_WaitDRDY(self):
        p = time.time()
        while digital_read(self.drdy_pin):
            if(time.time() - p > 10):
                print ("Time Out ...\r\n")
                pass
            
    def ADS1256_ReadChipID(self):
        self.ADS1256_WaitDRDY()
        id = self.ADS1256_Read_data(REG_E['REG_STATUS'])
        id = id[0] >> 4
        print("ID REG: ", id)
        return id

    def ADS1256_init(self):
        if (module_init() != 0):
            return -1
        self.ADS1256_reset()
        id = self.ADS1256_ReadChipID()
        if id == 3 :
            print("ID Read success  ")
        else:
            print("ID Read failed   ")
            return -1
        return 0
        
    def _raw_read(self):
        self.ADS1256_WaitDRDY()
        digital_write(self.cs_pin, GPIO.LOW)#cs  0
        spi_writebyte([CMD['CMD_RDATA']])
        buf = spi_readbytes(3)
        digital_write(self.cs_pin, GPIO.HIGH)#cs 1
        read = (buf[0]<<16) & 0xff0000
        read |= (buf[1]<<8) & 0xff00
        read |= buf[2]
        if read & (1 << 23) !=0:
            read = (~read) - 1
        read += 1 << 24
        read = read >> 0
        return read - self.OFFSET
        
    def raw_read(self, times):
        out_data = []
        for i in range(times):
            out_data.append(self._raw_read())
        return sum(out_data)/times
    
    def units_read(self, times):
        return self.raw_read(times)/self.SCALE
        
    def start(self, timer):
        time_start = time.time()
        SPS_time = []
        while time.time()-time_start < timer:
            conv_time_start = time.time()
            self._raw_read()
            SPS_time.append(1/(time.time()-conv_time_start))
        print("SPS_rate: ", sum(SPS_time)/len(SPS_time))
            
    def calculate_offset(self):
        self.OFFSET = 0
        self.OFFSET = self.raw_read(7500)
        print("OFFSET calibration = ", self.OFFSET)
    
    def offset_gain_calibration(self):
        self.ADS1256_WaitDRDY()
        self.ADS1256_WriteCmd(CMD["CMD_SELFCAL"])
        delay_ms(7)
        print("CALIBRATION DONE!!")
    
    def stable_result(self, set_hysteresis=False):
        ws = self.units_read(1)
        ws = filter_s.filter(ws)
        ws -= self.tare_weight
        
        if ws > self.SETPOINT + 1:
            self.SETPOINT = ws
        else:
            if ws < self.SETPOINT - 1.5:
                self.SETPOINT = ws

        self.SETPOINT = 0 if self.SETPOINT <= 0.5 else self.SETPOINT
        if self.tare_weight < 0.5 and ws < 0.5:
            self.tare_weight = 0
            self.off_count += 1
        else:
            self.off_count = 0
        if time.time() - self.cal_time > 60 and self.off_count >= 15:
            self.offset_gain_calibration()
            self.calculate_offset()
            self.cal_time = time.time()
            self.cal_time = time.time()
        
        return self.SETPOINT if set_hysteresis else ws
        
    def init_reg(self):
        print("SET REGISTERS")
        self.ADS1256_WriteReg(REG_E["REG_STATUS"], 0b00000010)
        print(bin(self.ADS1256_Read_data(REG_E["REG_STATUS"])[0]))
        self.ADS1256_WriteReg(REG_E["REG_DRATE"], ADS1256_DRATE_E["ADS1256_7500SPS"])
        print(bin(self.ADS1256_Read_data(REG_E["REG_DRATE"])[0]))
        self.ADS1256_WriteReg(REG_E["REG_ADCON"], 0b00100111)
        print(bin(self.ADS1256_Read_data(REG_E["REG_ADCON"])[0]))
        self.ADS1256_WriteReg(REG_E["REG_MUX"], 0b00000001)
        print(bin(self.ADS1256_Read_data(REG_E["REG_MUX"])[0]))
        delay_ms(500)
        self.start(10)
        self.offset_gain_calibration()
        self.calculate_offset()
    
    def set_tare_weight(self):
        self.tare_weight = self.units_read(7500)
    
    def prepare_calibration(self):
        self.SCALE = 1.0
        self.offset_gain_calibration()
        self.calculate_offset()
    
    def calibrate_weight_scale(self, known_mass):
        print("known mass is: {}".format(known_mass))
        raw_value = self.raw_read(7500)
        if raw_value != 0:
            self.SCALE = raw_value / known_mass
        else:
            self.SCALE = 1.0
        with open("config.json", "w") as f:
            json.dump({"calFactor": self.SCALE}, f)
        print("new cal factor: {}".format(self.SCALE))