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

if test "$3" != "pi";
then
    #Install AWS CLI if required
    installPackage awscli;

    #Copy Input file to EC2
    aws s3 cp s3://image-rec-512/input/$1 /home/ubuntu/darknet;

    # Run YOLO
    Xvfb :1 & export DISPLAY=:1;

    cd /home/ubuntu/darknet;

    ./darknet detector demo cfg/coco.data cfg/yolov3-tiny.cfg yolov3-tiny.weights $1 > output.txt;

else

    cd /home/pi/darknet;

    ./darknet detector demo cfg/coco.data cfg/yolov3-tiny.cfg yolov3-tiny.weights "/home/pi/iraas/data/"$1 > output.txt;

fi

# Copy output file to S3
aws s3 cp output.txt s3://image-rec-512/output/$2;