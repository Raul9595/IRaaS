import boto3
import ast
import json
from utils import read_file
import subprocess
import os.path
import sys

BUCKET_NAME = "image-rec-512"
CONFIG_S3_FILE_KEY = "config/config.json"
CONFIG_LOCAL_FILE_KEY = "./config/config.json"
COMMANDS_S3_FILE_KEY = "config/commands.txt"
COMMANDS_LOCAL_FILE_KEY = "config/commands.txt"
BUCKET_INPUT_DIR = "input"
BUCKET_OUTPUT_DIR = "output"
SQS_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/694968717068/ImageRec"


def delete_message(sqs, queue_url, receipt_handle):
    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)


def add_message(message):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='ImageRec')
    response = queue.send_message(MessageBody=message['Body'])


def process_video(message):
    input_video = ast.literal_eval(message['Body']).get('Records')[0].get('s3').get('object').get('key').split('/')[1]

    commands = get_from_local('commands')
    commands = commands.replace("inputFile", input_video)
    commands = commands.replace("outputFile", input_video + "_output.txt")
    commands = commands.replace("exType", "pi")
    print('\nCommannds ')
    print(commands)

    try:
        proc = subprocess.Popen(commands, stdout=subprocess.PIPE, shell=True)
        res = proc.communicate()
        print("error =", res[1])

    except subprocess.CalledProcessError:
        print('Adding message back to queue')
        add_message(message)


def get_message(sqs):
    response = sqs.receive_message(QueueUrl=SQS_QUEUE_URL)
    if 'Messages' in response.keys():
        return response['Messages'][0]


def get_from_local(file):
    # Load config from local file
    if file == 'config':
        return json.loads(read_file(CONFIG_LOCAL_FILE_KEY))
    elif file == 'commands':
        my_path = os.path.dirname(sys.argv[0])
        path = os.path.join(my_path, COMMANDS_LOCAL_FILE_KEY)
        print(path)
        file = open(path)
        return file.read()


def get_from_s3(file):
    # Load config from S3
    s3 = boto3.client('s3')
    if file == 'config':
        result = s3.get_object(Bucket=BUCKET_NAME, Key=CONFIG_S3_FILE_KEY)
        return json.loads(result["Body"].read().decode())
    elif file == 'commands':
        result = s3.get_object(Bucket=BUCKET_NAME, Key=COMMANDS_S3_FILE_KEY)
        return result


if __name__ == '__main__':
    sqs = boto3.client('sqs')
    try:
        while True:
            message = get_message(sqs)
            print(message)
            if message:
                delete_message(sqs, SQS_QUEUE_URL, message['ReceiptHandle'])
                process_video(message)

    except KeyboardInterrupt:
        pass
