# import bluetooth
# from pyb import Pin, ADC
# from time import ticks_ms, ticks_diff, sleep_ms
# from ble_advertising import advertising_payload
#
# # Identifiant de l'advertiser
# my_name = "PIRAdv"
#
# # Icône pour une trame GAP
# _ADV_APPEARANCE_GENERIC_TAG = const(512)
#
# # Configuration du capteur PIR
# pir = Pin('D2', Pin.IN)
#
# # Configuration de la photodiode
# adc = ADC(Pin('A1'))  # Photodiode connectée à A1
# _MAX_INTENSITY = 255  # Intensité maximale pour RGB
#
# # Initialisation du BLE
# class BLE_Adv_Control:
#     def __init__(self, ble):
#         self._ble = ble
#         self._ble.active(True)
#
#     def advertise(self, interval_us=500000, message=None):
#         self._payload = advertising_payload(name=message, appearance=_ADV_APPEARANCE_GENERIC_TAG)
#         self._ble.gap_advertise(interval_us, adv_data=self._payload, connectable=False)
#
# # Fonction pour détecter le mouvement via le PIR
# def detect_motion():
#     return pir.value() == 1
#
# # Fonction pour lire la luminosité depuis la photodiode
# def read_photodiode():
#     light_value = adc.read()  # Valeur entre 0 et 4095
#     print("Valeur de la photodiode :", light_value)
#
#     red = int((4095 - light_value) * _MAX_INTENSITY / 4095)
#     green = int(light_value * _MAX_INTENSITY / 4095)
#     blue = int((4095 - abs(2048 - light_value)) * _MAX_INTENSITY / 4095)
#     return red, green, blue
#
# # Programme principal
# print("Hello, je suis l'Advertiser BLE pour le PIR et la photodiode")
#
# ble = bluetooth.BLE()
# ble_device = BLE_Adv_Control(ble)
#
# # Initialisation des timers pour les tâches
# blink1 = ticks_ms()  # Timer pour le PIR et le buzzer
# blink2 = ticks_ms()  # Timer pour la luminosité
#
# while True:
#     n = ticks_ms()  # Temps actuel en millisecondes
#
#     # Tâche 1 : Buzzer et PIR
#     if ticks_diff(n, blink1) > 1000:  # Toutes les 1000 ms
#         if detect_motion():
#             message = f"{my_name}|BUZZ|1"
#             print("Mouvement détecté. Envoi :", message)
#         else:
#             message = f"{my_name}|BUZZ|0"
#             print("Pas de mouvement. Envoi :", message)
#         ble_device.advertise(message=message)
#         blink1 = n
#
#     # Tâche 2 : Luminosité
#     if ticks_diff(n, blink2) > 1000:  # Toutes les 1000 ms
#         red, green, blue = read_photodiode()
#         message = f"{my_name}|RGB|{red}|{green}|{blue}"
#         print(f"Luminosité mesurée. Envoi : {message}")
#         ble_device.advertise(message=message)
#         blink2 = n

# Objet du script :
# Connexion d'un module LoRa-E5 à un réseau LoRaWAN privé sur TTN, préalablement configuré.
# Publication de données de température, humidité et pression sur TTN dans un format
# hexadécimal qui devra ensuite être "décodé" par un parser de payloads sur TagoIO.
# Cet exemple a été construit à partir des ressources mises à disposition par
# Vittascience :
# https://github.com/vittascience/stm32-libraries/tree/main/grove_modules

