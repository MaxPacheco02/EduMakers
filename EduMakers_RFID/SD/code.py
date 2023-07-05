'''
This code plays a track depending on the approached object and has some user controls as well.

When the tag is read:
    a) Reads the info of the RFID tag and the langage selected
    b) Plays the folder and track selected (E. 1,1)
    c) An LED output shows when another tag can be read
    d) User can Pause/Play the track with the button
    e) User can also control the Volume with a potentiometer
'''

# External libraries
from DFPlayer import DFPlayer
from adafruit_pn532.i2c import PN532_I2C

# Internal  libraries
import board
import busio
import time
import digitalio
from digitalio import DigitalInOut
from analogio import AnalogIn

def map_range(s):  # The number to map.
    a1 = 0  # The lower bound of the value’s input range.
    a2 = 65535  # The upper bound of the value’s input range.
    b1 = 100  # The lower bound of the value’s target range.
    b2 = 0  # The upper bound of the value’s target range.
    # NOTE: The mapping is inverted due to the potentiometer's polarity.
    return round(b1 + ((s - a1) * (b2 - b1) / (a2 - a1)))


# MuonCode      MuonPIN/LED
# board.D16  -    PIN 21
# LED ON = the device can read a new TAG
# LED OFF = the device won't read TAG's
led = DigitalInOut(board.D16)
led.direction = digitalio.Direction.OUTPUT

# DFplayer Mini Reproductor MP3-TF-16P MH2024K-16SS
# MuonCode   MuonPIN  DFPlayer
# board.D8 - PIN 11 -   RX
# board.D9 - PIN 12 -   TX
#             GND   -   GND
#             VCC   -   VCC  (5V)
u = busio.UART(board.D8, board.D9, baudrate=9600)
player = DFPlayer(uart=u, volume=20)

# PN532 Módulo RFID NFC Lectura y Escritura V3
# MuonCode   MuonPIN    NFC
# board.D25 - PIN 34 -  SCL
# board.D24 - PIN 32 -  SDA
# board.D23 - PIN 31 -  RSTO
# board.D22 - PIN 29 -  IRQ
#              GND   -  GND
#              VCC   -  VCC  (5V)
i2c = busio.I2C(board.D25, board.D24)
reset_pin = DigitalInOut(board.D23)
irq_pin = DigitalInOut(board.D22)
pn532 = PN532_I2C(i2c, debug=False, reset=reset_pin, irq=irq_pin)
ic, ver, rev, support = pn532.firmware_version
print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))
pn532.SAM_configuration()

# MuonCode   MuonPIN   10k 3Pin Potentiometer
#              GND      -  GND
# board.A18 - PIN 24    -  Vol 0 to 65,525 16 bits
#              VCC      -  VCC  (3.3V)
potentiometer = AnalogIn(board.A18)

# MuonCode      MuonPIN     Dip Switch 4 (0 to 1)
# board.D21      PIN27          Dip1      1000
# board.D20      PIN26          Dip2      0100
# board.D19      PIN25          Dip3      0010
# board.D17      PIN22          Dip4      0001
dipswitch1 = DigitalInOut(board.D21)
dipswitch2 = DigitalInOut(board.D20)
dipswitch3 = DigitalInOut(board.D19)
dipswitch4 = DigitalInOut(board.D17)
dipswitch1.switch_to_input(pull=digitalio.Pull.UP)
dipswitch2.switch_to_input(pull=digitalio.Pull.UP)
dipswitch3.switch_to_input(pull=digitalio.Pull.UP)
dipswitch4.switch_to_input(pull=digitalio.Pull.UP)

time.sleep(0.5)
player.set_volume(50)
player.play(5, 1) # Whenever the device is rebooted, play the 'welcome' track
print("Sleeping for 1 second Before start")
time.sleep(1)

