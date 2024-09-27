import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Your-Table-Name')

def lambda_handler(event, context):
    # Get the connection ID from the event
    connection_id = event['requestContext']['connectionId']
    
    # Parse query string parameters (assuming email_id is passed in the query parameters during WebSocket connection)
    email_id = event['queryStringParameters'].get('email_id')
    
    if not email_id:
        return {
            'statusCode': 400,
            'body': json.dumps('email_id is required')
        }

    # Store the connection ID and email_id in DynamoDB
    table.put_item(
        Item={
            'email_id': email_id,           # Partition key
            'connectionId': connection_id   # Store connectionId
        }
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Connection successful')
    }
