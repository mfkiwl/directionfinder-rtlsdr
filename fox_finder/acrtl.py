from rtlsdr import RtlSdr
from time import *
from matplotlib import mlab as mlab
import pynmea2
import serial
import os
import threading

class RtlPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        #####################################
        ##### configure RTL device  #########
        #####################################
        self.sdr                 =  RtlSdr()
        self.sdr.sample_rate     =  1e6  # Hz
        self.sdr.center_freq     =  27.035e6  # Hz
        self.sdr.freq_correction =  60   # PPM
        self.sdr.gain            =  'auto'
        self.current_value = None
        self.running = True #setting the thread running to true

        #RtlSdr variables
        self.samples = set()
        self.power = set()
        self.max_pow = -999999999

    def get_max(self):
        return self.max_pow

    def run(self):
        while True:
            self.samples = self.sdr.read_samples(16*1024)
            self.power, _ = mlab.psd(self.samples, NFFT=1024, Fs=self.sdr.sample_rate / 1e6)

            # search whole data set for maximum and minimum value
            for dat in self.power:
                if dat > self.max_pow:
                    self.max_pow = dat
            sleep(0.5)