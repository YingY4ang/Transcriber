"""
Enhanced Lambda API with approval workflow, patient history, and task management
"""

import json
import os
import boto3
from uuid import uuid4
import urllib.parse
from typing import Dict, Any

# Import our modules
import sys
sys.path.append('/opt/python')  # Lambda layer path

from config.settings import (
    AWS_REGION, S3_BUCKET, DYNAMODB_TABLE, SQS_QUEUE_URL,
    WEBSOCKET_URL, get_integration_status
)
from storage.dynamodb.enhanced_storage import ConsultationStore, ConsentStore, AuditLog

# AWS clients
s3 = boto3.client('s3', region_name=AWS_REGION)
sqs = boto3.client('sqs', region_name=AWS_REGION)

# Storage clients
consultation_store = ConsultationStore(DYNAMODB_TABLE, AWS_REGION)
consent_store = ConsentStore(DYNAMODB_TABLE, AWS_REGION)
audit_log = AuditLog(DYNAMODB_TABLE, AWS_REGION)

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
}


def handler(event, context):
    """Main Lambda handler"""
    path = event.get('rawPath', '')
    method = event.get('requestContext', {}).get('http', {}).get('method', '')
    
    # Handle OPTIONS for CORS
    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS}
    
    # Route to appropriate handler
    try:
        if path == '/config':
            return handle_config()
        
        elif path == '/get-upload-url':
            return handle_get_upload_url(event)
        
        elif path == '/upload-complete':
            return handle_upload_complete(event)
        
        elif path.startswith('/result/'):
            return handle_get_result(path)
        
        elif path == '/approvals/pending':
            return handle_get_pending_approvals()
        
        elif path == '/approvals/approve':
            return handle_approve_consultation(event)
        
        elif path == '/approvals/reject':
            return handle_reject_consultation(event)
        
        elif path.startswith('/patient/'):
            return handle_patient_history(path)
        
        elif path == '/tasks/pending':
            return handle_get_pending_tasks()
        
        elif path == '/tasks/update':
            return handle_update_task(event)
        
        elif path == '/handover':
            return handle_get_handover(event)
        
        elif path == '/consent/record':
            return handle_record_consent(event)
        
        elif path == '/consent/check':
            return handle_check_consent(event)
        
        elif path == '/integration/status':
            return handle_integration_status()
        
        else:
            return error_response(404, 'Not found')
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return error_response(500, str(e))


def handle_config():
    """Return system configuration"""
    return success_response({
        'websocketUrl': WEBSOCKET_URL,
        'integrations': get_integration_status()
    })


def handle_get_upload_url(event):
    """Generate presigned URL for audio upload"""
    params = event.get('queryStringParameters', {}) or {}
    patient_id = params.get('patientId', 'unknown')
    
    # Check consent before allowing upload
    if not consent_store.check_consent(patient_id, 'recording'):
        return error_response(403, 'Patient consent required for recording')
    
    key = f"uploads/{patient_id}_{uuid4()}.webm"
    
    url = s3.generate_presigned_url(
        'put_object',
        Params={'Bucket': S3_BUCKET, 'Key': key},
        ExpiresIn=3600,
        HttpMethod='PUT'
    )
    
    return success_response({'upload_url': url, 'key': key})


def handle_upload_complete(event):
    """Trigger processing after upload"""
    body = json.loads(event.get('body', '{}'))
    key = body.get('key')
    
    if not key:
        return error_response(400, 'key required')
    
    # Send to SQS for processing
    message = {
        'Records': [{
            's3': {
                'bucket': {'name': S3_BUCKET},
                'object': {'key': key}
            }
        }]
    }
    
    sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps(message)
    )
    
    return success_response({'status': 'processing triggered'})


