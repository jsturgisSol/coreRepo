import os
import boto3
import requests

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Get the URL of the audio file from the request body
    url = event['url']

    # Get the consumer key from the request body
    consumer_key = event['consumer_key']

    # Get the bucket prefix from the request body
    bucket_prefix = event['bucket_prefix']

    # Create an S3 bucket with the given bucket prefix and consumer key if it doesn't already exist
    bucket_name = f'{bucket_prefix}-{consumer_key}'
    if s3.list_buckets()['Buckets'] == [] or bucket_name not in [bucket['Name'] for bucket in s3.list_buckets()['Buckets']]:
        s3.create_bucket(Bucket=bucket_name)

    # Get the file name from the URL
    file_name = url.split('/')[-1]

    # Download the file to S3
    s3.download_file(bucket_name, file_name, f'/tmp/{file_name}')

    # Create a presigned URL for the downloaded file
    presigned_url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': bucket_name,
            'Key': file_name
        }
    )

    # Send the presigned URL back in the response body
    return {
        'statusCode': 200,
        'body': presigned_url
    }