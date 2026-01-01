import json
import os
import boto3
from uuid import uuid4

REGION = 'ap-southeast-2'
s3 = boto3.client('s3', region_name=REGION, config=boto3.session.Config(s3={'addressing_style': 'virtual'}))
dynamodb = boto3.resource('dynamodb', region_name=REGION)

BUCKET = os.environ['BUCKET_NAME']
TABLE = os.environ['TABLE_NAME']

def handler(event, context):
    path = event.get('rawPath', '')
    method = event.get('requestContext', {}).get('http', {}).get('method', '')
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers}
    
    # GET /get-upload-url
    if path == '/get-upload-url':
        key = f"uploads/{uuid4()}.webm"
        url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': BUCKET, 'Key': key, 'ContentType': 'audio/webm'},
            ExpiresIn=300
        )
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'upload_url': url, 'key': key})
        }
    
    # GET /result/{key}
    if path.startswith('/result/'):
        key = path.replace('/result/', '').replace('%2F', '/')
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
