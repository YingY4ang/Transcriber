import json
import os
import boto3
from uuid import uuid4

REGION = 'ap-southeast-2'
# Use default credentials without specifying config
s3 = boto3.client('s3', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)

BUCKET = os.environ['BUCKET_NAME']
TABLE = os.environ['TABLE_NAME']

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
    
    # POST /upload - Handle file upload through API
    if path == '/upload' and method == 'POST':
        try:
            import base64
            patient_id = event.get('queryStringParameters', {}).get('patientId', 'unknown')
            
            # Get file data from request body
            body = event.get('body', '')
            if event.get('isBase64Encoded'):
                file_data = base64.b64decode(body)
            else:
                file_data = body if isinstance(body, bytes) else body.encode()
            
            # Upload to S3
            key = f"uploads/{patient_id}_{uuid4()}.webm"
            s3.put_object(Bucket=BUCKET, Key=key, Body=file_data, ContentType='audio/webm')
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'key': key, 'status': 'uploaded'})
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
        key = f"uploads/{patient_id}_{uuid4()}.webm"
        url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': BUCKET, 'Key': key},
            ExpiresIn=3600,  # 1 hour
            HttpMethod='PUT'
        )
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'upload_url': url, 'key': key})
        }
    
    # GET /result/{key}
    if path.startswith('/result/'):
        key = path.replace('/result/', '')
        # Decode URL encoding
        import urllib.parse
        key = urllib.parse.unquote(key)
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
