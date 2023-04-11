import requests
import base64
import os

def lambda_handler(event, context):
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        "content-type": "multipart/form-data"
    }

    # decode the file content from base64
    file_content = base64.b64decode(event['file_content'])

    # create the multipart-encoded data as a dictionary
    data = {
        "model": "whisper-1"
    }

    # add the file to the data dictionary
    files = {
        'file': ('file.wav', file_content, 'audio/wav')
    }

    # send the request
    response = requests.post(url, headers=headers, data=data, files=files)

    # parse the response
    if response.ok:
        transcript = response.json()['data'][0]['text']
        return {
            "statusCode": 200,
            "body": transcript
        }
    else:
        error_message = response.json()['error']['message']
        return {
            "statusCode": response.status_code,
            "body": f"Error: {error_message}"
        }
