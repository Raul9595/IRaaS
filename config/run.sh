#!/bin/bash

# check if package is installed
# install package if not installed
installPackage() {
    retval=0
    echo "Installing package $1"
    if [ $(dpkg-query -W -f='${Status}' $1 2>/dev/null | grep -c "ok installed") -eq 0 ];
    then
        echo "Package $1 is not installed"
        if echo "yes" | sudo apt-get install $1; then
            retval=1
        fi
    else
        echo "Package $1 is already installed"
        retval=1
    fi
    return "$retval"
}

Xvfb :1 & export DISPLAY=:1;

#Install AWS CLI if required
installPackage awscli;

#Copy Input file to EC2
aws s3 cp s3://image-rec-512/input/$1 /home/ubuntu/darknet;

# Run YOLO
cd /home/ubuntu/darknet;

./darknet detector demo cfg/coco.data cfg/yolov3-tiny.cfg yolov3-tiny.weights $1 > output.txt;

rm push.py
wget https://image-rec-512.s3.amazonaws.com/config/push.py;

python3 push.py

aws s3 cp /home/ubuntu/darknet/output_processed.txt s3://image-rec-512/output/$1;
