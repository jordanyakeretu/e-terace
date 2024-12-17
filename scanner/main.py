# import bluetooth
# from pyb import Pin, Timer
# import neopixel
# from time import ticks_ms, ticks_diff, sleep_ms
# from ble_advertising import decode_name
#
# # Constantes pour le BLE
# _IRQ_SCAN_RESULT = const(5)
# _IRQ_SCAN_DONE = const(6)
# _SCAN_DURATION_MS = const(1000)
# _SCAN_INTERVAL_US = const(10000)
# _SCAN_WINDOW_US = const(10000)
#
# # Configuration du buzzer
# buzzer_pin = Pin('D6')
# buzzer_timer = Timer(1, freq=2000)  # Timer pour le PWM
# buzzer_channel = buzzer_timer.channel(1, Timer.PWM, pin=buzzer_pin)
#
# # Configuration de la LED RGB (Neopixel)
# _NB_LED = 1  # Nombre de LEDs
# np = neopixel.NeoPixel(Pin('D2'), _NB_LED)
#
# class BLE_Scan_Control:
#     def __init__(self, ble):
#         self._ble = ble
#         self._ble.active(True)
#         self._ble.irq(self._irq)
#         self._message = set()
#
#     def _irq(self, event, data):
#         if event == _IRQ_SCAN_RESULT:
#             addr_type, addr, adv_type, rssi, adv_data = data
#             smessage = decode_name(adv_data)
#             if smessage and smessage.startswith("PIRAdv"):
#                 self._message.add(smessage)
#         elif event == _IRQ_SCAN_DONE:
#             if self._message:
#                 self.handle_message(self._message)
#                 self._message = set()
#
#     def handle_message(self, messages):
#         for message in messages:
#             print("Message reçu :", message)
#             parts = message.split("|")
#             if "BUZZ" in parts:
#                 _, _, state = parts
#                 self.control_buzzer(state)
#             elif "RGB" in parts:
#                 _, _, red, green, blue = parts
#                 self.control_led(int(red), int(green), int(blue))
#
#     def control_buzzer(self, state):
#         state = int(state)
#         if state == 1:
#             print("Activation du buzzer")
#             buzzer_channel.pulse_width_percent(50)
#         else:
#             print("Désactivation du buzzer")
#             buzzer_channel.pulse_width_percent(0)
#
#     def control_led(self, red, green, blue):
#         print(f"Régler LED RGB - Rouge: {red}, Vert: {green}, Bleu: {blue}")
#         for i in range(_NB_LED):
#             np[i] = (red, green, blue)
#         np.write()
#
#     def scan(self):
#         self._ble.gap_scan(_SCAN_DURATION_MS, _SCAN_INTERVAL_US, _SCAN_WINDOW_US)
#
# # Programme principal
# print("Hello, je suis le Scanner BLE pour le PIR et la LED RGB")
#
# # Initialisation du BLE
# ble = bluetooth.BLE()
# scanner = BLE_Scan_Control(ble)
#
# while True:
#     # Lancer le scan
#     scanner.scan()
#     # Temporisation de 10 secondes entre les scans
#     sleep_ms(1000)

############################################################################### SCAN OK


import bluetooth
from pyb import Pin, Timer
import neopixel
from time import ticks_ms, ticks_diff, sleep_ms
from ble_advertising import decode_name
from stm32_rgb_led_matrix_ import GroveTwoRGBLedMatrix

# --- Initialisation de la matrice RGB LED ---
i2c = machine.I2C(1)  # Configuration du bus I2C
RGBmatrix = GroveTwoRGBLedMatrix(i2c=i2c)  # Instance de la matrice LED


# Constantes pour le BLE
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_SCAN_DURATION_MS = const(1000)
_SCAN_INTERVAL_US = const(10000)
_SCAN_WINDOW_US = const(10000)
SCAN_TIMEOUT_MS = 10000  # Temps d'attente pour afficher KO (10 secondes)

# Configuration du buzzer
buzzer_pin = Pin('D6')
buzzer_timer = Timer(1, freq=2000)  # Timer pour le PWM
buzzer_channel = buzzer_timer.channel(1, Timer.PWM, pin=buzzer_pin)

# Configuration de la LED RGB (Neopixel)
_NB_LED = 1  # Nombre de LEDs
np = neopixel.NeoPixel(Pin('D2'), _NB_LED)

class BLE_Scan_Control:
    def __init__(self, ble):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._message = set()
        self._scan_in_progress = False  # Drapeau pour suivre l'état du scan

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            smessage = decode_name(adv_data)
            if smessage and smessage.startswith("PIRAdv"):
                self._message.add(smessage)
        elif event == _IRQ_SCAN_DONE:
            self._scan_in_progress = False  # Scan terminé
            if self._message:
                self.handle_message(self._message)
                self._message = set()

    def handle_message(self, messages):
        global last_received_time
        last_received_time=ticks_ms()
        for message in messages:
            print("Message reçu :", message)
            parts = message.split("|")
            #if "BUZZ" in parts and "RGB" in parts:
            _, state, red, green, blue = parts
            self.control_buzzer(state)
            self.control_led(int(red), int(green), int(blue))

    def control_buzzer(self, state):
        state = int(state)
        if state == 1:
            print("Activation du buzzer")
            buzzer_channel.pulse_width_percent(50)
        else:
            print("Désactivation du buzzer")
            buzzer_channel.pulse_width_percent(0)

    def control_led(self, red, green, blue):
        print(f"Régler LED RGB - Rouge: {red}, Vert: {green}, Bleu: {blue}")
        for i in range(_NB_LED):
            np[i] = (red, green, blue)
        np.write()

    def scan(self):
        if not self._scan_in_progress:  # Lancer un nouveau scan seulement si aucun en cours
            self._scan_in_progress = True
            self._ble.gap_scan(_SCAN_DURATION_MS, _SCAN_INTERVAL_US, _SCAN_WINDOW_US)
        else:
            print("Un scan est déjà en cours, attente avant le prochain.")