def handle_get_result(path):
    """Get consultation result"""
    key = urllib.parse.unquote(path.replace('/result/', ''))
    
    # Get from DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
    resp = table.get_item(Key={'audio_key': key})
    
    if 'Item' not in resp:
        return success_response({'status': 'processing'}, 404)
    
    item = resp['Item']
    
    # Log access
    audit_log.log_action('view', 'system', key)
    
    # Return based on format
    if item.get('artifact_version') == '2.0':
        return success_response(format_consultation_response(item))
    else:
        return success_response(item)


def handle_get_pending_approvals():
    """Get all consultations pending approval"""
    approvals = consultation_store.get_pending_approvals()
    
    # Format for frontend
    formatted = []
    for item in approvals:
        formatted.append({
            'audio_key': item.get('audio_key'),
            'patient_id': item.get('patient_id'),
            'timestamp': item.get('consultation_timestamp'),
            'chief_complaint': item.get('chief_complaint'),
            'primary_diagnosis': item.get('primary_diagnosis'),
            'task_count': item.get('total_task_count', 0),
            'urgent_task_count': item.get('urgent_task_count', 0),
            'created_at': item.get('created_at')
        })
    
    return success_response({'approvals': formatted, 'count': len(formatted)})


def handle_approve_consultation(event):
    """Approve a consultation"""
    body = json.loads(event.get('body', '{}'))
    audio_key = body.get('audio_key')
    approved_by = body.get('approved_by')
    notes = body.get('notes')
    modified_artifact = body.get('modified_artifact')
    
    if not audio_key or not approved_by:
        return error_response(400, 'audio_key and approved_by required')
    
    success = consultation_store.approve_consultation(
        audio_key, approved_by, notes, modified_artifact
    )
    
    if success:
        # Log approval
        audit_log.log_action('approve', approved_by, audio_key, {'notes': notes})
        
        # TODO: Trigger task routing here
        
        return success_response({'status': 'approved'})
    else:
        return error_response(500, 'Failed to approve consultation')


def handle_reject_consultation(event):
    """Reject a consultation"""
    body = json.loads(event.get('body', '{}'))
    audio_key = body.get('audio_key')
    rejected_by = body.get('rejected_by')
    reason = body.get('reason')
    
    if not audio_key or not rejected_by:
        return error_response(400, 'audio_key and rejected_by required')
    
    # Update status to rejected
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    table.update_item(
        Key={'audio_key': audio_key},
        UpdateExpression='SET approval_status = :status, rejected_by = :by, rejection_reason = :reason',
        ExpressionAttributeValues={
            ':status': 'rejected',
            ':by': rejected_by,
            ':reason': reason
        }
    )
    
    # Log rejection
    audit_log.log_action('reject', rejected_by, audio_key, {'reason': reason})
    
    return success_response({'status': 'rejected'})


def handle_patient_history(path):
    """Get patient consultation history"""
    patient_id = urllib.parse.unquote(path.replace('/patient/', ''))
    
    history = consultation_store.get_patient_history(patient_id)
    
    # Format for timeline view
    formatted = []
    for item in history:
        formatted.append({
            'audio_key': item.get('audio_key'),
            'timestamp': item.get('consultation_timestamp'),
            'chief_complaint': item.get('chief_complaint'),
            'primary_diagnosis': item.get('primary_diagnosis'),
            'medications': item.get('medications', []),
            'task_count': item.get('total_task_count', 0),
            'approval_status': item.get('approval_status')
        })
    
    return success_response({
        'patient_id': patient_id,
        'consultation_count': len(formatted),
        'consultations': formatted
    })


def handle_get_pending_tasks():
    """Get all pending tasks across all patients"""
    tasks = consultation_store.get_all_pending_tasks()
    
    return success_response({
        'tasks': tasks,
        'count': len(tasks),
        'urgent_count': len([t for t in tasks if t.get('urgency') in ['stat', 'urgent']])
    })


