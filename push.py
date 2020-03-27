import json
import boto3
import re
import sys

BUCKET_NAME = "image-rec-512"


def push_output():
    s3 = boto3.client('s3')
    lst = ["zebra", "wine glass", "vase", "umbrella", "tv", "truck", "train", "traffic light", "toothbrush", "toilet",
           "toaster", "tie", "tennis racket", "teddy bear", "surfboard", "suitcase", "stop sign", "sports ball",
           "spoon", "snowboard", "skis", "skateboard", "sink", "sheep", "scissors", "sandwich", "remote",
           "refrigerator", "potted plant", "pizza", "person", "parking meter", "oven", "orange", "mouse", "motorcycle",
           "microwave", "laptop", "knife", "kite", "keyboard", "hot dog", "horse", "handbag", "hair drier", "giraffe",
           "frisbee", "fork", "fire hydrant", "elephant", "donut", "dog", "dining table", "cup", "cow", "couch",
           "clock", "chair", "cell phone", "cat", "carrot", "car", "cake", "bus", "broccoli", "bowl", "bottle", "book",
           "boat", "bird", "bicycle", "bench", "bed", "bear", "baseball glove", "baseball bat", "banana", "backpack",
           "apple", "airplane"]

    items_found = []

    for item in lst:
        with open('/home/ubuntu/darknet/output.txt') as f:
            for line in f:
                if re.search("{0}".format(item+":"), line):
                    print(line)
                    items_found.append(item)

    mylist = list(set(items_found))

    if len(items_found) == 0:
        items_found.append("No object detected")

    f = open("/home/ubuntu/darknet/output_processed.txt", "w")
    f.write(json.dumps(mylist))
    f.close()

push_output()