'''
Esta es la función principal. Es un loop infinito que en cada iteración lee por
la tarjeta del RFID; si se encuentra la señal de algún tag, se reproduce su audio
vinculado y posteriormente se apaga el LED de status por 5 segundos, lo que indica
que no se podrá leer otro tag hasta que pase ese tiempo.
'''
def main_loop(player=player):
    print("Waiting for NFC tag to start playing music")
    volPrevio = 30
    while True:
        track, volPrevio = read_nfc(volPrevio)
        lang = language()
        if track is not None:
            #           ↓ TODO: Replace with language() if the dipswitchswitch is used
            player.play(lang, track)
            print("Sleeping for 5 seconds")
            led.value = False
            time.sleep(5)
        else:
            print(f"Not working bc track is: {track}")

'''
# Estas funciones no se usan
def write_to_nfc():
    print("Waiting for RFID/NFC card to write to!")
    while True:
        uid = pn532.read_passive_target(timeout=0.5)
        print(".", end="")
        if uid is not None:
            break
    print(f"\nFound card with UID: {[hex(i) for i in uid]}")
    # You have to put the Number in Hexadecimal  ↓
    pn532.ntag2xx_write_block(2, b"\x00\x00\x00\x01")
    print("The number has been writen")


def write_to_nfc_loop():
    print("LOOP: Waiting for RFID/NFC card to write to!")
    while True:
        uid = pn532.read_passive_target(timeout=0.5)
        print(".", end="")
        if uid is not None:
            print(f"\nFound card with UID: {[hex(i) for i in uid]}")
            # You have to put the Number in Hexadecimal  ↓
            pn532.ntag2xx_write_block(2, b"\x00\x00\x00\x01")
            print("The number has been writen")
            time.sleep(1)

def read_nfc_loop():
    print("LOOP: Waiting for RFID/NFC card to read!")
    while True:
        uid = pn532.read_passive_target(timeout=0.5)
        print(".", end="")
        if uid is not None:
            print(f"\nFound card with UID: {[hex(i) for i in uid]}")
            print("Reading Page {4} ...")
            data = pn532.ntag2xx_read_block(4)  # .decode("utf-8")  # utf-8
            data = int.from_bytes(data, "big")
            print("Read that data:", data)
            time.sleep(1)
'''

'''
Esta función se usa para leer las señales de la tarjeta de RFID. Primero, mientras no
se haya detectado algún TAG, constantemente lee el volumen y el LED de status permanece
prendido. En cuanto lo detecta, retorna el valor leído.
'''
def read_nfc(volPrevio):
    print("Waiting for RFID/NFC card to read!")
    while True:
        volPrevio = volume(volPrevio)
        led.value = True
        uid = pn532.read_passive_target(timeout=0.5)
        print(".", end="")
        print(dipswitch1.value)
        if uid is not None:
            break
    print(f"\nFound card with UID: {[hex(i) for i in uid]}")
    print(f"Reading Page {4} ...")
    data = pn532.ntag2xx_read_block(4)
    # print(str(data))
    if data is not None:
        data = int.from_bytes(data, "big")
        print(f"The number readed is: {data}")
    return data, volPrevio

'''
Esta función mapea los valores leídos del potenciómetro a un volumen en porcentaje.
'''
def volume(volPrevio):
    volActual = map_range(potentiometer.value)
    if volPrevio != volActual:
        player.set_volume(volActual)
        volPrevio = volActual
        # print(f"Volume is changing: {volPrevio}")
    time.sleep(0.05)  # Needed if not program crash
    return volPrevio

'''
Esta función detecta el estado del dipswitch de lenguaje y lo modifica dependiendo de
la entrada.
'''
def language():
    idioma = 0
    dipswitch = [dipswitch1.value^1, dipswitch2.value^1, dipswitch3.value^1, dipswitch4.value^1]
    dipstring = ''.join(str(int(x)) for x in dipswitch)
    if dipstring == '0010':
        print("You are in Spanish Maps")
        idioma = 2  # Se refiere a la carpeta
    elif dipstring == '0011':  # 1110
        print("You are in English Human Body")
        idioma = 3
    elif dipstring == '0100':  # 1101
        print("You are in Spanish Human Body")
        idioma = 4
    return idioma


# Explicar que es esto
#write_to_nfc_loop()
#write_to_nfc()
# read_nfc_loop()
# read_nfc()
main_loop()
# language()