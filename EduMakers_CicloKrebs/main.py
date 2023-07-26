#!/usr/bin/env python3
import time
import os
from RPi import GPIO
from pygame import mixer
from datetime import datetime
 
os.system('clear') # Clear screen
 
# Tell to GPIO library to use logical PIN names/numbers, instead of the physical PIN numbers
GPIO.setmode(GPIO.BCM) 
 
# Set each GPIO pin address
clk = 22
dt = 27
sw = 17
mag_1 = [14,15,18,23]
mag_2 = [25,8,7,12]
mag_in_1 = 24
mag_in_2 = 16
led = [2,3,4]

# Set inputs
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(sw, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(mag_in_1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(mag_in_2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Set outputs
for i in range(4):
        GPIO.setup(mag_1[i], GPIO.OUT)
        GPIO.setup(mag_2[i], GPIO.OUT)
        if i < 3:
                GPIO.setup(led[i], GPIO.OUT)

# General global variables
clkLastState = GPIO.input(clk) # Initial encoder and button states
dtLastState = GPIO.input(dt)
swLastState = GPIO.input(sw)

volume = 0.5 # Initial volume
step = 0.1 # Rate of change for increasing/decreasing volume with encoder
paused = False # Initial pause state
num = 0 # The number being read by the demux

old_state = 0 # Last output LED state
state = 0 # Current LED state (off)
last_state_change = datetime.now() # The last time a state was modified

loaded = False # Know if an audio is loaded to be played or paused

last_changed = -1 # The address of the last piece to be raised
last_raised = [] # Know all the current pieces that are away from the box

last_paused_time = datetime.now() # The last time the button was pressed
button_still_pressed = False # Know if the button has remained pressed since its last rising edge

lang_no = len(next(os.walk("/home/pi4/EduMakers/EduMakers_CicloKrebs/audio/0/"))[2]) # How many languages are registered
lang_index = 0 # The index of the current language playing
 
# Functions

# Interrupt function to toggle the volume every time the encoder angle changes
def volChange(channel):
        global volume, state
        clkState = GPIO.input(clk)
        dtState = GPIO.input(dt)
 
        if not clkState and dtState:
                volume = volume - step
                state = 7 # Decrease volume state (white)
        elif clkState and not dtState:
                volume = volume + step
                state = 5 # Increase volume state (magenta)
        
        if volume > 1:
                volume = 1 # Volume can't be more than 1
        if volume < 0:
                volume = 0 # Volume can't be less than 0
        
        mixer.music.set_volume(volume) # Set volume
        print ("volume:", volume)

# Interrupt function to handle each button press and release
def butChange(channel):
        global paused, button_still_pressed, last_paused_time, state

        if not GPIO.input(sw): # If button is pressed...
                paused = not paused # Toggle pause state
                mixer.music.pause() if paused else mixer.music.unpause() # Pause if not, and the other way around
                if paused: # If the audio is paused...
                        state = 4 # Pause state (red)
                elif loaded: # If the audio is unpaused...
                        state = 1 # Playing state (blue)
                else: # If no audio was playing before pausing...
                        state = 2 # Standby state (green)

                print ("Paused ", paused)
                button_still_pressed = True # Update the press holding value
                last_paused_time = datetime.now() # Update the last time the button was pressed
        else: # If button is released...
                button_still_pressed = False # Update the press holding value

# Function to convert from decimal to 4-bit number
def byte(num):
       out = []
       for i in range(4): # Adding in little endian (due to the demux)
              out.append((num >> i) & 1) # Adding the last bit of the number one-by-one with bit shifting
       return out

# Function to handle the magnetic hall sensor values
def mag_handler(index, val):
        global state, last_changed, last_raised, loaded

        if val and index not in last_raised: # If the piece is raised and hasn't been registered in the list...
                last_changed = index # Update the address of the last-raised-piece
                last_raised.append(index) # Add it to the list
                loaded = True # A song is now loaded and ready to be played, paused, and consequently resumed
                play(lang_index+1,index+1, -1) # Play the newly-raised piece's audio
                state = 1 # Playing state (blue)
        
        if not val and index in last_raised: # If a raised piece is back in the box...
                if last_changed == index: # If it's the last-raised piece
                        mixer.music.stop() # Stop the audio
                        loaded = False # 'Unload' the audio, so if the pause button is pressed, it goes back to green
                        state = 2 # Standby state (green)
                last_raised.remove(index) # Remove the piece address from the list

 # Function to convert decimal to value of the RGB code, containing 8 combinations (3 bits)
def led_display(num):
        num_code = bin(num)[2:].zfill(3) # No matter if the number is low, convert it to 3-bit number
        for i in range(3):
                GPIO.output(led[i], int(num_code[i])) # Output the Red, Green, and Blue pins one-by-one

# Function to play an audio
def play(lang, track, loop):
        address = "/home/pi4/EduMakers/EduMakers_CicloKrebs/audio/" + str(lang) + "/" + str(track) + ".mp3" # Specify the address of the audio
        print("Playing:", track)
        mixer.music.load(address) # Load audio
        mixer.music.play(loops = loop) # Play audio (during simulations, the loops were infinite due to the small duration of each audio)

time.sleep(1) # Sleep 1 second before starting the program

# Interrupts setup
GPIO.add_event_detect(clk, GPIO.RISING, callback=volChange, bouncetime=50)
GPIO.add_event_detect(dt, GPIO.RISING, callback=volChange, bouncetime=50)
GPIO.add_event_detect(sw, GPIO.BOTH, callback=butChange, bouncetime=50)

# Main
mixer.init() # Initiate the audio player
play(0, lang_index+1, 0) # Play the name of the language to display audio in
state = 2 # Standby state (green)

while True: # Infinite loop
        num = (num+1) % 16 # Iterate the address read on demux
        sel = byte(num) # Convert decimal to 4-bit number

        if state != old_state: # If the current state differs from the last displayed...
                last_state_change = datetime.now() # Register new time for the state change
                old_state = state # Update the state

        if (datetime.now() - last_state_change).microseconds> 100_000: # Change the state 0.1 seconds after its change
                led_display(old_state) # Display the state with the LED
                if old_state in [3,5,7]: # If the state belongs to one of the 3 non-important states (volume up/down or language change)...
                        if paused: # Return to red if important state was pause
                                state = 4 # Pause state (red)
                        elif loaded: # Return to blue if important state was playing
                                state = 1 # Playing state (blue)
                        else: # Return to green if important state was standby
                                state = 2 # Standby state (green)

        for i in range(4): # Write the value of the selector of each demux bit-by-bit
                GPIO.output(mag_1[i], sel[i])
                GPIO.output(mag_2[i], sel[i])
        time.sleep(0.02) # Wait 20 ms
        val = [GPIO.input(mag_in_1) ^ 1, GPIO.input(mag_in_2) ^ 1] # Read each of the demux values
        
        if (datetime.now() - last_paused_time).seconds > 2 and button_still_pressed: # If the button has been pressed for 3 seconds...
                button_still_pressed = False # Wait until the button is released to change languages again
                mixer.music.stop() # Stop current audio
                loaded = False # 'Unload' the audio from the mixer, to go back to the Standby state
                lang_index = (lang_index+1) % lang_no # Iterate the language index
                play(0, lang_index+1, 0) # Play the audio saying the new language selected
                state = 3 # Language change state (cyan)
        mag_handler(num+16, val[1]) # Handle what each demux input does
        mag_handler(num, val[0])