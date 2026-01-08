import json, os, boto3, time
from openai import OpenAI

def generate_fhir_bundle(patient_id, encounter_id, extracted_data, transcript):
    """Generate FHIR R4 Bundle with NZ extensions"""
    bundle = {
        "resourceType": "Bundle",
        "id": encounter_id.replace('/', '-'),
        "type": "collection",
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S+12:00'),
        "entry": []
    }
    
    # Patient resource with NHI
    patient = {
        "resource": {
            "resourceType": "Patient",
            "id": f"patient-{patient_id}",
            "identifier": [{
                "use": "official",
                "system": "https://standards.digital.health.nz/ns/nhi-id",
                "value": patient_id
            }]
        }
    }
    bundle["entry"].append(patient)
    
    # Encounter resource
    encounter = {
        "resource": {
            "resourceType": "Encounter",
            "id": f"encounter-{encounter_id.replace('/', '-')}",
            "status": "finished",
            "class": {"code": "AMB", "display": "ambulatory"},
            "subject": {"reference": f"Patient/patient-{patient_id}"},
            "period": {"start": time.strftime('%Y-%m-%dT%H:%M:%S+12:00')}
        }
    }
    bundle["entry"].append(encounter)
    
    # Conditions from diagnosis
    if extracted_data.get('diagnosis') and extracted_data['diagnosis'] != 'string':
        condition = {
            "resource": {
                "resourceType": "Condition",
                "id": f"condition-{len(bundle['entry'])}",
                "subject": {"reference": f"Patient/patient-{patient_id}"},
                "encounter": {"reference": f"Encounter/encounter-{encounter_id.replace('/', '-')}"},
                "code": {"text": extracted_data['diagnosis']},
                "clinicalStatus": {"coding": [{"code": "active"}]}
            }
        }
        bundle["entry"].append(condition)
    
    # Medications
    for i, med in enumerate(extracted_data.get('medications', [])):
        if med and med != 'string':
            medication = {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": f"medication-{i}",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": f"Patient/patient-{patient_id}"},
                    "encounter": {"reference": f"Encounter/encounter-{encounter_id.replace('/', '-')}"},
                    "medicationCodeableConcept": {"text": med}
                }
            }
            bundle["entry"].append(medication)
    
    # Vital signs as Observations
    vitals = extracted_data.get('vital_signs', {})
    for vital_type, value in vitals.items():
        if value and value != 'string':
            observation = {
                "resource": {
                    "resourceType": "Observation",
                    "id": f"vital-{vital_type}",
                    "status": "final",
                    "category": [{"coding": [{"code": "vital-signs"}]}],
                    "subject": {"reference": f"Patient/patient-{patient_id}"},
                    "encounter": {"reference": f"Encounter/encounter-{encounter_id.replace('/', '-')}"},
                    "code": {"text": vital_type.upper()},
                    "valueString": str(value)
                }
            }
            bundle["entry"].append(observation)
    
    # Tasks as ServiceRequests
    for i, task in enumerate(extracted_data.get('tasks', [])):
        if task and task not in ['task1', 'task2', 'string']:
            service_request = {
                "resource": {
                    "resourceType": "ServiceRequest",
                    "id": f"task-{i}",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": f"Patient/patient-{patient_id}"},
                    "encounter": {"reference": f"Encounter/encounter-{encounter_id.replace('/', '-')}"},
                    "code": {"text": task}
                }
            }
            bundle["entry"].append(service_request)
    
    # Clinical notes as DocumentReference
    if transcript:
        document = {
            "resource": {
                "resourceType": "DocumentReference",
                "id": "clinical-transcript",
                "status": "current",
                "subject": {"reference": f"Patient/patient-{patient_id}"},
                "context": {"encounter": [{"reference": f"Encounter/encounter-{encounter_id.replace('/', '-')}"}]},
                "content": [{
                    "attachment": {
                        "contentType": "text/plain",
                        "data": transcript
                    }
                }]
            }
        }
        bundle["entry"].append(document)
    
    return bundle

REGION = os.environ.get('AWS_REGION', 'ap-southeast-2')
QUEUE_URL = os.environ.get('QUEUE_URL', 'https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue')
TABLE = os.environ.get('TABLE_NAME', 'clinical-results')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

