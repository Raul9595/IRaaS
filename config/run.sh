#!/bin/bash

Xvfb :1 & export DISPLAY=:1;

#Copy Input file to EC2
aws s3 cp s3://image-rec-512/input/$1 /home/ubuntu/darknet;

# Run YOLO
cd /home/ubuntu/darknet;

./darknet detector demo cfg/coco.data cfg/yolov3-tiny.cfg yolov3-tiny.weights $1 > output.txt;

# rm push.py
# wget https://image-rec-512.s3.amazonaws.com/config/push.py;

python3 push.py

aws s3 cp /home/ubuntu/darknet/output_processed.txt s3://image-rec-512/output/$1;
