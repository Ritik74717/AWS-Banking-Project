import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
banking_table = dynamodb.Table('Your-banking-Table-Name')
connections_table = dynamodb.Table('Your-websocket-Table-Name')

# Create a client to interact with API Gateway WebSockets
apigateway_client = boto3.client('apigatewaymanagementapi', endpoint_url="https://yourwebsocketurl")

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
    # Parse the connection ID and input parameters from the WebSocket message
    connection_id = event['requestContext']['connectionId']
    body = json.loads(event['body'])

    sender_email = body['sender_email']
    recipient_email = body['recipient_email']
    transfer_amount = Decimal(body['amount'])  # Amount to be transferred

    # Fetch current balance of sender
    sender_item = banking_table.get_item(Key={'email_id': sender_email})
    if 'Item' not in sender_item:
        send_message(connection_id, {'status': 'error', 'message': 'Sender email ID not found'})
        return {'statusCode': 404, 'body': json.dumps('Sender email ID not found')}
    
    # Fetch current balance of recipient
    recipient_item = banking_table.get_item(Key={'email_id': recipient_email})
    if 'Item' not in recipient_item:
        send_message(connection_id, {'status': 'error', 'message': 'Recipient email ID not found'})
        return {'statusCode': 404, 'body': json.dumps('Recipient email ID not found')}

    # Convert balance to Decimal for calculations
    sender_balance = Decimal(sender_item['Item']['balance'])
    recipient_balance = Decimal(recipient_item['Item']['balance'])

    # Check if sender has sufficient balance
    if sender_balance < transfer_amount:
        send_message(connection_id, {'status': 'error', 'message': 'Insufficient balance'})
        return {'statusCode': 400, 'body': json.dumps('Insufficient balance')}
    
    # Update balances
    new_sender_balance = str(sender_balance - transfer_amount)  # Convert back to string for DynamoDB
    new_recipient_balance = str(recipient_balance + transfer_amount)

    # Update the sender's balance in DynamoDB
    banking_table.update_item(
        Key={'email_id': sender_email},
        UpdateExpression="SET #balance = :new_balance",
        ExpressionAttributeNames={
            '#balance': 'balance'
        },
        ExpressionAttributeValues={
            ':new_balance': new_sender_balance
        }
    )

    # Update the recipient's balance in DynamoDB
    banking_table.update_item(
        Key={'email_id': recipient_email},
        UpdateExpression="SET #balance = :new_balance",
        ExpressionAttributeNames={
            '#balance': 'balance'
        },
        ExpressionAttributeValues={
            ':new_balance': new_recipient_balance
        }
    )

    # Notify the sender of successful transaction
    send_message(connection_id, {
        'status': 'success',
        'message': f'Successfully transferred {transfer_amount} from {sender_email} to {recipient_email}',
        'new_sender_balance': new_sender_balance,
        'new_recipient_balance': new_recipient_balance
    })

    # Retrieve the recipient's WebSocket connection ID from the connections table
    recipient_conn = connections_table.get_item(Key={'email_id': recipient_email})
    
    if 'Item' in recipient_conn:
        recipient_connection_id = recipient_conn['Item']['connectionId']  # Get the connectionId
        
        # Notify the recipient of the received money
        send_message(recipient_connection_id, {
            'status': 'success',
            'message': f'You received {transfer_amount} from {sender_email}',
            'new_balance': new_recipient_balance
        })
    else:
        print(f"Recipient {recipient_email} has no active WebSocket connection")

    # Return a success response for the API
    return {
        'statusCode': 200,
        'body': json.dumps('Transaction completed successfully')
    }
