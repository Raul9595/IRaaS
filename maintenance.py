import boto3
import json
from botocore.exceptions import ClientError
from utils import read_file
import paramiko
import threading
import os.path
import sys

from startInstances import *;

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

#create_new_instances(10)
stop_all_instances()

