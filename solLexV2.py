import json
import boto3

# Create a boto3 client for invoking Lambda functions
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    
    # Extract user input text from the event
    user_text = event['inputTranscript']
    
    # Invoke the SolChatGPT function with user input text
    chat_gpt_payload = {
        'body-json': {
            'key1': user_text
        }
    }
    chat_gpt_response = lambda_client.invoke(
        FunctionName='SolChatGPT',
        Payload=json.dumps(chat_gpt_payload)
    )
    
    # Extract the response message from the SolChatGPT function
    chat_gpt_response_payload = json.loads(chat_gpt_response['Payload'].read().decode('utf-8'))
    response_message = chat_gpt_response_payload['response']['choices'][0]['message']['content']
    
    # Construct the response message for Lex
    lex_response = {
        'sessionState': {
            'dialogAction': {
                'type': 'Close',
                'fulfillmentState': 'Fulfilled',
                'message': {
                    'contentType': 'PlainText',
                    'content': response_message
                }
            },
            'intent': {
                'name': event['currentIntent']['name'],
                'state': 'Fulfilled',
                'confirmationState': 'None',
                'slots': event['currentIntent']['slots']
            },
            'sessionAttributes': event['sessionAttributes'],
        },
        'messages': [],
        'requestAttributes': {}
    }
    return lex_response
