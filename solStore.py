import boto3
import requests
from requests.structures import CaseInsensitiveDict
import os
import tempfile
import re
import json

s3 = boto3.client('s3')
sqs = boto3.client('sqs')

def lambda_handler(event, context):
    # Get the input from the event payload
    url = event['url']
    bucket_prefix = event['bucket_prefix']
    consumer_key = event['consumer_key'].lower()
    zoom_api_token = event['zoom_api_token']
    
    # Create the bucket if it doesn't exist
    bucket_name = f'{consumer_key}-{bucket_prefix}'
    try:
        s3.head_bucket(Bucket=bucket_name)
    except:
        s3.create_bucket(Bucket=bucket_name)
    
    # Get the new download URL using Zoom API credentials
    headers = CaseInsensitiveDict()
    headers["Authorization"] = f"Bearer {zoom_api_token}"
    response = requests.get(url, headers=headers)
    
    # Download the file
    response.raise_for_status()
    with tempfile.NamedTemporaryFile() as fp:
        for chunk in response.iter_content(chunk_size=8192):
            fp.write(chunk)
        fp.seek(0)
        
        # Upload the file to S3
        file_key = os.path.basename(url)
        
        # Sanitize the file name by replacing periods with underscores
        sanitized_file_key = file_key.replace('.', '_') + ".mp4"
        
        s3.upload_fileobj(fp, bucket_name, sanitized_file_key)
    
    # Generate a presigned URL for the uploaded file
    presigned_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': sanitized_file_key},
        ExpiresIn=3600
    )
    
    # Publish the presigned URL to the solTranscribe SQS queue
    queue_url = 'https://sqs.us-east-1.amazonaws.com/215555180754/solTranscribe'
    message_body = {
        'responsePayload': {
            'body': {
                'presigned_url': presigned_url
            }
        }
    }
    response = sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message_body))
    print(f"Published message to SQS: {response['MessageId']}")
    
    return {
        'statusCode': 200,
        'body': {
            'presigned_url': presigned_url
        }
    }
