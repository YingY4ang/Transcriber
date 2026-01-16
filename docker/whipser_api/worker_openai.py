import json, os, boto3, time, sys
import librosa
import numpy as np
import soundfile as sf
from openai import OpenAI

# Add project modules to path
sys.path.insert(0, '/app')
from analysis.prompts.bedrock_prompt import get_bedrock_prompt
from storage.dynamodb.consultation_storage import prepare_consultation_item
from pdf.templates.consultation_pdf import generate_consultation_pdf

def remove_silence_vad(audio_file_path):
    """Remove silence from audio using VAD"""
    try:
        print(f"Applying VAD to: {audio_file_path}")
        
        # Load audio file
        y, sr = librosa.load(audio_file_path, sr=16000)  # Resample to 16kHz for consistency
        
        # Use librosa's voice activity detection
        # Split audio where silence is detected (top_db controls sensitivity)
        intervals = librosa.effects.split(y, top_db=20, frame_length=2048, hop_length=512)
        
        if len(intervals) == 0:
            print("No voice activity detected, keeping original audio")
            return audio_file_path
        
        # Extract voice segments
        voice_segments = []
        total_voice_duration = 0
        
        for start, end in intervals:
            segment = y[start:end]
            voice_segments.append(segment)
            total_voice_duration += len(segment) / sr
        
        # Concatenate all voice segments
        processed_audio = np.concatenate(voice_segments)
        
        # Save processed audio
        output_path = audio_file_path.replace('.webm', '_vad.wav')
        sf.write(output_path, processed_audio, sr)
        
        original_duration = len(y) / sr
        print(f"VAD processing complete:")
        print(f"  Original duration: {original_duration:.2f}s")
        print(f"  Voice duration: {total_voice_duration:.2f}s") 
        print(f"  Reduction: {((original_duration - total_voice_duration) / original_duration * 100):.1f}%")
        
        return output_path
        
    except Exception as e:
        print(f"VAD processing failed: {e}")
        return audio_file_path  # Return original if VAD fails

