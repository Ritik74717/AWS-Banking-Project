import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Your-Table-Name')

def lambda_handler(event, context):
    # Get the connection ID from the event
    connection_id = event['requestContext']['connectionId']
    
    # Query DynamoDB to get the corresponding email_id using the connectionId
    response = table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('connectionId').eq(connection_id)
    )
    
    # If a matching item is found, delete the item based on email_id
    if response['Items']:
        email_id = response['Items'][0]['email_id']
        
        # Delete the item using email_id (partition key)
        table.delete_item(
            Key={
                'email_id': email_id
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Disconnected successfully and deleted connection for {email_id}')
        }
    
    # If no matching connection found
    return {
        'statusCode': 404,
        'body': json.dumps('Connection ID not found')
    }
