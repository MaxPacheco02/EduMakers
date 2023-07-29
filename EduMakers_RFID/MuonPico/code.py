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

# Global Variables
last_press = [0,0,0]    # List with the last 3 recorded times of button presses.
last_track = None # In case of reboot, we must know which track was played last.
folders = 3 # Know the number of extra folders included so the program iterates between them.

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
# board.D20      PIN26          Dip2      0100
# board.D19      PIN25          Dip3      0010
# board.D17      PIN22          Dip4      0001
pause_button = DigitalInOut(board.D17)
killswitch = DigitalInOut(board.D19)
pause_button.switch_to_input(pull=digitalio.Pull.UP)
killswitch.switch_to_input(pull=digitalio.Pull.UP)

# Functions

'''
This is the main function. It's an infinite loop which in every iteration reads
the RFID card; if a TAG from an object is found, it plays its code-related audio
and turns off the status LED for 3 seconds, indicating the reading service is 
temporarily unavailable.
'''
def main_loop(player=player):
    global last_track
    new_audio=0
    index = 0

    time.sleep(0.5)
    player.set_volume(50)
    player.play(0,0) # Whenever the device is rebooted, play the 'welcome' track
    print("Sleeping for 1.8 seconds Before start")
    time.sleep(1.8)
    print("Waiting for NFC tag to start playing music")
    volPrevio = 30

    player.play(0,index%folders+1) # Play the title of the current folder reading the audios
    while True:
        track, volPrevio, reboot, index, changed_lang = read_nfc(volPrevio, new_audio, index) # Read the NFC tag, or a command like reboot or language change
        if changed_lang:
            player.play(0,index%folders+1) # Play the title of the new folder selected
            new_audio = time.localtime().tm_sec+time.localtime().tm_min*60 # Set new playing time
            last_track = None # Erase current reading track to avoid triggering audios with a reboot command until a new tag is read
        elif track is not None:
            if led.value or reboot: # Check if playing service is available
                player.play(range(folders)[index%folders]+1, track)
                print("Playing audio... wait at least 3 seconds to track other objects")
                led.value = False # Disable the reading service (for 3 seconds)
                new_audio = time.localtime().tm_sec+time.localtime().tm_min*60 # New audio playing time, to enable pause button after 1 second
        else:
            print(f"Not working bc track is: {track}")

'''
# Not used functions
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
This function reads the RFID card. While no TAG is detected, it keeps reading the
volume and the language selected, and the status LED remains on until an object is 
read. If the audio is rebooted, it sends the data of the previously received tag to
be played again, which occurs when the pause/play button is presssed rapidly 3 times.
'''
def read_nfc(volPrevio, new_audio, index):
    global last_track, last_press
    pause = False # Variable to instruct if player should pause or not
    last_state = 0 # The last/previous state of the pause button in the current loop iteration
    been_on = False # Know if the button has been kept pressed
    played = False # Know if the audio is playing
    pause_released = False # Variable that validates the pause button has been released, to avoid the title announcement being interrupted
    print("Waiting for RFID/NFC card to read!")
    while True:
        if killswitch.value ^ 1: # The system can only work if the switch is on.
            volPrevio = volume(volPrevio) # Configure player volume
            if pause_button.value:
                pause_released = True # If the pause button has been released at least once, everything can now start working.
            if timer(new_audio, 1) and pause_released: # Enable button funcionality until 1 secon after the audio has started playing
                but = pause_button.value ^ 1
                if but and not last_state: # If the button is pressed and it wasn't...
                    pause = not pause # Iterate pause command
                    last_press[2] = last_press[1] # Shift list values to have the 3 most recent times
                    last_press[1] = last_press[0]
                    last_press[0] = time.localtime().tm_sec+time.localtime().tm_min*60
                    if last_track is not None and last_press[0] - last_press[2] < 2: # If there's been 3 presses in less than 2 seconds...
                        print("Reboot")
                        return last_track, volPrevio, True, index, False

                if last_state != but: # If the last state recorded of the button is not updated...
                    been_on = True # Since this moment, the button has been pressed
                    last_state = but # Update it
                
                been_on *= bool(last_state) # Keep updating the variable in case the state changes to False
                if been_on and timer(last_press[0], 2): # If the button has been pressed for 2 seconds...
                    print("Changing to the next Folder")
                    return last_track, volPrevio, False, index+1, True

            if pause: #If the pause command is True...
                player.pause()
                played = False
            elif not played and last_track is not None: # If pause command is False, audio stopped, and track detected...
                player.play()
                played = True

            if not led.value: # If the reading service is unavailable
                led.value = timer(new_audio, 3) # Wait until the 3 seconds have passed to make it availble

            #print(f"Volume: {volPrevio}, ({potentiometer.value}), {led.value}")

            uid = pn532.read_passive_target(timeout=0.03) # Read the RFID tag
            if uid is not None: # If it has detected something...
                print(f"\nFound card with UID: {[hex(i) for i in uid]}")
                print(f"Reading Page {4} ...")
                data = pn532.ntag2xx_read_block(4) # Store data
                if data is not None:
                    data = int.from_bytes(data, "big")
                    last_track = data # Save track number in case of a reboot, else the data would be lost
                    print(f"The number read is: {data}")
                return data, volPrevio, False, index, False
        else: # Make sure neither the LED nor the music is on
            last_track = None
            if led.value:
                led.value = False
            if played:
                player.pause()
                played = False

'''
Mapping function from the read values of the potentiometer to a percentage.
'''
def volume(volPrevio):
    volActual = round(100-potentiometer.value*100/65525)
    if volPrevio != volActual:
        player.set_volume(volActual)
        return volActual
    return volPrevio

'''
This function returns a boolean value comparing if certain seconds have passed based
on a reference time. It is used to avoid using the time.sleep(seconds) function, that 
makes the whole program sleep and makes it useless otherwise during that period.
'''
def timer(reference,tim):
    if time.localtime().tm_sec+time.localtime().tm_min*60-reference >= tim:
        return True
    else:
        return False

main_loop()