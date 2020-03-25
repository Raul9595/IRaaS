#!/usr/bin/python

import storeS3
import os

'''
SETUP:

    -   -->     GND     -->     PIN6
    +   -->     5V      -->     PIN4
    S   -->     GPIO18  -->     PIN12

'''

import RPi.GPIO as GPIO
import subprocess
import time


def main(maxVid):
    sensor = 12

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(sensor, GPIO.IN)

    flag = 0
    max = maxVid

    while flag < max + 1:
        time.sleep(0.5)
        i = GPIO.input(sensor)
        if i == 0:
            print("No intruders")
            time.sleep(1)
        elif i == 1:
            print("Intruder detected")
            flag += 1
            subprocess.call(['sudo', 'cpulimit', '--pid', str(os.getpid()), '--limit', '20'])
            proc = subprocess.Popen(['raspivid', '-o', '../iraas/data/video' + str(flag) + '.h264'], stdout=subprocess.PIPE)
            subprocess.call(['sudo', 'cpulimit', '--pid', str(proc.pid), '--limit', '20'])
            storeS3.main()