sqs = boto3.client('sqs', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
bedrock = boto3.client('bedrock-runtime', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

print("Ready!")
print("Waiting for requests....")

while True:
    resp = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=1, WaitTimeSeconds=20)
    print(f"SQS Response: {resp.get('ResponseMetadata', {}).get('RequestId', 'No RequestId')}")
    if 'Messages' in resp:
        print(f"Found {len(resp['Messages'])} message(s)")
    else:
        print("No messages in queue")
    for msg in resp.get('Messages', []):
        try:
            body = json.loads(msg['Body'])
            bucket = body['Records'][0]['s3']['bucket']['name']
            key = body['Records'][0]['s3']['object']['key']
            print(f"Processing: {key}")
            
            # Check if file exists before processing
            try:
                s3.head_object(Bucket=bucket, Key=key)
            except Exception as e:
                print(f"File already processed or not found: {key} - {e}")
                sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg['ReceiptHandle'])
                continue
            
            # Extract patient ID from S3 key
            patient_id = key.split('/')[-1].split('_')[0] if '_' in key else 'unknown'
            
            local = f"/tmp/{os.path.basename(key)}"
            s3.download_file(bucket, key, local)
            
            with open(local, "rb") as audio_file:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                ).text
            print(f"Transcript: {transcript[:100]}...")
            
            prompt = """Extract clinical data and return ONLY valid JSON in this format:
{
  "tasks": ["task1", "task2"],
  "diagnosis": "condition name",
  "medications": ["med1", "med2"],
  "follow_up": "follow up plan",
  "notes": "additional notes",
  "vital_signs": {"bp": "120/80", "hr": "72", "temp": "36.5"},
  "symptoms": ["symptom1", "symptom2"]
}

Clinical transcript: """ + transcript
            
            try:
                resp_ai = bedrock.invoke_model(
                    modelId='anthropic.claude-3-haiku-20240307-v1:0',
                    body=json.dumps({
                        'anthropic_version': 'bedrock-2023-05-31',
                        'max_tokens': 1024,
                        'messages': [{'role': 'user', 'content': prompt}]
                    })
                )
                import re
                ai_text = json.loads(resp_ai['body'].read())['content'][0]['text']
                match = re.search(r'\{.*\}', ai_text, re.DOTALL)
                extracted = json.loads(match.group()) if match else {"notes": ai_text}
                
                # Generate FHIR resources
                fhir_bundle = generate_fhir_bundle(patient_id, key, extracted, transcript)
                
            except Exception as e:
                print(f"Bedrock error: {e}")
                extracted = {"notes": "extraction failed"}
                fhir_bundle = None
            
            dynamodb.Table(TABLE).put_item(Item={
                'audio_key': key, 
                'patient_id': patient_id,
                'transcript': transcript, 
                'timestamp': int(time.time()),
                'fhir_bundle': fhir_bundle,
                **extracted
            })
            
            # Send WebSocket notification
            try:
                print("Attempting WebSocket notification...")
                apigateway = boto3.client('apigatewaymanagementapi',
                    endpoint_url='https://cmxbu5k037.execute-api.ap-southeast-2.amazonaws.com/prod',
                    region_name=REGION
                )
                
                # Get connections subscribed to this audio key
                connections_table = dynamodb.Table('websocket-connections')
                print(f"Scanning for connections with audioKey: {key}")
                response = connections_table.scan(
                    FilterExpression='audioKey = :key',
                    ExpressionAttributeValues={':key': key}
                )
                print(f"Found {len(response['Items'])} connections")
                
                # Send completion notification to all subscribers
                for item in response['Items']:
                    try:
                        apigateway.post_to_connection(
                            ConnectionId=item['connectionId'],
                            Data=json.dumps({
                                'type': 'completed',
                                'audioKey': key,
                                'result': {
                                    'transcript': transcript,
                                    'fhir_bundle': fhir_bundle,
                                    **extracted
                                }
                            })
                        )
                        print(f"Sent notification to connection: {item['connectionId']}")
                    except Exception as conn_error:
                        print(f"Failed to send to connection {item['connectionId']}: {conn_error}")
                        pass
            except Exception as e:
                print(f"WebSocket notification error: {e}")
                import traceback
                traceback.print_exc()
            
            s3.delete_object(Bucket=bucket, Key=key)
            os.remove(local)
            sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg['ReceiptHandle'])
            print(f"Done: {key}")
        except Exception as e:
            print(f"Error processing message: {e}")
            print(f"Message body: {msg.get('Body', 'No body')}")
            import traceback
            traceback.print_exc()
