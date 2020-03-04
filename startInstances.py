import boto3
import json

BUCKET_NAME = "image-rec-512"
CONFIG_FILE_KEY = "config/config.json"
BUCKET_INPUT_DIR = "input"
BUCKET_OUTPUT_DIR = "output"


def launch_instance(ec2, config):
    # EC2 Instance Configuration details
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
    # Queue instance which retrieves all the messages
    sqs = boto3.resource('sqs')
    queue_name = 'ImageRec'
    max_queue_messages = 10

    queue = sqs.get_queue_by_name(QueueName=queue_name)
    message_body = []

    # Get all the messages from queue and delete it once the instances are created for each message
    while True:
        delete_messages = []
        for message in queue.receive_messages(MaxNumberOfMessages=max_queue_messages):

            body = json.loads(message.body)
            message_body.append(body)
            # Get the message only if the message is created by the s3 instance
            if message_body[0].get('Records')[0].get('eventSource') == 'aws:s3':
                delete_messages.append({
                    'Id': message.message_id,
                    'ReceiptHandle': message.receipt_handle
                })

        # If there are no more messages in the queue, break
        if len(delete_messages) == 0:
            break
        else:
            # Launch instances for each sqs message
            s3 = boto3.client('s3')
            result = s3.get_object(Bucket=BUCKET_NAME, Key=CONFIG_FILE_KEY)
            ec2_config = json.loads(result["Body"].read().decode())
            ec2 = boto3.client('ec2', region_name=ec2_config['region'])

            result = launch_instance(ec2, ec2_config)
            # Print the location of the file in the bucket for the message
            print(message_body[0].get('Records')[0].get('s3').get('object').get('key'))
            print('Launched EC2 instance - '.format(result[0]))
            queue.delete_messages(Entries=delete_messages)


if __name__ == '__main__':
    create_instances()
