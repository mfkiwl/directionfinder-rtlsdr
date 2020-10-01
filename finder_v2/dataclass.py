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




class Data(threading.thread):
	def __init__(self):
		threading.Thread.__init__(self)

		#variables a inicialitzar dins la classe data:
		#variables del GPS
		self.gpsd = gps(mode=WATCH_ENABLE)

		#variables de la brujula
		ax,ay,az=0,0,0

		#variables del RTLSDR
		self.sdr                 =  RtlSdr()
		self.sdr.sample_rate     =  1e6  # Hz
		self.sdr.center_freq     =  27.035e6  # Hz
		self.sdr.freq_correction =  60   # PPM
		self.sdr.gain            =  'auto'

	#Loop principal del thread. Llegir dades de Brujula, GPS i RTLSDR.
	def run(self):
		while True:
			#Llegeixo dades del GPS
			self.gpsd.next()
			#Llegeixo dades de la brujula

			#Llegeixo dades del RTLSDR
			self



