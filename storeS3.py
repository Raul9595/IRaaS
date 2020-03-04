import boto3

REGION_NAME = "us-east-1"
s3 = boto3.resource('s3')
s3BucketName = 'image-rec-512'
path = 'BTS1.mp4'
put_into_bucket = True

for my_bucket_object in s3.Bucket(s3BucketName).objects.filter(Prefix='input/'):
    if path[5:] in my_bucket_object.key:
        put_into_bucket = False
        break

if put_into_bucket:
    s3.Bucket(s3BucketName).upload_file(path, 'input/' + path[5:],
                                        ExtraArgs={"ACL": "public-read", "ContentType": "video/h264"})