# # Importation des différents pilotes
# import machine
# from stm32_LoRa import *
# from utime import sleep_ms
#
# # Port série de la NUCLEO_WB55
# UART_WB55 = const(2)
#
# # Identifiants sur le réseau LoRaWAN
# devAddr = '42 00 22 AB'
# appEui	= '00 00 00 00 00 00 00 00'
# appKey	= 'BF E1 E7 9E F8 90 48 A7 06 B5 7D 8B 1A 41 59 82'
#
# # Temporisations diverses
# DelayRebootLostConnection = 300  # Exprimé en minutes
# DelayTryJoin = 10  # Exprimé en secondes
# MaxTryJoin = int((DelayRebootLostConnection * 60) / DelayTryJoin)
# DelaySend = 30  # Exprimé en secondes
#
#
# # Fonction de callback chargée de traiter et réagir aux messages envoyés par le serveur
# # LoRaWAN au module LoRa-E5
# def DataReceived(Port=0, DataReceived=b''):
#     print("#### = Data received")
#     print("Data received on PORT: " + str(Port) +
#           ", Size = " + str(len(DataReceived)) +
#           ", Data = " + str([hex(x) for x in list(DataReceived)]))
#
#
# # Initialisation du module LoRa-E5
# loRa = LoRa(9600, UART_WB55, DataReceiveCallback=DataReceived)
#
# # Paramètres d'identification du module pour sa connexion au réseau LoRaWAN
# status = loRa.setIdentify(DevAddr=devAddr, AppEui=appEui, AppKey=appKey)
#
#
# # Affichage des différents paramètres du réseau LoRaWAN
# def PrintLoRaParameters():
#     identify = loRa.getIdentify()
#     if (identify != -1):
#         print("#####################################################################")
#         print("########## INITIALIZE                                        ########")
#         print("#####################################################################")
#         print("LORA_DRIVER_VERSION : " + loRa.getDriverVersion())
#         print("#### " + loRa.getMode() + " ####")
#         print("#### AppKey: " + identify['AppKey'])
#         print("#### DevEUI: " + identify['DevEui'])
#         print("#### AppEUI: " + identify['AppEui'])
#         print("#### DevAddr: " + identify['DevAddr'])
#     else:
#         print("#### = Read identify fail.\nReboot!")
#         sleep_ms(2000)
#         machine.reset()
#     if status == -1:
#         print("#### = Initialize fail.\nReboot!")
#         sleep_ms(2000)
#         machine.reset()
#     else:
#         print("#### = Initialize success.")
#
#
# # Etablissement de la connexion ("join") LoRaWAN
# def JoinNetwork():
#     # Try to join network
#     joinStatus = False
#     tryJoin = 0
#     while joinStatus == False:
#         # Join LoRaWAN
#         print("#### = Try join n°" + str(tryJoin + 1))
#         status = loRa.join()
#         if status == -1:
#             print("#### = Join Fail, retry in " + str(DelayTryJoin) + " seconds.")
#             tryJoin += 1
#             if tryJoin > MaxTryJoin:
#                 # Reboot board
#                 print("Reboot!")
#                 machine.reset()
#                 sleep_ms(DelayTryJoin * 1000)
#         else:
#             joinStatus = True
#             print("#### = Join sucess.")
#
#
# # Emission de trames dans un format hexadécimal contenant les mesures du BME280
# def GetSendData():
#     # Temporisation en millisecondes, fréquence d'émission des trames
#     TEMPO = const(600000)
#
#     from time import sleep_ms  # Pout temporiser
#     from machine import I2C  # Pilote du bus I2C
#
#     # Pause d'une seconde pour laisser à l'I2C le temps de s'initialiser
#     sleep_ms(1000)
#
#
#
#     # Décompte des tentatives d'émission d'une trame
#     trySend = 0
#
#     # Nombres d'octets dans la payload
#     NB_BYTES = const(5)
#
#     # Initialisation d'un tableau de NB_BYTES octets qui contiendra la payload LoRaWAN
#     LoRaPayload = [0x00] * NB_BYTES
#
#     while True:
#
#
#         # Préparation des mesures
#         temp = 28
#         press = 23
#         humi = 20
#
#         # Affichage des mesures
#         print('=' * 40)  # Imprime une ligne de séparation
#         print("Température : %.1f °C" % temp)
#         print("Pression : %d hPa" % press)
#         print("Humidité relative : %d %%" % humi)
#
#         # On convertit les mesures de température, pression et humidité en entiers
#         temp = int(temp * 10)
#         press = int(press * 10)
#         humi = int(humi * 2)
#
#         # Construction de la payload LoRaWAN, on agrège directement les données au format hexadécimal
#
#         # Température, donnée codée sur 16 bits
#         LoRaPayload[0] = (temp >> 8) & 0xFF  # Extraction de l'octet de poids faible
#         LoRaPayload[1] = temp & 0xFF  # Extraction de l'octet de poids fort
#
#         # Pression, donnée codée sur 16 bits
#         LoRaPayload[2] = (press >> 8) & 0xFF  # Extraction de l'octet de poids faible
#         LoRaPayload[3] = press & 0xFF  # Extraction de l'octet de poids fort
#
#         # Humidité, donnée codée sur un seul octet
#         LoRaPayload[4] = humi
#
#         # Emission de la trame LoRaWAN
#
#         print("#### = Send data.")
#         trySend += 1
#         sendStatus = loRa.sendData(LoRaPayload, Port=1, NeedAck=False)
#
#         #  Si l'émission échoue, reessaye trySend fois puis force un reset du STM32WB55
#         if sendStatus == -1:
#             print("#### = Join fail.")
#             if trySend > MaxTrySend:
#                 print("Reset!")
#                 machine.reset()
#         else:
#             print("#### = Send success.")
#             trySend = 0
#
#         # Place le module LoRa-E5 en mode veille
#         # print("#### = LoRa module enter low power mode.")
#         #loRa.enterLowPowerMode()
#         sleep_ms(2000)
#         # Temporisation jusqu'à l'envoi de la prochaine trame
#         # Place le STM32WB55 en mode "sommeil profond"
#         # Le réveil génère un reset.
#         #print("#### = MCU enter low power mode for %d seconds" % (TEMPO / 1000))
#         #machine.deepsleep(TEMPO)  # Impose un reset du script après TEMPO millisecondes
#     # machine.lightsleep(TEMPO) # Le script redémarre à ce point après TEMPO millisecondes
#
#     # Alternative au mode "sommeil" pour ne pas perdre
#     # la connexion au RPL en phase de développement
#     # sleep_ms(TEMPO)
#
#
# # Exécution des fonctions
# PrintLoRaParameters()  # Affichage des paramètres
# JoinNetwork()  # Connexion à TTN
# GetSendData()  # Emission de trames vers TagoIO


