import os
import requests
import boto3
import json

# API endpoint URL
endpoint_url = "https://api.openai.com/v1/chat/completions"

# set openai model
model = os.environ['OAI_MODEL']

# JSON request body format
request_body = {
  "model": model,
  "temperature": 0.5,
  "max_tokens": 1000,
  "messages": []
}

# Function to handle incoming events
def lambda_handler(event, context):
    # Extract key1 from the event
    key1 = event['body-json']['key1']
    #key1 = {
    #  "role": "user",
    #  "content": "create a soql statement to pull all records from the lead table"}
    #
    
    # Connect to S3
    s3 = boto3.client('s3')
    
    # Retrieve the conversation history from S3
    try:
        obj = s3.get_object(Bucket=os.environ['S3_BUCKET_NAME'], Key='conversation_history.json')
        history = json.loads(obj['Body'].read().decode('utf-8'))
    except:
        history = []

    if key1 == "end thread":
        # Connect to S3
        s3 = boto3.client('s3')
        
        # Delete the conversation history from S3
        s3.delete_object(Bucket=os.environ['S3_BUCKET_NAME'], Key='conversation_history.json')
        
        return {
    "conversation_history": history,
    "response": {
        "id": "",
        "object": "",
        "created": "",
        "model": "",
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        },
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Thank you, this thread has been terminated"
                },
                "finish_reason": "",
                "index": 0
            }
        ]
    }
}
    
    # Add the new message to the history
    history.append({"role": "user", "content": key1})
    
    # Update the request body with the conversation history
    request_body["messages"] = history
    
    # Send the request to the API endpoint
    headers = {
        'Authorization': 'Bearer ' + os.environ['API_KEY']
    }
    response = requests.post(endpoint_url, json=request_body, headers=headers)
    #print(response)
    #print(request_body)
    # Add the response from the API to the conversation history
    response_json = response.json()
    for choice in response_json["choices"]:
        history.append(choice["message"])
    
    # Store the updated history in S3
    s3.put_object(Bucket=os.environ['S3_BUCKET_NAME'], Key='conversation_history.json', Body=json.dumps(history))
    
    # Return the response from the API and the conversation history
    return {
        "conversation_history": history,
        "response": response_json
    }
