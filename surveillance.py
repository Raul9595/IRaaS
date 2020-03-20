#!/usr/bin/python

'''
SETUP:

    -   -->     GND     -->     PIN6
    +   -->     5V      -->     PIN4
    S   -->     GPIO18  -->     PIN12

'''

import RPi.GPIO as GPIO
import subprocess
import time
import sys


def main(maxVid):
    sensor = 12

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(sensor, GPIO.IN)

    on = 0
    off = 0
    flag = 0
    max = maxVid

    while flag < max + 1:
        i = GPIO.input(sensor)
        if i == 0:
            print("No intruders")
            time.sleep(1)
        elif i == 1:
            print("Intruder detected")
            flag += 1
            subprocess.call(['raspivid', '-o', '../darknet/video' + str(flag) + '.h264'])
            time.sleep(0.1)
