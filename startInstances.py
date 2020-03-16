import boto3
import json
from botocore.exceptions import ClientError
from utils import read_file
import paramiko
import threading
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


def launch_new_instance(ec2, config):
    # Launch a new instance

    # EC2 Instance Configuration details
    tag_specs = [{}]
    tag_specs[0]['ResourceType'] = 'instance'
    tag_specs[0]['Tags'] = config['set_new_instance_tags']

    print('Launching new EC2 instance')
    ec2_response = ec2.run_instances(
        ImageId=config['ami'],
        InstanceType=config['instance_type'],
        KeyName=config['ssh_key_name'],
        MinCount=1,
        MaxCount=1,
        SecurityGroupIds=config['security_group_ids'],
        TagSpecifications=tag_specs
    )

    new_instance_resp = ec2_response['Instances'][0]
    instance_id = new_instance_resp['InstanceId']
    print('Launched new EC2 instance with id: ', instance_id)

    return instance_id, new_instance_resp


def start_instance(ec2, instance_id):
    # Start an existing instance with id instance_id
    try:
        response = ec2.start_instances(InstanceIds=[instance_id], DryRun=False)
        print('Started existing instance with ID:', instance_id)
    except ClientError as e:
        print(e)


def stop_instance(ec2, instance_id):
    # Stop an instance with id instance_id
    try:
        response = ec2.stop_instances(InstanceIds=[instance_id], DryRun=False)
        print('Stopped instance with ID:', instance_id)
    except ClientError as e:
        print(e)


def start_instances(ec2_client, sqs_messages):
    # Start multiple instances depending on the number of messages in SQS queue
    ec2 = boto3.resource('ec2')
    thread = [0] * len(sqs_messages)
    instance_thread_link = {}

    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])
    i = 0
    for instance in instances:
        print(instance, instance.id, instance.public_dns_name)
        instance_thread_link[i] = instance.id
        thread[i] = threading.Thread(
            target=thread_work, args=(ec2_client, i, instance.id, sqs_messages[i],))
        thread[i].start()
        i = i + 1
        print(i)
        if i == len(sqs_messages):
            break

    for j in range(len(sqs_messages)):
        if i != 0:
            thread[j].join()
            print('Stopping instance')
            stop_instance(ec2_client, instance_thread_link[j])


def delete_messages_from_sqs_queue(message):
    # Delete messages from queue
    sqs = boto3.resource('sqs')
    queue_name = 'ImageRec'
    print(message)
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    queue.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=message.get('ReceiptHandle'))


def get_messages_from_sqs_queue(delete_messages):
    # Queue instance which retrieves all the messages
    sqs = boto3.resource('sqs')
    queue_name = 'ImageRec'
    max_queue_messages = 10

    queue = sqs.get_queue_by_name(QueueName=queue_name)

    for message in queue.receive_messages(MaxNumberOfMessages=max_queue_messages, VisibilityTimeout=180):
        body = json.loads(message.body)
        # Get the message only if the message is created by the s3 instance
        if body.get('Records')[0].get('eventSource') == 'aws:s3':
            delete_messages.append({
                'Id': message.message_id,
                'ReceiptHandle': message.receipt_handle,
                'Body': body
            })
    delete_messages = list({v['Id']: v for v in delete_messages}.values())
    if len(delete_messages):
        print('Returning {} message from SQS'.format(len(delete_messages)))
    else:
        print('Returning {} messages from SQS'.format(len(delete_messages)))
    return delete_messages


def thread_work(ec2_client, tid, instance_id, sqs_message):
    ec2 = boto3.resource('ec2')
    start_instance(ec2_client, instance_id)
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

    commands = get_from_local('commands')
    commands = commands.replace("videoDownload",
                                sqs_message['Body'].get('Records')[0].get('s3').get('object').get('key').split('/')[1])
    commands.replace("queueURL", SQS_QUEUE_URL)
    commands.replace("receiptHandle", sqs_message.get('ReceiptHandle'))
    print('\nCommannds ')
    print(commands)
    stdin, stdout, stderr = ssh.exec_command(commands)
    data = stdout.read().splitlines()
    print(data)
    for line in data:
        x = line.decode()
        print(x)

    if len(stderr) == 0:
        delete_messages_from_sqs_queue(sqs_message)

    ssh.close()


def check_queue_and_launch_instances(ec2_client, ec2_config):
    # Get all the messages from queue and delete it once the instances are created for each message
    delete_messages = []

    while True:
        delete_messages = get_messages_from_sqs_queue(delete_messages)

        # If there are no more messages in the queue, break
        if len(delete_messages) == 0:
            break
        else:
            # Launch instances for each sqs message
            print('Starting instances as the SQS has messages')
            start_instances(ec2_client, delete_messages)


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
    ec2_config = get_from_local('config')
    ec2_client = boto3.client('ec2', region_name=ec2_config['region'])
    check_queue_and_launch_instances(ec2_client, ec2_config)
