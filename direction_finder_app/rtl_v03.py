# -*- coding: utf-8 -*-
from rtlsdr import RtlSdr
from matplotlib import mlab as mlab
import serial
import pynmea2
import os
from gps import *
from time import *
import time
import threading
from bluetooth import *
#llibreries pel compass
import smbus        #import SMBus module of I2C
import math


'''brujula'''
__author__ = "Niccolo Rigacci"
__copyright__ = "Copyright 2018 Niccolo Rigacci <niccolo@rigacci.org>"
__license__ = "GPLv3-or-later"
__email__ = "niccolo@rigacci.org"
__version__ = "0.1.4"

DFLT_BUS = 1
DFLT_ADDRESS = 0x0d

REG_XOUT_LSB = 0x00     # Output Data Registers for magnetic sensor.
REG_XOUT_MSB = 0x01
REG_YOUT_LSB = 0x02
REG_YOUT_MSB = 0x03
REG_ZOUT_LSB = 0x04
REG_ZOUT_MSB = 0x05
REG_STATUS_1 = 0x06     # Status Register.
REG_TOUT_LSB = 0x07     # Output Data Registers for temperature.
REG_TOUT_MSB = 0x08
REG_CONTROL_1 = 0x09    # Control Register #1.
REG_CONTROL_2 = 0x0a    # Control Register #2.
REG_RST_PERIOD = 0x0b   # SET/RESET Period Register.
REG_CHIP_ID = 0x0d      # Chip ID register.

# Flags for Status Register #1.
STAT_DRDY = 0b00000001  # Data Ready.
STAT_OVL = 0b00000010   # Overflow flag.
STAT_DOR = 0b00000100   # Data skipped for reading.

# Flags for Status Register #2.
INT_ENB = 0b00000001    # Interrupt Pin Enabling.
POL_PNT = 0b01000000    # Pointer Roll-over.
SOFT_RST = 0b10000000   # Soft Reset.

# Flags for Control Register 1.
MODE_STBY = 0b00000000  # Standby mode.
MODE_CONT = 0b00000001  # Continuous read mode.
ODR_10HZ = 0b00000000   # Output Data Rate Hz.
ODR_50HZ = 0b00000100
ODR_100HZ = 0b00001000
ODR_200HZ = 0b00001100
RNG_2G = 0b00000000     # Range 2 Gauss: for magnetic-clean environments.
RNG_8G = 0b00010000     # Range 8 Gauss: for strong magnetic fields.
OSR_512 = 0b00000000    # Over Sample Rate 512: less noise, more power.
OSR_256 = 0b01000000
OSR_128 = 0b10000000
OSR_64 = 0b11000000     # Over Sample Rate 64: more noise, less power.


