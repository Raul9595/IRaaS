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
import storeS3


def main(maxVid):
    sensor = 12

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(sensor, GPIO.IN)

    flag = 0
    max = maxVid

    while flag < max:
        time.sleep(0.5)
        i = GPIO.input(sensor)
        if i == 0:
            print("No intruders")
        elif i == 1:
            print("Intruder detected")
            flag += 1
            subprocess.call(['raspivid', '-o', '../iraas/data/video' + str(flag) + '.h264', '-t', '5000', '-w', '640', '-h', '480', '-fps', '20'])
            storeS3.main()
