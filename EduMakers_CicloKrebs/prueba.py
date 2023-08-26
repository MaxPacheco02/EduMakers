#!/usr/bin/env python3
import time
import os
from RPi import GPIO
 
os.system('clear') # Clear screen
 
# Tell to GPIO library to use logical PIN names/numbers, instead of the physical PIN numbers
GPIO.setmode(GPIO.BCM) 
 
# Set each GPIO pin address
mag_2 = [25,8,7,12]
mag_in_2 = 16
GPIO.setup(mag_in_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for i in range(4):
        GPIO.setup(mag_2[i], GPIO.OUT)

def byte(num):
       out = []
       for i in range(4): # Adding in little endian (due to the demux)
              out.append((num >> i) & 1) # Adding the last bit of the number one-by-one with bit shifting
       return out

sel = byte(31) # Convert decimal to 4-bit number

for i in range(4): # Write the value of the selector of each demux bit-by-bit
        GPIO.output(mag_2[i], sel[i])

while True: # Infinite loop
        d = GPIO.input(mag_in_2)^1
        time.sleep(0.02) # Wait 20 ms
        print(d)