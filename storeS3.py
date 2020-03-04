import boto3
import os


def uploadDirectory(path, s3, bucketname):
    for root, dirs, files in os.walk(path):
        for file in files:
            put_into_bucket = True

            # Check if the file exists in the bucket already
            for my_bucket_object in s3.Bucket(bucketname).objects.filter(Prefix='input/'):
                if file in my_bucket_object.key:
                    put_into_bucket = False
                    break

            # Put into bucket if the file does not exist in the s3 database
            if put_into_bucket:
                s3.Bucket(bucketname).upload_file(os.path.join(root, file), 'input/' + file,
                                                    ExtraArgs={"ACL": "public-read", "ContentType": "video/h264"})


if __name__ == '__main__':
    s3 = boto3.resource('s3')
    s3BucketName = 'image-rec-512'
    # Local folder path
    path = 'data'
    # Upload all the files from the path
    uploadDirectory(path, s3, s3BucketName)
