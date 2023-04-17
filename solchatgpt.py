import requests
import boto3
import json
import os
import re

# API endpoint URL
endpoint_url = "https://api.openai.com/v1/chat/completions"

# Set openai model
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
    
    # Ensure key1 is a string
    if not isinstance(key1, str):
        key1 = str(key1)
    
    # Connect to S3
    s3 = boto3.client('s3')
    
    # Retrieve the conversation history from S3
    try:
        obj = s3.get_object(Bucket=os.environ['S3_BUCKET_NAME'], Key='conversation_history.json')
        history = json.loads(obj['Body'].read().decode('utf-8'))
    except:
        history = []

    save_thread_pattern = re.compile(r'^save this thread as (.+)$', re.IGNORECASE)
    save_thread_match = save_thread_pattern.match(key1)

    if key1.lower() == "end thread":
        # Delete the conversation history from S3
        s3.delete_object(Bucket=os.environ['S3_BUCKET_NAME'], Key='conversation_history.json')
        
        response_text = "Thank you, this thread has been terminated"
    elif save_thread_match:
        filename = save_thread_match.group(1).strip() + '.json'

        # Save the conversation history in S3 as {{variable}}.json
        s3.put_object(Bucket=os.environ['S3_BUCKET_NAME'], Key=filename, Body=json.dumps(history))

        response_text = f"Conversation history has been saved as {filename}"
    else:
        # Add the new message to the history
        history.append({"role": "user", "content": key1})
        
        # Update the request body with the conversation history
        request_body["messages"] = history
        
        # Send the request to the API endpoint
        headers = {
            'Authorization': 'Bearer ' + os.environ['API_KEY']
        }
        response = requests.post(endpoint_url, json=request_body, headers=headers)
        
        response_json = response.json()

        if "choices" in response_json:
            for choice in response_json["choices"]:
                history.append(choice["message"])

            # Store the updated history in S3
            s3.put_object(Bucket=os.environ['S3_BUCKET_NAME'], Key='conversation_history.json', Body=json.dumps(history))
            response_text = response_json["choices"][0]["message"]["content"]
        else:
            response_text = "An error occurred while processing your request. Please try again."
            if "error" in response_json:
                print(f"Error: {response_json['error']}")

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
                        "content": response_text
                    },
                    "finish_reason": "",
                    "index": 0
                }
            ]
        }
        }
