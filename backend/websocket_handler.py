import json
import boto3
import time

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
apigateway = boto3.client('apigatewaymanagementapi', 
    endpoint_url='https://cmxbu5k037.execute-api.ap-southeast-2.amazonaws.com/prod'
)

def handler(event, context):
    route_key = event.get('requestContext', {}).get('routeKey')
    connection_id = event.get('requestContext', {}).get('connectionId')
    
    if route_key == '$connect':
        # Store connection for later use
        table = dynamodb.Table('websocket-connections')
        table.put_item(Item={
            'connectionId': connection_id,
            'timestamp': int(time.time())
        })
        return {'statusCode': 200}
    
    elif route_key == '$disconnect':
        # Clean up connection
        table = dynamodb.Table('websocket-connections')
        table.delete_item(Key={'connectionId': connection_id})
        return {'statusCode': 200}
    
    elif route_key == 'subscribe':
        # Subscribe to specific audio key
        body = json.loads(event.get('body', '{}'))
        audio_key = body.get('audioKey')
        
        table = dynamodb.Table('websocket-connections')
        table.update_item(
            Key={'connectionId': connection_id},
            UpdateExpression='SET audioKey = :key',
            ExpressionAttributeValues={':key': audio_key}
        )
        return {'statusCode': 200}
    
    return {'statusCode': 404}
