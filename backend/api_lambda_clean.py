import json
import os
import boto3
from uuid import uuid4

REGION = 'ap-southeast-2'
s3 = boto3.client('s3', 
    region_name=REGION, 
    config=boto3.session.Config(
        region_name=REGION,
        signature_version='s3v4',
        s3={'addressing_style': 'virtual'}
    )
)
sqs = boto3.client('sqs', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)

BUCKET = os.environ['BUCKET_NAME']
TABLE = os.environ['TABLE_NAME']
QUEUE_URL = 'https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue'

def handler(event, context):
    path = event.get('rawPath', '')
    method = event.get('requestContext', {}).get('http', {}).get('method', '')
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers}
    
    # GET /config - Return configuration
    if path == '/config':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'websocketUrl': 'wss://cmxbu5k037.execute-api.ap-southeast-2.amazonaws.com/prod'
            })
        }
    
    # POST /upload-complete - Trigger processing after successful upload
    if path == '/upload-complete' and method == 'POST':
        try:
            body = json.loads(event.get('body', '{}'))
            key = body.get('key')
            
            if key:
                # Send SQS message to trigger processing
                message = {
                    'Records': [{
                        's3': {
                            'bucket': {'name': BUCKET},
                            'object': {'key': key}
                        }
                    }]
                }
                
                sqs.send_message(
                    QueueUrl=QUEUE_URL,
                    MessageBody=json.dumps(message)
                )
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({'status': 'processing triggered'})
                }
            
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'key required'})
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': str(e)})
            }
    
    # GET /get-upload-url
    if path == '/get-upload-url':
        patient_id = event.get('queryStringParameters', {}).get('patientId', 'unknown')
        key = f"uploads/test_{uuid4()}.webm"
        
        try:
            url = s3.generate_presigned_url(
                'put_object',
                Params={'Bucket': BUCKET, 'Key': key},
                ExpiresIn=3600,
                HttpMethod='PUT'
            )
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'upload_url': url, 'key': key})
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': str(e)})
            }
    
    # GET /result/{key}
    if path.startswith('/result/'):
        key = path.replace('/result/', '')
        # Decode URL encoding properly
        import urllib.parse
        key = urllib.parse.unquote(key)
        print(f"Looking for key: {key}")  # Debug log
        
        table = dynamodb.Table(TABLE)
        resp = table.get_item(Key={'audio_key': key})
        
        if 'Item' in resp:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(resp['Item'])
            }
        return {'statusCode': 404, 'headers': headers, 'body': '{"status": "processing"}'}
    
    return {'statusCode': 404, 'headers': headers, 'body': '{"error": "not found"}'}
