import boto3
import json

BUCKET_NAME = "image-rec-512"
CONFIG_FILE_KEY = "config/config.json"
BUCKET_INPUT_DIR = "input"
BUCKET_OUTPUT_DIR = "output"


def launch_instance(ec2, config):
    tag_specs = [{}]
    tag_specs[0]['ResourceType'] = 'instance'
    tag_specs[0]['Tags'] = config['set_new_instance_tags']

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

    return instance_id, new_instance_resp


def create_instances():
    sqs = boto3.resource('sqs')
    queue_name = 'ImageRec'
    max_queue_messages = 10

    queue = sqs.get_queue_by_name(QueueName=queue_name)
    message_bodies = []

    while True:
        messages_to_delete = []
        for message in queue.receive_messages(MaxNumberOfMessages=max_queue_messages):

            body = json.loads(message.body)
            message_bodies.append(body)
            if message_bodies[0].get('Records')[0].get('eventSource') == 'aws:s3':
                messages_to_delete.append({
                    'Id': message.message_id,
                    'ReceiptHandle': message.receipt_handle
                })

        if len(messages_to_delete) == 0:
            break
        else:
            print(message_bodies[0].get('Records')[0].get('s3').get('object').get('key'))
            s3 = boto3.client('s3')
            result = s3.get_object(Bucket=BUCKET_NAME, Key=CONFIG_FILE_KEY)
            ec2_config = json.loads(result["Body"].read().decode())
            ec2 = boto3.client('ec2', region_name=ec2_config['region'])

            result = launch_instance(ec2, ec2_config)
            print(f"[INFO] LAUNCHED EC2 instance-id '{result[0]}'")
            queue.delete_messages(
                Entries=messages_to_delete)


if __name__ == '__main__':
    create_instances()
