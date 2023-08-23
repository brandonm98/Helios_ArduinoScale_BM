import time
from ADC1256.pyADS1256 import *
import RPi.GPIO as GPIO
import time


try:
	#init config
	ADC = ADS1256()
	ADC.ADS1256_init()
	ADC.init_reg()
	
	#prepare calibration
	ADC.prepare_calibration()
	print("NOW")
	time.sleep(5)
	#make calibration with known scale
	ADC.calibrate_weight_scale(4000)
	time.sleep(5)
	#do tare
	#ADC.set_tare_weight()
	#ADC.DEBUG_SIGNAL = True
	st = time.time()
	while 1:
		#get stable read from ADC in real units
		ads_res = ADC.stable_result()
		if (time.time() - st) > 0.1:
			st = time.time()
			print("PESO: {}".format(ads_res))
		
		
except Exception as ee:
	GPIO.cleanup()
	print("EXCPTION: ", ee)
	exit()
