#!/usr/bin/env python3
import time
import os
from RPi import GPIO
import subprocess
 
os.system('clear') #clear screen, this is just for the OCD purposes
 
step = 1 #linear steps for increasing/decreasing volume
paused = False #paused state
num = 0
 
#tell to GPIO library to use logical PIN names/numbers, instead of the physical PIN numbers
GPIO.setmode(GPIO.BCM) 
 
#set up the pins we have been using
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
 
#set up the GPIO events on those pins
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
 
#get the initial states
counter = 0
clkLastState = GPIO.input(clk)
dtLastState = GPIO.input(dt)
swLastState = GPIO.input(sw)
 
#define functions which will be triggered on pin state changes
def encoderClicked(channel):
        global counter, step
        clkState = GPIO.input(clk)
        dtState = GPIO.input(dt)
 
        if not clkState and dtState:
                counter = counter + step
        elif clkState and not dtState:
                counter = counter - step
        print ("Counter ", counter)

def swClicked(channel):
        global paused
        paused = not paused
        print ("Paused ", paused)

def byte(num):
       out = []
       for i in range(4): # Little endian
              out.append((num >> i) & 1)
       return out

def mag_handler(index, val):
        global state, last_changed
        
        if val and not state[index] :
                pass
                # rc = subprocess.call("./play.sh 'audio/%s.mp3'" % index, shell=True)
        
        if state[index] != val:
                state[index] = val
                last_changed = index

def led_display(num):
        code_list = bin(num)[2:].zfill(3)
        for i in range(3):
                GPIO.output(led[i], int(code_list[i]))

#set up the interrupts
GPIO.add_event_detect(clk, GPIO.RISING, callback=encoderClicked, bouncetime=50)
GPIO.add_event_detect(dt, GPIO.RISING, callback=encoderClicked, bouncetime=50)
GPIO.add_event_detect(sw, GPIO.FALLING, callback=swClicked, bouncetime=200)
 
while True:
        #print("Paused:", int(paused), "Encoder:", counter, )
        num = (num+1) % 16
        #led_display(num % 8)

        sel = byte(num)
        for i in range(4):
                GPIO.output(mag_1[i], sel[i])
                GPIO.output(mag_2[i], sel[i])
        val = [GPIO.input(mag_in_1) ^ 1, GPIO.input(mag_in_2) ^ 1]
        print(counter, paused, last_changed)
        mag_handler(num+16, val[1])
        mag_handler(num, val[0])
        time.sleep(0.1)

GPIO.cleanup()

'''
Lines 41, 42, 52, 53 have negations needed to simulate the encoder with buttons.
They need to be reversed again to work correctly in the final implementation.
'''