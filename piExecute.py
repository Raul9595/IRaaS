import boto3
import ast
import subprocess
import os.path
import sys
import paramiko
import json
import time

BUCKET_NAME = "image-rec-512"
CONFIG_S3_FILE_KEY = "config/config.json"
CONFIG_LOCAL_FILE_KEY = "./config/config.json"
COMMANDS_S3_FILE_KEY = "config/commandPi.txt"
COMMANDS_LOCAL_FILE_KEY = "config/commandPi.txt"
BUCKET_INPUT_DIR = "input"
BUCKET_OUTPUT_DIR = "output"
SQS_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/103147106654/ImageRec"


def delete_message(sqs, queue_url, receipt_handle):
    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)


def add_message(message):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='ImageRec')
    response = queue.send_message(MessageBody=message['Body'])


def connect_to_instance(instance_id, val):
    ec2_config = get_from_local('config')
    ec2 = boto3.resource('ec2', region_name=ec2_config['region'])
    instance = ec2.Instance(id=instance_id)
    print('Waiting for instance {} come in running state'.format(instance_id))
    instance.wait_until_running()
    print('Instance {} is now in running state'.format(instance_id))
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    privkey = paramiko.RSAKey.from_private_key_file(
        './config/image_rec_auth.pem')
    current_instance = list(ec2.instances.filter(InstanceIds=[instance_id]))
    print(current_instance[0].public_ip_address)
    print('SSH into the instance')
    ssh.connect(hostname=current_instance[0].public_ip_address,
                username='ubuntu', pkey=privkey)

    commands = "echo \"" + str(val) + "\" > /home/ubuntu/pi_status.txt;"

    print('\nCommands ')
    print(commands)

    stdin, stdout, stderr = ssh.exec_command(commands)
    data = stdout.read().splitlines()
    print(data)
    for line in data:
        x = line.decode()
        print(x)

    ssh.close()


def process_video(message):
    connect_to_instance('i-01b3d9f2d287a0a1c', 1)
    input_video = ast.literal_eval(message['Body']).get('Records')[0].get('s3').get('object').get('key').split('/')[1]

    commands = get_from_local('commands')
    commands = commands.replace("inputFile", input_video)
    commands = commands.replace("outputFile", input_video + "_output.txt")
    print('\nCommands ')
    print(commands)

    try:
        proc = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('Complete')
        res = proc.communicate()

        if res[1] is not None:
            print('Adding message back to queue as res[1] is not None', res[1])
            add_message(message)
            return
        else:
            connect_to_instance('i-01b3d9f2d287a0a1c', 0)
            return

    except subprocess.CalledProcessError as e:
        print('Adding message back to queue due to process error', e)
        add_message(message)
        connect_to_instance('i-01b3d9f2d287a0a1c', 0)


def get_message(sqs):
    response = sqs.receive_message(QueueUrl=SQS_QUEUE_URL, MaxNumberOfMessages=10, WaitTimeSeconds=5,
                                   VisibilityTimeout=10)
    if 'Messages' in response.keys():
        return response['Messages'][0]


def get_from_local(file):
    # Load config from local file
    if file == 'config':
        return json.loads(open(CONFIG_LOCAL_FILE_KEY).read())
    elif file == 'commands':
        my_path = os.path.dirname(sys.argv[0])
        path = os.path.join(my_path, COMMANDS_LOCAL_FILE_KEY)
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


def main():
    sqs = boto3.client('sqs')
    try:
        while True:
            message = get_message(sqs)
            if message and ast.literal_eval(message['Body']).get('Records') is not None and \
                    ast.literal_eval(message['Body']).get('Records')[0].get('eventSource') == 'aws:s3':
                delete_message(sqs, SQS_QUEUE_URL, message['ReceiptHandle'])
                process_video(message)

    except KeyboardInterrupt:
        connect_to_instance('i-01b3d9f2d287a0a1c', 0)
