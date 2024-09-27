import json
import boto3

dynamodb = boto3.resource('dynamodb')
banking_table = dynamodb.Table('Your-banking-Table-Name')
connections_table = dynamodb.Table('Your-websocket-Table-Name')

# Create a client to interact with API Gateway WebSockets
apigateway_client = boto3.client('apigatewaymanagementapi', 
                                 endpoint_url="https://yourwebsocketurl")

def send_message(connection_id, message):
    """Send a message back to the WebSocket client"""
    try:
        apigateway_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
    except Exception as e:
        print(f"Error sending message to {connection_id}: {e}")


def lambda_handler(event, context):
    
    # print(event)
    # sender_email = event['sender_email']
    body = json.loads(event['body'])
    sender_email = body['sender_email']
    
    # Fetch current balance of sender
    sender_item = banking_table.get_item(Key={'email_id': sender_email})
    
    if 'Item' not in sender_item:
        # Send an error message back if the sender is not found
        send_message(event['requestContext']['connectionId'], {'status': 'error', 'message': 'Sender email ID not found'})
        return {'statusCode': 404, 'body': json.dumps('Sender email ID not found')}
        
    # Convert balance to Decimal for calculations
    sender_balance = str(sender_item['Item']['balance'])
    
    # Retrieve the recipient's WebSocket connection ID from the connections table
    recipient_conn = connections_table.get_item(Key={'email_id': sender_email})
    
    # Check if the recipient has an active WebSocket connection
    if 'Item' in recipient_conn:
        recipient_connection_id = recipient_conn['Item']['connectionId']  # Get the connectionId
        
        # Notify the recipient of the received money
        send_message(recipient_connection_id, {
            'status': 'success',
            'new_balance': sender_balance
        })
    else:
        print(f"Recipient {sender_email} has no active WebSocket connection")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Sender Balance Received')
    }