def generate_fhir_bundle(patient_id, encounter_id, consultation_artifact, transcript):
    """Generate FHIR R4 Bundle with NZ extensions from consultation artifact"""
    # Clean IDs to be FHIR compliant (alphanumeric only)
    clean_encounter_id = ''.join(c for c in encounter_id if c.isalnum())
    clean_patient_id = ''.join(c for c in patient_id if c.isalnum())
    
    # Extract data from artifact
    soap = consultation_artifact.get('soap_notes', {})
    subjective = soap.get('subjective', {})
    objective = soap.get('objective', {})
    assessment = soap.get('assessment', {})
    plan = soap.get('plan', {})
    
    bundle = {
        "resourceType": "Bundle",
        "id": clean_encounter_id,
        "type": "transaction",
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S+12:00'),
        "entry": []
    }
    
    # Patient resource with NHI
    patient = {
        "resource": {
            "resourceType": "Patient",
            "id": f"patient-{clean_patient_id}",
            "identifier": [{
                "use": "official",
                "system": "https://standards.digital.health.nz/ns/nhi-id",
                "value": patient_id
            }]
        },
        "request": {
            "method": "PUT",
            "url": f"Patient/patient-{clean_patient_id}"
        }
    }
    bundle["entry"].append(patient)
    
    # Encounter resource
    encounter = {
        "resource": {
            "resourceType": "Encounter",
            "id": f"encounter-{clean_encounter_id}",
            "status": "finished",
            "class": {"code": "AMB", "display": "ambulatory"},
            "subject": {"reference": f"Patient/patient-{clean_patient_id}"},
            "period": {"start": time.strftime('%Y-%m-%dT%H:%M:%S+12:00')}
        },
        "request": {
            "method": "PUT",
            "url": f"Encounter/encounter-{clean_encounter_id}"
        }
    }
    bundle["entry"].append(encounter)
    
    # Conditions from assessment
    primary_dx = assessment.get('primary_diagnosis')
    if primary_dx:
        condition = {
            "resource": {
                "resourceType": "Condition",
                "id": f"condition-primary",
                "subject": {"reference": f"Patient/patient-{clean_patient_id}"},
                "encounter": {"reference": f"Encounter/encounter-{clean_encounter_id}"},
                "code": {"text": primary_dx},
                "clinicalStatus": {"coding": [{"code": "active"}]}
            },
            "request": {
                "method": "POST",
                "url": "Condition"
            }
        }
        bundle["entry"].append(condition)
    
    # Medications from plan
    for i, med in enumerate(plan.get('medications_prescribed', [])):
        if med.get('medication'):
            medication = {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": f"medication-{i}",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": f"Patient/patient-{clean_patient_id}"},
                    "encounter": {"reference": f"Encounter/encounter-{clean_encounter_id}"},
                    "medicationCodeableConcept": {
                        "text": f"{med['medication']} {med.get('dose', '')} {med.get('route', '')} {med.get('frequency', '')}"
                    }
                },
                "request": {
                    "method": "POST",
                    "url": "MedicationRequest"
                }
            }
            bundle["entry"].append(medication)
    
    # Vital signs as Observations
    vitals = objective.get('vital_signs', {})
    for vital_type, value in vitals.items():
        if value:
            observation = {
                "resource": {
                    "resourceType": "Observation",
                    "id": f"vital-{vital_type}",
                    "status": "final",
                    "category": [{"coding": [{"code": "vital-signs"}]}],
                    "subject": {"reference": f"Patient/patient-{clean_patient_id}"},
                    "encounter": {"reference": f"Encounter/encounter-{clean_encounter_id}"},
                    "code": {"text": vital_type.replace('_', ' ').upper()},
                    "valueString": str(value)
                },
                "request": {
                    "method": "POST",
                    "url": "Observation"
                }
            }
            bundle["entry"].append(observation)
    
    # Tasks as ServiceRequests
    tasks = consultation_artifact.get('follow_up_tasks', [])
    for i, task in enumerate(tasks[:10]):  # Limit to first 10 tasks
        if task.get('description'):
            service_request = {
                "resource": {
                    "resourceType": "ServiceRequest",
                    "id": f"task-{i}",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": f"Patient/patient-{clean_patient_id}"},
                    "encounter": {"reference": f"Encounter/encounter-{clean_encounter_id}"},
                    "code": {"text": task['description']},
                    "priority": task.get('urgency', 'routine')
                },
                "request": {
                    "method": "POST",
                    "url": "ServiceRequest"
                }
            }
            bundle["entry"].append(service_request)
    
    # Clinical notes as DocumentReference
    if transcript:
        import base64
        encoded_transcript = base64.b64encode(transcript.encode('utf-8')).decode('utf-8')
        document = {
            "resource": {
                "resourceType": "DocumentReference",
                "id": "clinical-transcript",
                "status": "current",
                "subject": {"reference": f"Patient/patient-{clean_patient_id}"},
                "context": {"encounter": [{"reference": f"Encounter/encounter-{clean_encounter_id}"}]},
                "content": [{
                    "attachment": {
                        "contentType": "text/plain",
                        "data": encoded_transcript
                    }
                }]
            },
            "request": {
                "method": "POST",
                "url": "DocumentReference"
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
            
            # Apply VAD to remove silence
            processed_audio = remove_silence_vad(local)
            
            with open(processed_audio, "rb") as audio_file:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                ).text
            print(f"Transcript: {transcript[:100]}...")
            
            # === SINGLE BEDROCK CALL - Extract complete structured artifact ===
            print("Calling Bedrock for comprehensive extraction...")
            try:
                bedrock_request = get_bedrock_prompt(transcript)
                resp_ai = bedrock.invoke_model(
                    modelId='anthropic.claude-3-haiku-20240307-v1:0',
                    body=json.dumps(bedrock_request)
                )
                
                ai_text = json.loads(resp_ai['body'].read())['content'][0]['text']
                print(f"Bedrock response length: {len(ai_text)} chars")
                
                # Parse JSON from response
                import re
                match = re.search(r'\{.*\}', ai_text, re.DOTALL)
                if not match:
                    raise ValueError("No JSON found in Bedrock response")
                
                consultation_artifact = json.loads(match.group())
                
                # Set metadata fields
                consultation_artifact['metadata']['consultation_id'] = key
                consultation_artifact['metadata_extraction'] = {
                    'extraction_timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+12:00'),
                    'model_used': 'anthropic.claude-3-haiku-20240307-v1:0',
                    'transcript_length': len(transcript),
                    'processing_notes': 'Successful extraction'
                }
                
                print(f"Extracted artifact version: {consultation_artifact.get('version')}")
                print(f"Tasks extracted: {len(consultation_artifact.get('follow_up_tasks', []))}")
                
            except Exception as e:
                print(f"Bedrock extraction error: {e}")
                import traceback
                traceback.print_exc()
                
                # Fallback minimal artifact
                consultation_artifact = {
                    'version': '2.0',
                    'metadata': {
                        'consultation_id': key,
                        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+12:00'),
                        'setting_type': 'other',
                        'specialty': 'general_practice',
                        'encounter_type': 'initial_consultation'
                    },
                    'patient_context': {},
                    'soap_notes': {
                        'subjective': {'chief_complaint': 'Extraction failed'},
                        'objective': {},
                        'assessment': {'clinical_impression': f'Error: {str(e)}'},
                        'plan': {}
                    },
                    'clinical_safety': {
                        'confidence_level': 'low',
                        'missing_information': ['Complete extraction failed']
                    },
                    'follow_up_tasks': [],
                    'handover': {},
                    'metadata_extraction': {
                        'extraction_timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+12:00'),
                        'model_used': 'anthropic.claude-3-haiku-20240307-v1:0',
                        'transcript_length': len(transcript),
                        'processing_notes': f'Extraction failed: {str(e)}'
                    }
                }
            
            # === GENERATE PDF (Deterministic - NO AI) ===
            print("Generating PDF...")
            pdf_path = None
            pdf_s3_key = None
            try:
                pdf_filename = f"/tmp/{key.replace('.webm', '').replace('/', '_')}.pdf"
                generate_consultation_pdf(
                    consultation_artifact,
                    pdf_filename,
                    facility_info={
                        'name': 'Clinical Recorder',
                        'address': 'New Zealand Healthcare',
                        'phone': 'Contact via system'
                    }
                )
                
                # Upload PDF to S3 (commented out - uncomment to enable)
                # pdf_s3_key = f"pdfs/{key.replace('.webm', '.pdf').replace('uploads/', '')}"
                # s3.upload_file(pdf_filename, bucket, pdf_s3_key)
                # pdf_url = s3.generate_presigned_url(
                #     'get_object',
                #     Params={'Bucket': bucket, 'Key': pdf_s3_key},
                #     ExpiresIn=86400
                # )
                
                pdf_path = pdf_filename  # Keep local for now
                print(f"PDF generated: {pdf_filename}")
                
            except Exception as e:
                print(f"PDF generation error: {e}")
                import traceback
                traceback.print_exc()
            
            # === GENERATE FHIR BUNDLE (for backward compatibility) ===
            try:
                fhir_bundle = generate_fhir_bundle(patient_id, key, consultation_artifact, transcript)
            except Exception as e:
                print(f"FHIR generation error: {e}")
                fhir_bundle = None
            
            # === SAVE TO DYNAMODB (Nested structure + backward compatible) ===
            print("Saving to DynamoDB...")
            try:
                item = prepare_consultation_item(
                    audio_key=key,
                    patient_id=patient_id,
                    transcript=transcript,
                    consultation_artifact=consultation_artifact,
                    fhir_bundle=fhir_bundle
                )
                
                # Add PDF path if generated
                if pdf_path:
                    item['pdf_local_path'] = pdf_path
                if pdf_s3_key:
                    item['pdf_s3_key'] = pdf_s3_key
                
                dynamodb.Table(TABLE).put_item(Item=item)
                print(f"Saved to DynamoDB: {key}")
                
            except Exception as e:
                print(f"DynamoDB save error: {e}")
                import traceback
                traceback.print_exc()
            
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
                for conn_item in response['Items']:
                    try:
                        apigateway.post_to_connection(
                            ConnectionId=conn_item['connectionId'],
                            Data=json.dumps({
                                'type': 'completed',
                                'audioKey': key,
                                'result': {
                                    'transcript': transcript,
                                    'consultation_artifact': consultation_artifact,
                                    'fhir_bundle': fhir_bundle,
                                    'pdf_available': pdf_path is not None,
                                    # Legacy fields for backward compatibility
                                    'diagnosis': item.get('diagnosis'),
                                    'medications': item.get('medications'),
                                    'tasks': item.get('tasks')
                                }
                            })
                        )
                        print(f"Sent notification to connection: {conn_item['connectionId']}")
                    except Exception as conn_error:
                        print(f"Failed to send to connection {conn_item['connectionId']}: {conn_error}")
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
