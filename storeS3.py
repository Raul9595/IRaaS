import boto3
import os
import subprocess


def uploadDirectory(path, s3, bucketname):
    for root, dirs, files in os.walk(path):
        for file in files:
            s3.Bucket(bucketname).upload_file(os.path.join(root, file), 'input/' + file,
                                              ExtraArgs={"ACL": "public-read",
                                                         "ContentType": "video/h264"})
            print('{0} is inserted into the database'.format(file))
            subprocess.call(['rm', file])


def main():
    s3 = boto3.resource('s3')
    s3BucketName = 'image-rec-512'
    # Local folder path
    path = '/home/pi/iraas/data'
    # Upload all the files from the path
    uploadDirectory(path, s3, s3BucketName)
