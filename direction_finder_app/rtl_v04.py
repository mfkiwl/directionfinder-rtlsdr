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

def afegeix_linea(pot, lat, longd, ori):
    global totes_senyals
    linia = class_linia()
    linia.potencia_senyal = pot
    linia.latitud= lat
    linia.longitud = longd
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
        get_data()
        latitudx=gpsd.fix.latitude                                      #agafo les dades del RTL_SDR i guardo el valor de maxima potencia en una variable global
        longitudx = gpsd.fix.longitude
        if i != 0:
            orientation =get_orientation(latitudx,longitudx, gpsd.fix.latitude, gpsd.fix.longitude)
        if (max_pow > linia_temp.potencia_senyal):
            linia_temp.potencia_senyal = max_pow
            linia_temp.latitud= gpsd.fix.latitude
            linia_temp.longitud = gpsd.fix.longitude
            ##
            ##
            ##
            ##CANVI!!!!!!!!!!!!!!!!!!!!!!!!!
            linia_temp.orientacio = orientation     #si la variable que estic lleguint es mes fran que la variable anterior, la guardo.
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

def get_orientation(lati, longi, lati2, longi2):
    return arctan((lati2-lati)/(longi2-longi))