################################################################################




from stm32_LoRa import *
from pyb import Pin, ADC
from time import ticks_ms, ticks_diff, sleep_ms
import machine

# Port série de la NUCLEO_WB55
UART_WB55 = const(2)

# Identifiants sur le réseau LoRaWAN
devAddr = '420022AB'
appEui  = '0000000000000000'
appKey  = 'BFE1E79EF89048A706B57D8B1A415982'

# Configuration des capteurs
pir = Pin('D2', Pin.IN)  # Capteur PIR
adc = ADC(Pin('A1'))     # Photodiode connectée à A1

# Configuration LoRa-E5
loRa = LoRa(9600, UART_WB55)

# Initialisation des identifiants LoRaWAN
status = loRa.setIdentify(DevAddr=devAddr, AppEui=appEui, AppKey=appKey)

# Paramètres d'envoi
NB_BYTES = const(6)  # Taille de la payload (2 octets pour chaque capteur)
LoRaPayload = [0x00] * NB_BYTES  # Initialisation de la payload


# Affichage des différents paramètres du réseau LoRaWAN
def PrintLoRaParameters():
    identify = loRa.getIdentify()
    if (identify != -1):
        print("#####################################################################")
        print("########## INITIALIZE                                        ########")
        print("#####################################################################")
        print("LORA_DRIVER_VERSION : " + loRa.getDriverVersion())
        print("#### " + loRa.getMode() + " ####")
        print("#### AppKey: " + identify['AppKey'])
        print("#### DevEUI: " + identify['DevEui'])
        print("#### AppEUI: " + identify['AppEui'])
        print("#### DevAddr: " + identify['DevAddr'])
    else:
        print("#### = Read identify fail.\nReboot!")
        sleep_ms(2000)
        machine.reset()
    if status == -1:
        print("#### = Initialize fail.\nReboot!")
        sleep_ms(2000)
        machine.reset()
    else:
        print("#### = Initialize success.")

# Etablissement de la connexion ("join") LoRaWAN
def JoinNetwork():
    joinStatus = False
    tryJoin = 0
    while joinStatus == False:
        print("#### = Try join n°" + str(tryJoin + 1))
        status = loRa.join()
        if status == -1:
            print("#### = Join Fail, retry in " + str(DelayTryJoin) + " seconds.")
            tryJoin += 1
            if tryJoin > MaxTryJoin:
                print("#### = Too many attempts. Resetting...")
                machine.reset()
            sleep_ms(DelayTryJoin * 1000)
        else:
            joinStatus = True
            print("#### = Join success.")

def detect_motion():
    """Retourne 1 si un mouvement est détecté par le PIR, sinon 0."""
    return pir.value()

def read_photodiode():
    """Lit la valeur de la photodiode et calcule des valeurs RGB."""
    light_value = adc.read()  # Valeur brute de 0 à 4095
    red = int((4095 - light_value) * 255 / 4095)
    green = int(light_value * 255 / 4095)
    blue = int((4095 - abs(2048 - light_value)) * 255 / 4095)
    light_value_pct = (light_value*100)/4095
    return light_value_pct,red, green, blue

def GetSendData():
    """Lecture des capteurs et envoi des données via LoRa."""
    trySend = 0

    while True:
        # Lecture des capteurs
        motion = detect_motion()  # 1 si mouvement, 0 sinon
        light_value, red, green, blue = read_photodiode()  # Valeurs RGB de la photodiode

        # Construction de la payload LoRaWAN
        LoRaPayload[0] = motion  # PIR : 1 octet
        LoRaPayload[1] = 0x00    # Octet inutilisé pour alignement

        LoRaPayload[2] = int(light_value)
        # Affichage des mesures pour validation
        print('=' * 40)
        print(f"Mouvement détecté : {motion}")
        print(f"Luminosité détectée : {light_value}")
        print(f"Photodiode - Rouge : {red}, Vert : {green}, Bleu : {blue}")

        # Envoi des données via LoRaWAN
        print("#### = Send data.")
        sendStatus = loRa.sendData(LoRaPayload, Port=1, NeedAck=False)

        if sendStatus == -1:
            print("#### = Send fail. Retrying...")
            trySend += 1
            if trySend > 5:  # Si trop d'échecs, redémarre la carte
                print("#### = Too many failures. Resetting...")
                machine.reset()
        else:
            print("#### = Send success.")
            trySend = 0  # Réinitialise le compteur d'échecs

        # Temporisation avant la prochaine lecture et envoi
        sleep_ms(2000)

# Exécution des fonctions
print("#### Initialisation du réseau LoRaWAN...")
PrintLoRaParameters()
JoinNetwork()
GetSendData()