def handle_update_task(event):
    """Update task status"""
    body = json.loads(event.get('body', '{}'))
    audio_key = body.get('audio_key')
    task_id = body.get('task_id')
    new_status = body.get('status')
    completed_by = body.get('completed_by')
    notes = body.get('notes')
    
    if not all([audio_key, task_id, new_status]):
        return error_response(400, 'audio_key, task_id, and status required')
    
    success = consultation_store.update_task_status(
        audio_key, task_id, new_status, completed_by, notes
    )
    
    if success:
        # Log task update
        audit_log.log_action('update_task', completed_by or 'system', task_id, {
            'new_status': new_status,
            'notes': notes
        })
        
        return success_response({'status': 'updated'})
    else:
        return error_response(500, 'Failed to update task')


def handle_get_handover(event):
    """Generate handover report"""
    params = event.get('queryStringParameters', {}) or {}
    clinician_id = params.get('clinician_id', 'unknown')
    date = params.get('date')  # Optional, defaults to today
    
    handover_data = consultation_store.get_handover_data(clinician_id, date)
    
    return success_response(handover_data)


def handle_record_consent(event):
    """Record patient consent"""
    body = json.loads(event.get('body', '{}'))
    patient_id = body.get('patient_id')
    consent_type = body.get('consent_type')
    granted = body.get('granted', False)
    recorded_by = body.get('recorded_by')
    notes = body.get('notes')
    
    if not all([patient_id, consent_type, recorded_by]):
        return error_response(400, 'patient_id, consent_type, and recorded_by required')
    
    consent_id = consent_store.record_consent(
        patient_id, consent_type, granted, recorded_by, notes
    )
    
    if consent_id:
        return success_response({'consent_id': consent_id, 'status': 'recorded'})
    else:
        return error_response(500, 'Failed to record consent')


def handle_check_consent(event):
    """Check if patient has granted consent"""
    params = event.get('queryStringParameters', {}) or {}
    patient_id = params.get('patient_id')
    consent_type = params.get('consent_type')
    
    if not all([patient_id, consent_type]):
        return error_response(400, 'patient_id and consent_type required')
    
    has_consent = consent_store.check_consent(patient_id, consent_type)
    
    return success_response({
        'patient_id': patient_id,
        'consent_type': consent_type,
        'granted': has_consent
    })


def handle_integration_status():
    """Get integration status"""
    return success_response(get_integration_status())


def format_consultation_response(item: Dict[str, Any]) -> Dict[str, Any]:
    """Format consultation for frontend (3-button interface)"""
    follow_up_tasks = item.get('follow_up_tasks', [])
    
    return {
        'status': 'completed',
        'approval_status': item.get('approval_status', 'pending_approval'),
        'buttons': [
            {
                'type': 'pdf',
                'label': 'Download PDF',
                'url': item.get('pdf_url'),
                'available': item.get('pdf_url') is not None
            },
            {
                'type': 'tasks',
                'label': 'Follow-up Tasks',
                'count': len(follow_up_tasks),
                'urgent_count': item.get('urgent_task_count', 0),
                'tasks': [
                    {
                        'task_id': task.get('task_id'),
                        'description': task.get('description'),
                        'urgency': task.get('urgency'),
                        'owner_role': task.get('owner_role'),
                        'due_at': task.get('due_at'),
                        'status': task.get('status'),
                        'details': task
                    }
                    for task in follow_up_tasks
                ]
            },
            {
                'type': 'json',
                'label': 'Full JSON',
                'data': {
                    'transcript': item.get('transcript'),
                    'consultation_artifact': item.get('consultation_artifact'),
                    'fhir_bundle': item.get('fhir_bundle'),
                    'metadata': {
                        'audio_key': item.get('audio_key'),
                        'patient_id': item.get('patient_id'),
                        'timestamp': item.get('timestamp'),
                        'setting_type': item.get('setting_type'),
                        'specialty': item.get('specialty'),
                        'encounter_type': item.get('encounter_type')
                    }
                }
            }
        ]
    }


def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Return success response"""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(data)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Return error response"""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps({'error': message})
    }
