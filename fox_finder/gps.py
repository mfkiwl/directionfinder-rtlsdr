from gps import *
from time import *
import threading

class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true
 
  def run(self):
    global gpsd
    while gpsp.running:
        gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer








#executar en el main:


gpsd = gps(mode=WATCH_ENABLE)    #variable GPS class

#Declaro THREAD del GPS
gpsp = GpsPoller() # create the thread
try:
    gpsp.start() # start it up
except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    print ("\nKilling Thread...")
    gpsp.running = False
    gpsp.join() # wait for thread to finish