class QMC5883L(object):
    """Interface for the QMC5883l 3-Axis Magnetic Sensor."""
    def __init__(self,
                 i2c_bus=DFLT_BUS,
                 address=DFLT_ADDRESS,
                 output_data_rate=ODR_10HZ,
                 output_range=RNG_2G,
                 oversampling_rate=OSR_512):

        self.address = address
        self.bus = smbus.SMBus(i2c_bus)
        self.output_range = output_range
        self._declination = 1.0
        self._calibration = [[1.364, 0.003, 0.033],
                             [-0.118, 1.337, -0.063],
                             [0.021, -0.036, 1.426]]
        self._bias = [1713.317,1881.857,1068.749]
        chip_id = self._read_byte(REG_CHIP_ID)
        if chip_id != 0xff:
            msg = "Chip ID returned 0x%x instead of 0xff; is the wrong chip?"
            logging.warning(msg, chip_id)
        self.mode_cont = (MODE_CONT | output_data_rate | output_range
                          | oversampling_rate)
        self.mode_stby = (MODE_STBY | ODR_10HZ | RNG_2G | OSR_64)
        self.mode_continuous()

    def __del__(self):
        """Once finished using the sensor, switch to standby mode."""
        self.mode_standby()

    def mode_continuous(self):
        """Set the device in continuous read mode."""
        self._write_byte(REG_CONTROL_2, SOFT_RST)  # Soft reset.
        self._write_byte(REG_CONTROL_2, INT_ENB)  # Disable interrupt.
        self._write_byte(REG_RST_PERIOD, 0x01)  # Define SET/RESET period.
        self._write_byte(REG_CONTROL_1, self.mode_cont)  # Set operation mode.

    def mode_standby(self):
        """Set the device in standby mode."""
        self._write_byte(REG_CONTROL_2, SOFT_RST)
        self._write_byte(REG_CONTROL_2, INT_ENB)
        self._write_byte(REG_RST_PERIOD, 0x01)
        self._write_byte(REG_CONTROL_1, self.mode_stby)  # Set operation mode.

    def _write_byte(self, registry, value):
        self.bus.write_byte_data(self.address, registry, value)
        time.sleep(0.01)

    def _read_byte(self, registry):
        return self.bus.read_byte_data(self.address, registry)

    def _read_word(self, registry):
        """Read a two bytes value stored as LSB and MSB."""
        low = self.bus.read_byte_data(self.address, registry)
        high = self.bus.read_byte_data(self.address, registry + 1)
        val = (high << 8) + low
        return val

    def _read_word_2c(self, registry):
        """Calculate the 2's complement of a two bytes value."""
        val = self._read_word(registry)
        if val >= 0x8000:  # 32768
            return val - 0x10000  # 65536
        else:
            return val

    def get_data(self):
        """Read data from magnetic and temperature data registers."""
        i = 0
        [x, y, z, t] = [None, None, None, None]
        while i < 20:  # Timeout after about 0.20 seconds.
            status = self._read_byte(REG_STATUS_1)
            if status & STAT_OVL:
                # Some values have reached an overflow.
                msg = ("Magnetic sensor overflow.")
                if self.output_range == RNG_2G:
                    msg += " Consider switching to RNG_8G output range."
                logging.warning(msg)
            if status & STAT_DOR:
                # Previous measure was read partially, sensor in Data Lock.
                x = self._read_word_2c(REG_XOUT_LSB)
                y = self._read_word_2c(REG_YOUT_LSB)
                z = self._read_word_2c(REG_ZOUT_LSB)
                continue
            if status & STAT_DRDY:
                # Data is ready to read.
                x = self._read_word_2c(REG_XOUT_LSB)
                y = self._read_word_2c(REG_YOUT_LSB)
                z = self._read_word_2c(REG_ZOUT_LSB)
                t = self._read_word_2c(REG_TOUT_LSB)
                break
            else:
                # Waiting for DRDY.
                time.sleep(0.01)
                i += 1
        return [x, y, z, t]

    def get_magnet_raw(self):
        """Get the 3 axis values from magnetic sensor."""
        [x, y, z, t] = self.get_data()
        return [x, y, z]

    def get_magnet(self):
        """Return the horizontal magnetic sensor vector with (x, y) calibration applied."""
        [x, y, z] = self.get_magnet_raw()
        if x is None or y is None:
            [x1, y1, z1] = [x, y, z]
        else:
            c = self._calibration
            b = self._bias
            x = x - b[0]
            y = y - b[1]
            z = z - b[2]
            x1 = x * c[0][0] + y * c[0][1] + c[0][2]
            y1 = x * c[1][0] + y * c[1][1] + c[1][2]
            z1 = x * c[2][0] + y * c[2][1] + z*c[2][2]
        return [x1, y1]

    def get_bearing_raw(self):
        """Horizontal bearing (in degrees) from magnetic value X and Y."""
        [x, y, z] = self.get_magnet_raw()
        if x is None or y is None:
            return None
        else:
            b = math.degrees(math.atan2(y, x))
            if b < 0:
                b += 360.0
            return b

    def get_bearing(self):
        """Horizontal bearing, adjusted by calibration and declination."""
        [x, y] = self.get_magnet()
        if x is None or y is None:
            return None
        else:
            b = math.degrees(math.atan2(y, x))
            if b < 0:
                b += 360.0
            b += self._declination
            if b < 0.0:
                b += 360.0
            elif b >= 360.0:
                b -= 360.0
        return b

    def get_temp(self):
        """Raw (uncalibrated) data from temperature sensor."""
        [x, y, z, t] = self.get_data()
        return t

    def set_declination(self, value):
        """Set the magnetic declination, in degrees."""
        try:
            d = float(value)
            if d < -180.0 or d > 180.0:
                logging.error(u'Declination must be >= -180 and <= 180.')
            else:
                self._declination = d
        except:
            logging.error(u'Declination must be a float value.')

    def get_declination(self):
        """Return the current set value of magnetic declination."""
        return self._declination

    def set_calibration(self, value):
        """Set the 3x3 matrix for horizontal (x, y) magnetic vector calibration."""
        c = [[1.364, 0.003, 0.033],[-0.118, 1.337, -0.063],[0.021, -0.036, 1.426]]
        try:
            for i in range(0, 3):
                for j in range(0, 3):
                    c[i][j] = float(value[i][j])
            self._calibration = c
        except:
            logging.error(u'Calibration must be a 3x3 float matrix.')

    def get_calibration(self):
        """Return the current set value of the calibration matrix."""
        return self._calibration

    declination = property(fget=get_declination,
                           fset=set_declination,
                           doc=u'Magnetic declination to adjust bearing.')

    calibration = property(fget=get_calibration,
                           fset=set_calibration,
                           doc=u'Transformation matrix to adjust (x, y) magnetic vector.')
