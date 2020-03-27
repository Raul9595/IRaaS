#!/bin/bash

cd /home/pi/darknet;

aws s3 cp s3://image-rec-512/input/$1 $1;

./darknet detector demo cfg/coco.data cfg/yolov3-tiny.cfg yolov3-tiny.weights $1 > output.txt;

# Copy output file to S3
aws s3 cp output.txt s3://image-rec-512/output/$2;