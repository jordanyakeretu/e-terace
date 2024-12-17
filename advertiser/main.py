from stm32_LoRa import *
from pyb import Pin, ADC
from time import ticks_ms, ticks_diff, sleep_ms
import machine
import bluetooth
from ble_advertising import advertising_payload
import dht

# Port série de la NUCLEO_WB55
UART_WB55 = const(2)

# Identifiants sur le réseau LoRaWAN
devAddr = '420022AB'
appEui  = '0000000000000000'
appKey  = 'BFE1E79EF89048A706B57D8B1A415982'

# Configuration des capteurs
pir = Pin('D2', Pin.IN)  # Capteur PIR
adc = ADC(Pin('A1'))     # Photodiode connectée à A1
sensor = dht.DHT22('D4')# initiation capteur température humidity

# Configuration LoRa-E5
loRa = LoRa(9600, UART_WB55)

# Initialisation des identifiants LoRaWAN
status = loRa.setIdentify(DevAddr=devAddr, AppEui=appEui, AppKey=appKey)

# Paramètres d'envoi LoRa
NB_BYTES = const(6)  # Taille de la payload (2 octets pour chaque capteur)
LoRaPayload = [0x00] * NB_BYTES  # Initialisation de la payload

# Paramètres Bluetooth
my_name = "PIRAdv"  # Nom de l'advertiser BLE
_ADV_APPEARANCE_GENERIC_TAG = const(512)

# Initialisation du BLE
class BLE_Adv_Control:
    def __init__(self, ble):
        self._ble = ble
        self._ble.active(True)

    def advertise(self, interval_us=500000, message=None):
        self._payload = advertising_payload(name=message, appearance=_ADV_APPEARANCE_GENERIC_TAG)
        self._ble.gap_advertise(interval_us, adv_data=self._payload, connectable=False)

ble = bluetooth.BLE()
ble_device = BLE_Adv_Control(ble)

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
            print("#### = Join Fail, retry in 10 seconds.")
            tryJoin += 1
            if tryJoin > 5:
                print("#### = Too many attempts. Resetting...")
                machine.reset()
            sleep_ms(10000)
        else:
            joinStatus = True
            print("#### = Join success.")

def detect_motion():
    """Retourne 1 si un mouvement est détecté par le PIR, sinon 0."""
    return pir.value()

def read_photodiode():
    """Lit la valeur de la photodiode et calcule des valeurs RGB."""
    light_value = adc.read()  # Valeur brute de 0 à 4095
    light_value_pct = (light_value * 100) / 4095
    red = int((255 * light_value) / 4095)
    green = int((255 * light_value) / 4095)
    blue = int((255 * light_value) / 4095)
    return light_value_pct, red, green, blue

