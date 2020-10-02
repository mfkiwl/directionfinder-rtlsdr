#Llibreries generals
import threading
import os
import serial
import math
from matplotlib import mlab as mlab
from time import sleep

#Llibreries RTLSDR
from rtlsdr import RtlSdr

#Llibreria gps
from gps import *

#Llibreria Brujula
#https://makersportal.com/blog/2019/11/11/raspberry-pi-python-accelerometer-gyroscope-magnetometer
from mpu9250_i2c import *

NUM_BYTES = 1024


class Data(threading.thread):
	def __init__(self):
		threading.Thread.__init__(self)
		#variables a inicialitzar dins la classe data:
		#variables del GPS
		self.gpsd = gps(mode=WATCH_ENABLE)

		#variables de la brujula
		self.ax,self.ay,self.az=0,0,0

		#variables del RTLSDR
		self.sdr                 =  RtlSdr()
		self.sdr.sample_rate     =  1e6  # Hz
		self.sdr.center_freq     =  27.035e6  # Hz
		self.sdr.freq_correction =  60   # PPM
		self.sdr.gain            =  'auto'

	#Captura la maxima senyal del RTLSDR.
	def get_signal_power(self):
		middle = int(len(self.power) / 2)
		self.middle_data = self.power[middle-50:middle+50]

		for dat in self.power:
        	if dat > self.max_signal:
            	self.max_signal = dat
        return self.max_signal

	#Loop principal del thread. Llegir dades de Brujula, GPS i RTLSDR.
	def run(self):
		while True:
			#Llegeixo dades del GPS
			self.gpsd.next()
			#Llegeixo dades de la brujula


			#Llegeixo dades del RTLSDR. Divideixo el NFFT en 4 per tenir menys data i que operi mes rapid. Revisar aizo del NUM_BYTES
    		self.power, _ = mlab.psd(self.sdr.read_samples(NUM_BYTES), NFFT=NUM_BYTES//4, pad_to=NUM_BYTES, Fs=self.sdr.sample_rate/1e6)