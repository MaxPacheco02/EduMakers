#!/usr/bin/env python3
import time
import os
from RPi import GPIO
from pygame import mixer
from datetime import datetime
 
os.system('clear') #clear screen, this is just for the OCD purposes

counter = 0.5
step = 0.1 #linear steps for increasing/decreasing volume
paused = False #paused state
num = 0
 
# Tell to GPIO library to use logical PIN names/numbers, instead of the physical PIN numbers
GPIO.setmode(GPIO.BCM) 
 
# Set up the pins we have been using
clk = 22
dt = 27
sw = 17
mag_1 = [14,15,18,23]
mag_2 = [25,8,7,12]
mag_in_1 = 24
mag_in_2 = 16

led = [2,3,4]

state = [0]*32
last_changed = -1
last_raised = []

last_paused_time = 0
button_still_pressed = False

lang_no = next(os.walk("/audio/0"))
lang_index = 0
 
# Set up the GPIO events on those pins
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(sw, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.setup(mag_in_1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(mag_in_2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

for i in range(3):
        GPIO.setup(led[i], GPIO.OUT)
        GPIO.setup(mag_1[i], GPIO.OUT)
        GPIO.setup(mag_2[i], GPIO.OUT)
GPIO.setup(mag_1[3], GPIO.OUT)
GPIO.setup(mag_2[3], GPIO.OUT)
 
# Get the initial states
clkLastState = GPIO.input(clk)
dtLastState = GPIO.input(dt)
swLastState = GPIO.input(sw)

# Initiate the audio player
mixer.init()
 
# Define functions which will be triggered on pin state changes
def volChange(channel):
        global counter
        clkState = GPIO.input(clk)
        dtState = GPIO.input(dt)
 
        if not clkState and dtState:
                counter = counter - step
                led_display(7)
        elif clkState and not dtState:
                counter = counter + step
                led_display(5)
        
        if counter > 1:
                counter = 1
        if counter < 0:
                counter = 0
        
        mixer.music.set_volume(counter)

        print ("Counter ", counter)

def butPressed(channel):
        global paused, button_still_pressed, last_paused_time
        paused = not paused
        mixer.music.pause() if paused else mixer.music.unpause()
        led_display(4) if paused else led_display(1)
        print ("Paused ", paused)
        button_still_pressed = True
        last_paused_time = datetime.now()

def butReleased(channel):
        global button_still_pressed
        button_still_pressed = False

def byte(num):
       out = []
       for i in range(4): # Little endian
              out.append((num >> i) & 1)
       return out

def mag_handler(index, val):
        global state, last_changed, last_raised

        if val and index not in last_raised:
                last_changed = index
                last_raised.append(index)
                play(lang_index+1,index+1)
                led_display(1)
        
        if not val and index in last_raised:
                if last_changed == index:
                        mixer.music.stop()
                        led_display(2)
                last_raised.remove(index)
                
        
        '''
        if val and not state[index] :
                play(1,index+1)                
        
        if state[index] != val:
                state[index] = val
                last_changed = index
        '''

def led_display(num): # Decimal to binary conversion of the RGB code, containing 8 combinations.
        num_code = bin(num)[2:].zfill(3)
        for i in range(3):
                GPIO.output(led[i], int(num_code[i]))

def play(lang, track):
        address = "/home/pi4/EduMakers/EduMakers_CicloKrebs/audio/" + str(lang) + "/" + str(track) + ".mp3"
        #address = "/home/pi4/EduMakers/EduMakers_CicloKrebs/audio/huuh.mp3"
        print("=" * 20)
        print("playing:", track)
        mixer.music.load(address)
        mixer.music.play()

#set up the interrupts
time.sleep(1)
GPIO.add_event_detect(clk, GPIO.RISING, callback=volChange, bouncetime=50)
GPIO.add_event_detect(dt, GPIO.RISING, callback=volChange, bouncetime=50)
GPIO.add_event_detect(sw, GPIO.FALLING, callback=butPressed, bouncetime=200)
GPIO.add_event_detect(sw, GPIO.RISING, callback=butReleased, bouncetime=200)

play(0, lang_index+1)
led_display(2)

while True:
        #print("Paused:", int(paused), "Encoder:", counter)
        num = (num+1) % 16
        sel = byte(num)
        for i in range(4):
                GPIO.output(mag_1[i], sel[i])
                GPIO.output(mag_2[i], sel[i])
        val = [GPIO.input(mag_in_1) ^ 1, GPIO.input(mag_in_2) ^ 1]
        
        delta_time = datetime.now() - last_paused_time
        if delta_time.seconds > 3:
                lang_index = (lang_index+1) % lang_no
                play(0, lang_index+1)
                led_display(3)
        #print(counter, paused, last_changed)
        print(lang_index, last_raised)
        mag_handler(num+16, val[1])
        mag_handler(num, val[0])
        time.sleep(0.02)

GPIO.cleanup()

# Pendiente:
# - Probar status de LEDs
# - Probar camdio de lenguaje
# - Probar funcionalidad de parar en cuanto el último recogido sea puesto de nuevo con implementacion de listas