def GetSendData():
    """Lecture des capteurs et envoi des données via LoRa et BLE."""
    blink1 = ticks_ms()  # Timer pour luminosity
    blink2 = ticks_ms()  # Timer pour motion

    while True:
        n = ticks_ms()

        # Tâche 1 : Luminosity
        if ticks_diff(n, blink1) > 1500:
            light_value, red, green, blue = read_photodiode()
            motion = detect_motion()
            # On mesure et on lit les résultats
            sensor.measure()
            temp = sensor.temperature()
            humi = sensor.humidity()

            # Construction de la payload LoRaWAN pour motion
            LoRaPayload[0] = motion
            LoRaPayload[1] = 0x00  # Octet inutilisé
            # Construction de la payload LoRaWAN pour luminosity
            LoRaPayload[2] = int(light_value)  # Luminosité en pourcentage
            LoRaPayload[3] = int(temp)
            LoRaPayload[4] = int(humi)

            # Affichage des mesures
            print("#### Motion Task")
            print(f"Mouvement détecté : {motion}")
            # Affichage des mesures
            print("#### Luminosity Task")
            print(f"Luminosité détectée : {light_value}%")
            print(f"Photodiode - Rouge : {red}, Vert : {green}, Bleu : {blue}")
            print("Température : " + str(temp) + " °C")
            print("Humidité relative : " + str(humi) + " %")

            # Envoi des données via LoRa
            print("#### = Send luminosity data via LoRa.")
            sendStatus = loRa.sendData(LoRaPayload, Port=1, NeedAck=False)
            if sendStatus == -1:
                print("#### = Send fail via LoRa.")
            else:
                print("#### = Send success via LoRa.")

            # Envoi des données via BLE
            message_ble = f"{my_name}|{motion}|{red}|{green}|{blue}"
            print("#### = Send data via BLE: ", message_ble)
            ble_device.advertise(message=message_ble)
            print("#### = Sent via BLE.")

            blink1 = n  # Mise à jour du timer

        # # Tâche 2 : Motion
        # if ticks_diff(n, blink2) > 100000:
        #     motion = detect_motion()
        #
        #     # Construction de la payload LoRaWAN pour motion
        #     LoRaPayload[0] = motion
        #     LoRaPayload[1] = 0x00  # Octet inutilisé
        #
        #     # Affichage des mesures
        #     print("#### Motion Task")
        #     print(f"Mouvement détecté : {motion}")
        #
        #     # Envoi des données via LoRa
        #     print("#### = Send motion data via LoRa.")
        #     sendStatus = loRa.sendData(LoRaPayload, Port=1, NeedAck=False)
        #     if sendStatus == -1:
        #         print("#### = Send fail via LoRa.")
        #     else:
        #         print("#### = Send success via LoRa.")
        #
        #     # Envoi des données via BLE
        #     message_motion = f"{my_name}|BUZZ|{motion}"
        #     print("#### = Send motion data via BLE: ", message_motion)
        #     ble_device.advertise(message=message_motion)
        #     print("#### = Sent via BLE.")
        #     blink2 = n  # Mise à jour du timer

# Exécution des fonctions
print("#### Initialisation du réseau LoRaWAN...")
PrintLoRaParameters()
JoinNetwork()
GetSendData()


# from stm32_LoRa import *
# from pyb import Pin, ADC
# from time import ticks_ms, ticks_diff, sleep_ms
#
# # Paramètres LoRaWAN
# devAddr = '420022AB'
# appEui  = '0000000000000000'
# appKey  = 'BFE1E79EF89048A706B57D8B1A415982'
#
# # Configuration LoRa-E5 avec callback
# def on_data_received(Port, DataReceived):
#     """Fonction callback pour gérer les données reçues (downlink)."""
#     print("#### Données LoRa downlink reçues ####")
#     print(f"Port : {Port}")
#     print(f"Données : {DataReceived}")
#
# # Initialisation du module LoRa
# loRa = LoRa(Baudrate=9600, UartId=2, DataReceiveCallback=on_data_received)
#
# # Configuration des identifiants
# status = loRa.setIdentify(DevAddr=devAddr, AppEui=appEui, AppKey=appKey)
#
# # Fonction pour rejoindre le réseau LoRa
# def JoinNetwork():
#     print("#### Tentative de connexion LoRaWAN...")
#     while loRa.join() == -1:
#         print("Échec de la connexion. Nouvelle tentative dans 5s...")
#         sleep_ms(5000)
#     print("Connexion réussie au réseau LoRaWAN.")
#
# # Fonction pour envoyer des données
# def SendDataLoRa():
#     payload = [0x01, 0x02, 0x03, 0x04]  # Exemple de payload
#     print("#### Envoi des données via LoRa...")
#     result = loRa.sendData(payload, Port=1, NeedAck=True)  # Port=1 et avec ACK
#     if result == 0:
#         print("Envoi réussi. Attente du downlink...")
#     else:
#         print("Échec de l'envoi.")
#
# # Programme principal
# def main():
#     JoinNetwork()
#     while True:
#         SendDataLoRa()
#         sleep_ms(10000)  # Pause avant le prochain envoi
#
# if __name__ == "__main__":
#     main()

