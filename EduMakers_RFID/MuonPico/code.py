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

last_1 = 0
last_2 = 0
last_3 = 0
new_last_press = 0
prevCount = 2
prevCount2 = 2
dataPrev = 0
folders = 3

pause = {
    0:"Play",
    1:"Pause",
}
    
lang_dict = {
  1 : "Song",
  2 : "Spanish Maps",
  3 : "English Human Body",
  4 : "Spanish Human Body",
  16 : "Default Beeps",
}

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
pause_but = DigitalInOut(board.D20)
prev_lang = DigitalInOut(board.D17)
next_lang = DigitalInOut(board.D19)
pause_but.switch_to_input(pull=digitalio.Pull.UP)
prev_lang.switch_to_input(pull=digitalio.Pull.UP)
next_lang.switch_to_input(pull=digitalio.Pull.UP)

time.sleep(0.5)
player.set_volume(50)
player.play(0,0) # Whenever the device is rebooted, play the 'welcome' track
print("Sleeping for 1.8 seconds Before start")
time.sleep(1.8)

'''
This is the main function. It's an infinite loop which in every iteration reads
the RFID card; if a TAG from an object is found, it plays its code-related audio
y turns off the status LED for 5 seconds, indicating the reading service is 
temporarily unavailable.
'''
def main_loop(player=player):
    global prevCount, prevCount2, dataPrev
    new_audio=0
    trackPrev = 0
    index = 0
    print("Waiting for NFC tag to start playing music")
    volPrevio = 30

    player.play(0,index%folders+1)
    while True:
        track, volPrevio, reboot, index, changed_lang = read_nfc(volPrevio, new_audio, index)
        print("main loop")
        if changed_lang:
            player.play(0,index%folders+1)
            new_audio = time.localtime().tm_sec+time.localtime().tm_min*60
            dataPrev = 0
        elif track is not None:
            if led.value or reboot:
                #player.play(16, 2)
                player.play(range(folders)[index%folders]+1, track)
                print("Playing audio... wait at least 3 seconds to track other objects")
                led.value = False
                new_audio = time.localtime().tm_sec+time.localtime().tm_min*60
                prevCount += 2
                prevCount2 += 2
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
be played again.
'''
def read_nfc(volPrevio, new_audio, index):
    global dataPrev, last_1, last_2, last_3
    count = 0
    last = 0
    changed_lang = False
    played = False
    lang = 0
    print("Waiting for RFID/NFC card to read!")
    while True:
        volPrevio = volume(volPrevio)

        if timer(new_audio, 1):
            lang = language()
            if lang[0] and not last:
                count+=1
                last_3 = last_2
                last_2 = last_1
                last_1 = time.localtime().tm_sec+time.localtime().tm_min*60
                if last_1 - last_3 < 2:
                    print("Reboot")
                    if dataPrev == 0:
                        return None, volPrevio, True, index, False
                    else:
                        return dataPrev, volPrevio, True, index, False

            last = lang[0]
            if lang[1]:
                return dataPrev, volPrevio, False, index-1, True
            if lang[2]:
                return dataPrev, volPrevio, False, index+1, True
        
        if count%2 == 1:
            player.pause()
            played = False
        elif not played:
            print('a')
            if dataPrev != 0:
                player.play()
            played = True

        if not led.value:
            led.value = timer(new_audio, 3)

        #print(f"Audio status: {pause[count%2]}, Index: {index}, List: {lang}")
        print(f"Volume: {volPrevio}, ({potentiometer.value}), {led.value}")
        if reset_audio(count):
            pass
            #print('REBOOT')
            #return dataPrev, volPrevio, lang, True

        uid = pn532.read_passive_target(timeout=0.03)
        if uid is not None:
            print(f"\nFound card with UID: {[hex(i) for i in uid]}")
            print(f"Reading Page {4} ...")
            data = pn532.ntag2xx_read_block(4)
            if data is not None:
                data = int.from_bytes(data, "big")
                dataPrev = data
                print(f"The number read is: {data}")
            return data, volPrevio, False, index, changed_lang

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
This function reads the dipswitch value and returns its decimal representation.
The user is supposed to select in binary (BigEndian) the number of the folder 
where the wished language/book/theme points to.

# No-Language
# 1-Song
# 2-Spanish Maps
# 3-English Human Body
# 4-Spanish Human Body
# 16-Default beeps (DO NOT REMOVE)
'''
def language():
    lang = [next_lang.value, prev_lang.value, pause_but.value]
    return [int(x^1) for x in lang]

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
    
'''
This function detects how many times the button has been pressed in the last
2 seconds. According to most audio systems, if the pause/play button is pressed
3 times in a certain amount of time, a song is played again from the beginning.
'''
def reset_audio(count):
    global prevCount, prevCount2, new_last_press
    if count != prevCount2:
        prevCount2 = count
        new_last_press = time.localtime().tm_sec+time.localtime().tm_min*60
    time_passed = timer(new_last_press, 2)
    if not time_passed:
        if count - prevCount > 2:
            prevCount = count
            prevCount2 = count
            return True
    else:
        if count != prevCount:
            prevCount = count    
    return False

'''
This functions warns the user if the specified album/folder/book/theme/language
is not registered in the device if the dipswitch is not correctly configured. 
Remember to register new languages in the global 'lang_dict' variable.
'''
def play_song(lang, track):
    if lang in lang_dict:
        player.play(lang, track)
    else:
        player.play(99, 99)

main_loop()