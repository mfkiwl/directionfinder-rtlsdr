#Llibreries generals
import threading
import os
import serial
import math
from matplotlib import mlab as mlab
from time import sleep

#Llibreries RTLSDR
from rtlsdr import RtlSdr


NUM_BYTES = 1024
maxim = -999


sdr                 =  RtlSdr()
sdr.sample_rate     =  1e6  # Hz
sdr.center_freq     =  27.035e6  # Hz
sdr.freq_correction =  60   # PPM
sdr.gain            =  'auto'


#Captura la maxima senyal del RTLSDR.
def get_signal_power():
	max_signal=-99
	middle = int(len(power) / 2)
	middle_data = power[middle-50:middle+50]

	for dat in power:
    	if dat > max_signal:
        	max_signal = dat
    return max_signal


while True:
#Llegeixo dades del RTLSDR. Divideixo el NFFT en 4 per tenir menys data i que operi mes rapid. Revisar aizo del NUM_BYTES
	x = sdr.read_samples(NUM_BYTES)
	print (len(x))
	power, _ = mlab.psd(x, NFFT=NUM_BYTES//4, pad_to=NUM_BYTES, Fs=sdr.sample_rate/1e6)
	print(len(power))

	maxim = get_signal_power()



	#Opening and Closing a file "MyFile.txt" 
	# for object name file1. 
	file1 = open("MyFile.txt","a") 
	file1.write(f"{maxim} \n") 
	file1.close() 

	sleep(0.2)