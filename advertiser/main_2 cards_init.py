# Exemple de mise en œuvre d'une NUCLEO-WB55 en mode scanner BLE à l'écoute de trames provenant
# d'autres cartes NUCLEO-WB55 en mode advertising.
# Le scanner capture toutes les dix secondes les trames d'advertising dont le nom commence par "Adv".
# Il affiche également les données de température et d'humidité envoyées sous forme de texte
# dans le nom des trames d'advertising.

import bluetooth  # Bibliothèque pour gérer le BLE
from time import sleep_ms  # Méthode pour générer des temporisations en millisecondes
from ble_advertising import decode_services, decode_name  # Méthodes pour décoder le contenu des trames d'advertising

# Constantes utilisées pour GAP (voir https://docs.MicroPython.org/en/latest/library/ubluetooth.html)
_IRQ_SCAN_RESULT = const(5)  # Le scan signale une trame d'advertising
_IRQ_SCAN_DONE = const(6)  # Le scan a pris fin

# Notifications "advertising" des objets qui ne sont pas connectables
_ADV_SCAN_IND = const(0x02)
_ADV_NONCONN_IND = const(0x03)

# Paramètres pour fixer le rapport cyclique du scan
_SCAN_DURATION_MS = const(1000)
_SCAN_INTERVAL_US = const(10000)
_SCAN_WINDOW_US = const(10000)


# Classe pour créer un scanner BLE environnemental
class BLE_Scan_Env:

    # Initialisations
    def __init__(self, ble):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._reset()

    # Effacement des données en mémoire cache
    def _reset(self):
        # Noms et adresses mises en mémoire cache après une étape de scan des périphériques
        self._message = set()
        # Callback du scan d'advertising
        self._scan_callback = None

    # Gestion des évènements
    def _irq(self, event, data):
        # Le scan des périphériques a permis d'identifier au moins un advertiser
        if event == _IRQ_SCAN_RESULT:
            # Lecture du contenu de la trame d'advertising
            addr_type, addr, adv_type, rssi, adv_data = data

            # Si la trame d'advertising précise que son émetteur n'est pas connectable
            if adv_type in (_ADV_SCAN_IND, _ADV_NONCONN_IND):
                # Le message est contenu dans le champ "name" de la trame d'advertising
                smessage = decode_name(adv_data)
                # Si le message commence par "Adv", enregistre le dans un "set".
                # (pour éviter d'enregistrer plusieurs fois le même message pendant le scan)
                if smessage[0:3] == "Adv":
                    self._message.add(smessage)

        # Lorsque le scan a pris fin (après _SCAN_DURATION_MS)
        elif event == _IRQ_SCAN_DONE:
            if self._scan_callback:  # Si un callback relatif à cet évènement a été assigné
                if len(self._message) > 0:
                    # Si au moins un message a été enregistré pendant le scan, appelle le callback pour afficher
                    self._scan_callback(self._message)
                    # Désactive le callback
                    self._scan_callback = None

    # Procède au scan
    def scan(self, callback=None):
        # Initialise (vide) le set qui va contenir les messages
        self._message = set()
        # Assigne le callback qui sera appelé en fin de scan
        self._scan_callback = callback
        # Scanne pendant _SCAN_DURATION_MS, pendant des durées de _SCAN_WINDOWS_US espacées de _SCAN_INTERVAL_US
        self._ble.gap_scan(_SCAN_DURATION_MS, _SCAN_INTERVAL_US, _SCAN_WINDOW_US)


# Programme principal

print("Hello, je suis Scanny")

# Instanciation du BLE
ble = bluetooth.BLE()
scanner = BLE_Scan_Env(ble)


# Fonction "callback" appelée à la fin du scan
def on_scan(message):
    # Pour chaque message d'advertising enregistré
    for payload in message:
        # On sépare les mesures grâce à l'instruction split
        device, temp, humi = payload.split("|")
        print("Message de " + device + " :")
        print(" - Température : " + temp + "°C")
        print(" - Humidité : " + humi + "%")


while True:
    # Lance le scan des trames d'advertising
    scanner.scan(callback=on_scan)

    # Temporisation de dix secondes
    sleep_ms(10000)