'''fi brujula'''
#####################################
##### variables del programa  #######
#####################################
bluetooth_missatge = ''
max_pow          =  0 #Guarda el valor de potencia maxim en una lectura de dades, passa a ser 0 cada cop que s'executa la funcio get_data()
max_power_temp   =  0 #Valor que representa el MAXIM dels valors de max_pow durant un interval de temps definit.
lat              =  0
longi            =  0
angle_brujula    =  0
totes_senyals    =  []
long2            =  0
lat2             =  0
counter_sp       =  0
counter_sp_msg   =  0
maxims           =  []
count_max        =  0
NUM_MAXIMS       =  10
minima_senyal    =  99999
maxima_senyal    =  0
maxima_senyal2   =  0
canvi            = False
cercle_bool      = 'N'
cercle_lat       = 0
cercle_long      = 0
MAX_1            = 0
MAX_2            = 0
maxims_plens     = False   #Fins que no esta la llista plena no paro de omplir element
#####################################
##### configure RTL device  #########
#####################################
sdr                 =  RtlSdr()
sdr.sample_rate     =  1e6  # Hz
sdr.center_freq     =  27.035e6  # Hz
sdr.freq_correction =  60   # PPM
sdr.gain            =  'auto'

#####################################
##### configure GPS device  #########
#####################################
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
        
gpsd = gps(mode=WATCH_ENABLE)    #variable GPS class

#####################################
##### configure COMPASS device  #####
#####################################
sensor=QMC5883L()

#Declaro THREAD del GPS
gpsp = GpsPoller() # create the thread
try:
    gpsp.start() # start it up
except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    print ("\nKilling Thread...")
    gpsp.running = False
    gpsp.join() # wait for thread to finish

