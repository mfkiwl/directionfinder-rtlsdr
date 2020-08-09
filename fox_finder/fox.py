from rtlsdr import RtlSdr
from matplotlib import mlab as mlab
import serial
import pynmea2
import os
import time
from bluetooth import *
from gps import *
from acgps import GpsPoller
from acrtl import RtlPoller

class direction_finder():

	def __init__(self):
		#variable GPS thread utilitzada a init_gps()
		self.gpsd = None #seting the global variable
		self.gpsp = GpsPoller() # create the thread
		#bluetooth variables
		self.server_sock=BluetoothSocket( RFCOMM )
		self.server_sock.bind(("",PORT_ANY))
		self.server_sock.listen(1)

		self.port = self.server_sock.getsockname()[1]
		#per saver el uuid fer el comando sudo blkid
		self.uuid = "80571af6-21c9-48a0-9df5-cffb60cf79af"

		advertise_service( self.server_sock, "SampleServer",
		                   service_id = self.uuid,
		                   service_classes = [ self.uuid, SERIAL_PORT_CLASS ],
		                   profiles = [ SERIAL_PORT_PROFILE ], 
		                   #protocols = [ OBEX_UUID ] 
		                    )

		#variables del RtlSdr thread
		self.rtl = RtlPoller()


	def init_rtl(self):
		try:
		    self.rtl.start() # start it up
		    print("GPS enabled")
		except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
		    print ("\nKilling Thread...")
		    self.rtl.running = False
		    self.rtl.join() # wait for thread to finish


	def init_gps(self):
		try:
		    self.gpsp.start() # start it up
		    print("GPS enabled")
		except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
		    print ("\nKilling Thread...")
		    self.gpsp.running = False
		    self.gpsp.join() # wait for thread to finish

	def init_bluetooth(self):
		print("Waiting for connection on RFCOMM channel %d" % port)
		self.client_sock, self.client_info = self.server_sock.accept()    #Espera a que s'establieix la connexio bluetooth amb el mobil
		print("Accepted connection from ", self.client_info)
		print("Waiting to begin")
		try:
		    while True:
		        data = client_sock.recv(1024)
		        if (data == "ON"):
		            break
		except IOError:
		    pass
		print("EXECUTANT FOX APP")

	def main(self):
		while True:
			print (self.gpsd.fix.latitude)
			print (self.rtl.get_max())
			sleep(4)