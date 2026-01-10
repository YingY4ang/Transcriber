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

BUCKET = 'clinical-audio-bucket'
TABLE = 'clinical-results'
QUEUE_URL = 'https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue'

@app.route('/get-upload-url')
def get_upload_url():
    patient_id = request.args.get('patientId', 'unknown')
    key = f"uploads/{patient_id}_{uuid4()}.webm"
    
    try:
        url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET, 
                'Key': key,
                'ContentType': 'application/octet-stream'
            },
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

@app.route('/ai-summary', methods=['POST'])
def generate_ai_summary():
    try:
        data = request.json
        patient_data = data.get('patientData', {})
        
        # Build comprehensive patient summary for AI
        summary_text = build_patient_summary(patient_data)
        
        # Send to Bedrock for AI analysis
        prompt = f"""Analyze this patient's medical history and provide a concise clinical summary highlighting:
1. Key medical conditions and their status
2. Current medications and potential interactions
3. Recent healthcare encounters and trends
4. Risk factors and clinical concerns
5. Recommendations for ongoing care

Patient Data:
{summary_text}

Provide a professional clinical summary in 2-3 paragraphs:"""

        bedrock = boto3.client('bedrock-runtime', region_name='ap-southeast-2')
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1024,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        ai_response = json.loads(response['body'].read())
        summary = ai_response['content'][0]['text']
        
        return jsonify({'summary': summary})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def build_patient_summary(patient_data):
    """Build comprehensive text summary from FHIR data"""
    summary_parts = []
    
    # Patient demographics
    patient = patient_data.get('patient', {})
    if patient:
        summary_parts.append(f"Patient: {patient.get('name', [{}])[0].get('given', [''])[0]} {patient.get('name', [{}])[0].get('family', '')}")
        if patient.get('birthDate'):
            summary_parts.append(f"DOB: {patient['birthDate']}")
        if patient.get('gender'):
            summary_parts.append(f"Gender: {patient['gender']}")
    
    # Current conditions
    conditions = patient_data.get('conditions', [])
    if conditions:
        summary_parts.append("\nActive Conditions:")
        for entry in conditions:
            condition = entry.get('resource', {})
            condition_name = condition.get('code', {}).get('text', 'Unknown condition')
            summary_parts.append(f"- {condition_name}")
    
    # Current medications
    medications = patient_data.get('medications', [])
    if medications:
        summary_parts.append("\nCurrent Medications:")
        for entry in medications:
            med = entry.get('resource', {})
            med_name = med.get('medicationCodeableConcept', {}).get('text', 'Unknown medication')
            med_date = med.get('authoredOn', '')
            summary_parts.append(f"- {med_name} (started: {med_date})")
    
    # Recent encounters
    encounters = patient_data.get('encounters', [])
    if encounters:
        summary_parts.append("\nRecent Encounters:")
        for entry in encounters[-5:]:  # Last 5 encounters
            encounter = entry.get('resource', {})
            encounter_type = encounter.get('type', [{}])[0].get('text', 'Clinical encounter')
            encounter_date = encounter.get('period', {}).get('start', '')
            summary_parts.append(f"- {encounter_type} ({encounter_date})")
    
    return '\n'.join(summary_parts)

@app.route('/config')
def get_config():
    return jsonify({
        'websocketUrl': 'wss://cmxbu5k037.execute-api.ap-southeast-2.amazonaws.com/prod'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