#BLUETOOTH CODI, crea la connexio client - server per a transferir dades
#LA PART ON ESPERA LA CONNEXIO HA D'ANAR ABANS D'INICIAR EL MAIN LOOP
server_sock=BluetoothSocket( RFCOMM )
server_sock.bind(("",PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]
#per saver el uuid fer el comando sudo blkid
uuid = "80571af6-21c9-48a0-9df5-cffb60cf79af"

advertise_service( server_sock, "SampleServer",
                   service_id = uuid,
                   service_classes = [ uuid, SERIAL_PORT_CLASS ],
                   profiles = [ SERIAL_PORT_PROFILE ], 
                   #protocols = [ OBEX_UUID ] 
                    )

#####################################
####### CLASSES I FUNCIONS  #########
#####################################
#Funcio que em guarda la potencia maxima que ha rebut
def get_data():
    global max_pow
    samples = sdr.read_samples(16*1024)
    power, _ = mlab.psd(samples, NFFT=1024, Fs=sdr.sample_rate / 1e6)
    max_pow = 0

    # search whole data set for maximum and minimum value
    for dat in power:
        if dat > max_pow:
            max_pow = dat

#Classe per a tenir les variables de les diferents linies en una taula d'aquest objecte
class class_linia():
    def __init__(self):
        self.potencia_senyal = 0
        self.latitud         = 0
        self.longitud        = 0
        self.orientacio      = 0
        self.latitud_2       = 0
        self.longitud_2       = 0
        self.pendent         = 0
        self.terme_independent = 0
linia_temp       =  class_linia()

def afegeix_linea(pot, lat, long, ori):
    global totes_senyals
    linia = class_linia()
    linia.potencia_senyal = pot
    linia.latitud= lat
    linia.longitud = long
    linia.orientacio = ori
    totes_senyals.append(linia)

    
def reset_linia_temp():
    global linia_temp
    linia_temp.potencia_senyal=0
    linia_temp.latitud=0
    linia_temp.longitud=0
    linia_temp.orientacio=0

#Part del programa que troba les interseccions de les diferents linies i guarda en una variable la variable Y o N, i lat i long
def interseccio_linies():
    global maxims, totes_senyals, cercle_bool, cercle_lat, cercle_long, MAX_1, MAX_2, maxima_senyal, maxima_senyal2
    #Calculo el pendent i terme independent de totes les senyals maximes.
    for i in maxims:
        totes_senyals[i].pendent           =  (totes_senyals[i].latitud_2-totes_senyals[i].latitud)/(totes_senyals[i].longitud_2-totes_senyals[i].longitud)
        totes_senyals[i].terme_independent = totes_senyals[i].latitud - totes_senyals[i].pendent * totes_senyals[i].longitud
    #Ara, primer el que fare sera agafar les dos senyals amb mes força i trobar la intereseccio.
    #Es a dir, trobar els dos valors maxims d'una taula totes_senyals[maxim].potencia_senyal
    #LOOP QUE EM TROBA ELS DOS VALORS MAXIMS DE TOTES_SENYALS EN LA TAULA DE MAXIMS
        if (totes_senyals[i].potencia_senyal > maxima_senyal):
            maxima_senyal = totes_senyals[i].potencia_senyal
            MAX_1 = i
        else:
            if (totes_senyals[i].potencia_senyal > maxima_senyal2):
                maxima_senyal2 = totes_senyals[i].potencia_senyal
                MAX_2 = i
    try:
        cercle_bool = 'Y'
        cercle_long = (totes_senyals[MAX_2].terme_independent-totes_senyals[MAX_1].terme_independent)/(totes_senyals[MAX_2].pendent-totes_senyals[MAX_1].pendent)
        cercle_lat  = totes_senyals[MAX_1].pendent*cercle_long + totes_senyals[MAX_1].terme_independent
    except IOError:
        cercle_bool = 'N'
        cercle_long = 0
        cercle_lat  = 0
        print("No es troba interessecio")

''' 
Comença el programa. Primer de tot espero la connexio bluetooth, despres, he de fer que apretis un boto i comenci el loop principal.

'''
print("Waiting for connection on RFCOMM channel %d" % port)

client_sock, client_info = server_sock.accept()    #Espera a que s'establieix la connexio bluetooth amb el mobil
print("Accepted connection from ", client_info)
print("Esperant inici")
try:
    while True:
        data = client_sock.recv(1024)
        if (data == "ON"):
            break
except IOError:
    pass
print("EXECUTANT FOX HUNTER")

#LOOP PRINCIPAL DEL PROGRAMA
while True:
    for i in range (20):                             #FOR I en un interval a definir (aprox 45 sec)
        get_data()                                      #agafo les dades del RTL_SDR i guardo el valor de maxima potencia en una variable global
        if (max_pow > linia_temp.potencia_senyal):
            linia_temp.potencia_senyal = max_pow
            linia_temp.latitud= gpsd.fix.latitude
            linia_temp.longitud = gpsd.fix.longitude
            linia_temp.orientacio = sensor.get_bearing()           #si la variable que estic lleguint es mes fran que la variable anterior, la guardo.
        sleep(0.1)
    afegeix_linea(linia_temp.potencia_senyal,linia_temp.latitud,linia_temp.longitud,linia_temp.orientacio)

    #Si la longitud de la llista on hi han guardats els maxims es mes petita que el maxim de linies que hi han d'avber(10):
    if (len(maxims) < NUM_MAXIMS):
        #Crea un altre element a la llista de maxims amb el valor de l'index de totes_senyals aon sta la senyal en questio
        counter_sp = len(maxims)
        maxims.append(len(maxims))
        canvi = True           #Fa que s'actgivi la part de programa que m0envia dades per Bluetooth

    if (len(maxims) == NUM_MAXIMS):   #Te PINTA QUE VA DAVANT DE L'ALTRE IFF
        maxims_plens = True
    #Si hi han tots els maxims, es pot comparar els diferents valors que hihan guardats
    if (maxims_plens):
        #_max te el valor de els diferents index que hi han a la llista de maxims
        for _max in maxims:
            #Si la senyal que hi ha es mes baixa que minima_senyal (arxiu temporal), substitueix mima senyal
            if (totes_senyals[_max].potencia_senyal < minima_senyal):
                minima_senyal = totes_senyals[_max].potencia_senyal #minim senyal = senyal miima que hi ha en la taula de maxims
                index_min_pot = _max                                #index de totes_senyals on esta la senyal minima
                counter_sp  = maxims.index(_max)                    #num d'element a la llista de maxims
                #MINIMA_SENYAL I INDEX_MIN_POT s'han de formatejar al acabar la iteracio
        if (totes_senyals[index_min_pot].potencia_senyal < linia_temp.potencia_senyal):
            maxims[counter_sp] =  len(totes_senyals)-1  #Subsitueixo l'index on hi ha el minim dels maxims per la longitud de la taula de totes_senyals, que equival al numero d'element-
            canvi = True            
            #substitueixo el valor que hi havia a maxims per el nou valor maxim
            #el nou valor es el nou que acaba d'entrar, per tant equival a la llargada de la llista totes_senyals
        interseccio_linies()

    #En cas que s'hagi afegit una nova linia(quan encara no estan totes), o be quan es modifiqui algun maxim,calcula l'altre punt de la recta, i el guarda en la mateixa taula
    if (canvi):
        totes_senyals[len(totes_senyals)-1].latitud_2  = totes_senyals[len(totes_senyals)-1].latitud  + 20*math.sin(totes_senyals[len(totes_senyals)-1].orientacio)  #sumo la part sinus a la latitud i cosinus a longitud.
        totes_senyals[len(totes_senyals)-1].longitud_2 = totes_senyals[len(totes_senyals)-1].longitud + 20*math.cos(totes_senyals[len(totes_senyals)-1].orientacio)
        string_linia = "[[" + str(totes_senyals[len(totes_senyals)-1].latitud) + "," + str(totes_senyals[len(totes_senyals)-1].longitud) + "],[" + str(totes_senyals[len(totes_senyals)-1].latitud_2) + "," + str(totes_senyals[len(totes_senyals)-1].longitud_2) + "]]"
        counter_sp_msg = counter_sp + 1
        bluetooth_missatge = str(linia_temp.potencia_senyal) + '!' + str(counter_sp_msg) + '!' + string_linia + '!' + cercle_bool + '!' + str(cercle_long) + '!' + str(cercle_lat) #sumo els diferents elements que formen el missatge a enviar
        print("intento try")
        try:
            print("enviant missatge bth...")
            client_sock.send(bluetooth_missatge)  #envio el missatge per bluetooth
            print("enviat:  ")
            print (bluetooth_missatge)
        except IOError:
            pass
    
    #Un cop ha acabat l'interval, retorno a 0 els valors d'aquests tres per a que no interfereixi en la primera lectura de l'interval seguent
    reset_linia_temp()
    max_power_temp   = 0
    minima_senyal    = 999999999
    maxima_senyal    = 0
    maxima_senyal2   = 0
    canvi            = False
    counter_sp       = 0

