import boto3
import json
from botocore.exceptions import ClientError
from utils import read_file
import paramiko
import threading
import os.path
import sys

from startInstances import *;

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

def create_new_instances(numberOfInstances):
    ec2_config = get_from_local('config')
    ec2_client = boto3.client('ec2', region_name=ec2_config['region'])

    for i in range(numberOfInstances):
        launch_new_instance(ec2_client, ec2_config)

def stop_all_instances():
    ec2_client = boto3.client('ec2', region_name=ec2_config['region'])
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for instance in instances:
        stop_instance(ec2_client, instance.instance_id)

def clearInputS3():
    s3 = boto.connect_s3()
    bucket = s3.get_bucket("image-rec-512")
    bucketListResultSet = bucket.list(prefix="input/")
    result = bucket.delete_keys([key.name for key in bucketListResultSet])

def clearOutputS3():
    s3 = boto.connect_s3()
    bucket = s3.get_bucket("image-rec-512")
    bucketListResultSet = bucket.list(prefix="output/")
    result = bucket.delete_keys([key.name for key in bucketListResultSet])

#create_new_instances(10)
stop_all_instances()

