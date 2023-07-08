#!/usr/bin/env python3
import time
import os
from RPi import GPIO
 
os.system('clear') #clear screen, this is just for the OCD purposes
 
step = 1 #linear steps for increasing/decreasing volume
paused = False #paused state
 
#tell to GPIO library to use logical PIN names/numbers, instead of the physical PIN numbers
GPIO.setmode(GPIO.BCM) 
 
#set up the pins we have been using
clk = 18
dt = 15
sw = 14
 
#set up the GPIO events on those pins
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(sw, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
 
#get the initial states
counter = 0
clkLastState = GPIO.input(clk)
dtLastState = GPIO.input(dt)
swLastState = GPIO.input(sw)
 
#define functions which will be triggered on pin state changes
def clkClicked(channel):
        global counter
        global step
 
        clkState = GPIO.input(clk)
        dtState = GPIO.input(dt)
 
        if clkState == 0 and dtState == 1:
                counter = counter + step
                #print ("Counter ", counter)

def dtClicked(channel):
        global counter
        global step
 
        clkState = GPIO.input(clk)
        dtState = GPIO.input(dt)
         
        if clkState == 1 and dtState == 0:
                counter = counter - step
                #print ("Counter ", counter)

def swClicked(channel):
        global paused
        paused = not paused
        #print ("Paused ", paused)

#set up the interrupts
GPIO.add_event_detect(clk, GPIO.FALLING, callback=clkClicked, bouncetime=50)
GPIO.add_event_detect(dt, GPIO.FALLING, callback=dtClicked, bouncetime=50)
GPIO.add_event_detect(sw, GPIO.FALLING, callback=swClicked, bouncetime=200)
 
while True:
    print(int(paused),counter)
    time.sleep(0.03)

GPIO.cleanup()