# Programme principal
print("Hello, je suis le Scanner BLE pour le PIR et la LED RGB")

last_received_time = ticks_ms()  # Dernière réception de trame BLE
# Initialisation du BLE
ble = bluetooth.BLE()
scanner = BLE_Scan_Control(ble)


def display_ascii_string(RGBmatrix, text, duration, forever, color):
    """Convertit une chaîne en valeurs ASCII et l'affiche sur la matrice."""
    ascii_data = [ord(c) for c in text]  # Convertit chaque caractère en ASCII
    RGBmatrix.displayString(ascii_data, duration, forever, color)

while True:
    # Lancer le scan
    print("Scan")
    scanner.scan()
    # Vérifier si aucune trame BLE n'a été reçue pendant 10 secondes
    if ticks_diff(ticks_ms(), last_received_time) > SCAN_TIMEOUT_MS:
        display_ascii_string(RGBmatrix, "KO", 1000, True, 0x00)  # Affiche "KO" en rouge
    else:
        display_ascii_string(RGBmatrix, "OK", 1000, True, 0x52)  # Affiche "OK" en vert
    # Temporisation pour permettre le traitement des messages entre les scans
    sleep_ms(2000)

################################################################
#
# import machine
# import bluetooth
# from pyb import Pin, Timer
# from time import ticks_ms, ticks_diff, sleep_ms
# from ble_advertising import decode_name
# from stm32_rgb_led_matrix_ import GroveTwoRGBLedMatrix
#
# # --- Initialisation de la matrice RGB LED ---
# i2c = machine.I2C(1)  # Configuration du bus I2C
# RGBmatrix = GroveTwoRGBLedMatrix(i2c=i2c)  # Instance de la matrice LED
#
# # --- Constantes BLE ---
# _IRQ_SCAN_RESULT = const(5)
# _IRQ_SCAN_DONE = const(6)
# _SCAN_DURATION_MS = const(1000)  # Durée d'un scan BLE
# _SCAN_INTERVAL_US = const(10000)
# _SCAN_WINDOW_US = const(10000)
# SCAN_TIMEOUT_MS = 10000  # Temps d'attente pour afficher KO (10 secondes)
#
# # --- Variables Globales ---
# ble = bluetooth.BLE()
# last_received_time = ticks_ms()  # Dernière réception de trame BLE
#
#
# class BLE_Scan_Control:
#     def __init__(self, ble):
#         self._ble = ble
#         self._ble.active(True)
#         self._ble.irq(self._irq)
#         self._message = set()
#         self._scan_in_progress = False
#
#     def _irq(self, event, data):
#         global last_received_time
#         if event == _IRQ_SCAN_RESULT:
#             addr_type, addr, adv_type, rssi, adv_data = data
#             smessage = decode_name(adv_data)
#             if smessage and smessage.startswith("PIRAdv"):
#                 self._message.add(smessage)
#                 last_received_time = ticks_ms()  # Mise à jour du temps
#         elif event == _IRQ_SCAN_DONE:
#             self._scan_in_progress = False
#             if self._message:
#                 self.handle_message(self._message)
#                 self._message = set()
#
#     def handle_message(self, messages):
#         for message in messages:
#             print("Message reçu :", message)
#             parts = message.split("|")
#             _, state, red, green, blue = parts
#             RGBmatrix.displayString("OK", 1000, True, 0x52)  # Affiche "OK" en vert
#
#     def scan(self):
#         if not self._scan_in_progress:
#             self._scan_in_progress = True
#             self._ble.gap_scan(_SCAN_DURATION_MS, _SCAN_INTERVAL_US, _SCAN_WINDOW_US)
#
#
# def display_ascii_string(RGBmatrix, text, duration, forever, color):
#     """Convertit une chaîne en valeurs ASCII et l'affiche sur la matrice."""
#     ascii_data = [ord(c) for c in text]  # Convertit chaque caractère en ASCII
#     RGBmatrix.displayString(ascii_data, duration, forever, color)
#
#
# # --- Programme principal ---
# scanner = BLE_Scan_Control(ble)
# print("Initialisation du Scanner BLE et de la matrice LED")
#
# while True:
#     # Lancer un scan BLE
#     scanner.scan()
#     print("Scan en cours...")
#
#     # Vérifier si aucune trame BLE n'a été reçue pendant 10 secondes
#     if ticks_diff(ticks_ms(), last_received_time) > SCAN_TIMEOUT_MS:
#         display_ascii_string(RGBmatrix, "KO", 1000, True, 0x00)  # Affiche "KO" en rouge
#     else:
#         display_ascii_string(RGBmatrix, "OK", 1000, True, 0x52)  # Affiche "OK" en vert
#
#     sleep_ms(2000)  # Pause entre chaque scan
