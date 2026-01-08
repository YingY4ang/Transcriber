from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import json
import os
from uuid import uuid4

app = Flask(__name__)
CORS(app)

# AWS clients
s3 = boto3.client('s3', region_name='ap-southeast-2')
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
sqs = boto3.client('sqs', region_name='ap-southeast-2')

BUCKET = 'clinical-audio-uploads'
TABLE = 'clinical-results'
QUEUE_URL = 'https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue'

@app.route('/get-upload-url')
def get_upload_url():
    patient_id = request.args.get('patientId', 'unknown')
    key = f"uploads/{patient_id}_{uuid4()}.webm"
    
    try:
        url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': BUCKET, 'Key': key},
            ExpiresIn=3600,
            HttpMethod='PUT'
        )
        return jsonify({'upload_url': url, 'key': key})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload-complete', methods=['POST'])
def upload_complete():
    data = request.json
    key = data.get('key')
    
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
        
        return jsonify({'status': 'processing triggered'})
    
    return jsonify({'error': 'key required'}), 400

@app.route('/result/<path:key>')
def get_result(key):
    import urllib.parse
    key = urllib.parse.unquote(key)
    
    table = dynamodb.Table(TABLE)
    resp = table.get_item(Key={'audio_key': key})
    
    if 'Item' in resp:
        return jsonify(resp['Item'])
    return jsonify({'status': 'processing'}), 404

@app.route('/config')
def get_config():
    return jsonify({
        'websocketUrl': 'wss://cmxbu5k037.execute-api.ap-southeast-2.amazonaws.com/prod'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
