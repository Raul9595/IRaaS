import boto3
import json
from botocore.exceptions import ClientError
from utils import read_file
import paramiko
import threading

BUCKET_NAME = "image-rec-512"
CONFIG_FILE_KEY = "config/config.json"
BUCKET_INPUT_DIR = "input"
BUCKET_OUTPUT_DIR = "output"


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
    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])
    i = 0
    for instance in instances:
        print(instance, instance.id, instance.public_dns_name)
        thread[i] = threading.Thread(
            target=thread_work, args=(ec2_client, i, instance.id,))
        thread[i].start()
        i = i+1
        print(i)
        if (i == len(sqs_messages)):
            break
    delete_messages_from_sqs_queue(delete_messages)

def delete_messages_from_sqs_queue(messages):
    # Delete messages from queue
    sqs = boto3.resource('sqs')
    queue_name = 'ImageRec'
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    queue.delete_messages(Entries=delete_messages) 

def get_messages_from_sqs_queue():
    # Queue instance which retrieves all the messages
    sqs = boto3.resource('sqs')
    queue_name = 'ImageRec'
    max_queue_messages = 10

    queue = sqs.get_queue_by_name(QueueName=queue_name)
    
    sqs_messages = []
    for message in queue.receive_messages(MaxNumberOfMessages=max_queue_messages):
        body = json.loads(message.body)
        # Get the message only if the message is created by the s3 instance
        if body.get('Records')[0].get('eventSource') == 'aws:s3':
            sqs_messages.append({
                'Id': message.message_id,
                'ReceiptHandle': message.receipt_handle
            })
    print('Returning {} messages from SQS'.format(len(sqs_messages)))
    return sqs_messages

def thread_work(ec2_client, tid, instance_id):
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
    cd = '"cd " + "/home/ubuntu/darknet"'
    stdin, stdout, stderr = ssh.exec_command(cd)
    stdin.flush()
    data = stdout.read().splitlines()
    for line in data:
        x = line.decode()
        print(x)

    stdin, stdout1, stderr = ssh.exec_command('pwd')
    stdin.flush()

    data = stdout1.read().splitlines()
    print(data)
    for line in data:
        x = line.decode()
        print(x)

    stdin, stdout1, stderr = ssh.exec_command(
        './darknet detector demo cfg/coco.cfg cfg/yolov3-tiny.cfg yolov3-tiny.weights video.h264')
    stdin.flush()

    data = stdout1.read().splitlines()
    print(data)
    for line in data:
        x = line.decode()
        print(x)

    ssh.close()

def check_queue_and_launch_instances(ec2_client, ec2_config):
    # Get all the messages from queue and delete it once the instances are created for each message
    while True:
        delete_messages = get_messages_from_sqs_queue()

        # If there are no more messages in the queue, break
        if len(delete_messages) == 0:
            break
        else:
            '''
            # Launch instances for each sqs message
            queue.delete_messages(Entries=delete_messages)
            '''
            print('Starting instances as the SQS has messages')
            start_instances(ec2_client, delete_messages)

def get_config_from_file():
    # Load config from local file
    return json.loads(read_file('./config/config.json'))


def get_config_from_s3():
    # Load config from S3
    s3 = boto3.client('s3')
    result = s3.get_object(Bucket=BUCKET_NAME, Key=CONFIG_FILE_KEY)
    ec2_config = json.loads(result["Body"].read().decode())


if __name__ == '__main__':
    ec2_config = get_config_from_file()
    ec2_client = boto3.client('ec2', region_name=ec2_config['region'])
    check_queue_and_launch_instances(ec2_client, ec2_config)
    #stop_instance(ec2, 'i-091db2b47191de217')
