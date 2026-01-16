"""
DynamoDB storage module for consultation artifacts.
Preserves nested JSON structure while maintaining backward compatibility.
"""

import json
from typing import Dict, Any
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def prepare_consultation_item(
    audio_key: str,
    patient_id: str,
    transcript: str,
    consultation_artifact: Dict[str, Any],
    fhir_bundle: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Prepare DynamoDB item with nested artifact structure and backward-compatible flat fields.
    
    Args:
        audio_key: S3 key of audio file (partition key)
        patient_id: Patient identifier
        transcript: Full transcript text
        consultation_artifact: Complete structured artifact from Bedrock
        fhir_bundle: Optional FHIR bundle
        
    Returns:
        DynamoDB item dict
    """
    import time
    
    # Extract commonly queried fields for top-level indexing
    metadata = consultation_artifact.get('metadata', {})
    soap = consultation_artifact.get('soap_notes', {})
    tasks = consultation_artifact.get('follow_up_tasks', [])
    
    # Count task statistics
    pending_tasks = [t for t in tasks if t.get('status') == 'proposed']
    urgent_tasks = [t for t in tasks if t.get('urgency') in ['stat', 'urgent']]
    
    # Build item with nested structure
    item = {
        # Primary key
        'audio_key': audio_key,
        
        # Metadata
        'patient_id': patient_id,
        'timestamp': int(time.time()),
        'consultation_timestamp': metadata.get('timestamp'),
        'setting_type': metadata.get('setting_type'),
        'specialty': metadata.get('specialty'),
        'encounter_type': metadata.get('encounter_type'),
        
        # Core data
        'transcript': transcript,
        'consultation_artifact': consultation_artifact,  # NESTED STRUCTURE PRESERVED
        
        # Task statistics for querying
        'follow_up_tasks': tasks,  # Duplicate for easy access
        'pending_task_count': len(pending_tasks),
        'urgent_task_count': len(urgent_tasks),
        'total_task_count': len(tasks),
        
        # Clinical summary for quick access
        'primary_diagnosis': soap.get('assessment', {}).get('primary_diagnosis'),
        'chief_complaint': soap.get('subjective', {}).get('chief_complaint'),
        
        # FHIR bundle
        'fhir_bundle': fhir_bundle,
        
        # Version tracking
        'artifact_version': consultation_artifact.get('version', '2.0'),
        
        # LEGACY FIELDS FOR BACKWARD COMPATIBILITY
        # Extract from artifact for old consumers
        'diagnosis': soap.get('assessment', {}).get('primary_diagnosis'),
        'medications': [
            m.get('medication') 
            for m in soap.get('plan', {}).get('medications_prescribed', [])
        ],
        'tasks': [t.get('description') for t in tasks[:5]],  # First 5 task descriptions
        'follow_up': soap.get('plan', {}).get('follow_up', {}).get('timeframe'),
        'notes': soap.get('assessment', {}).get('clinical_impression'),
        'vital_signs': soap.get('objective', {}).get('vital_signs', {}),
        'symptoms': [
            s.get('symptom') 
            for s in soap.get('subjective', {}).get('symptoms', [])
        ]
    }
    
    return item


def extract_legacy_format(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract legacy flat format from item for backward compatibility.
    
    Args:
        item: DynamoDB item
        
    Returns:
        Legacy format dict
    """
    return {
        'audio_key': item.get('audio_key'),
        'patient_id': item.get('patient_id'),
        'transcript': item.get('transcript'),
        'timestamp': item.get('timestamp'),
        'diagnosis': item.get('diagnosis'),
        'medications': item.get('medications', []),
        'tasks': item.get('tasks', []),
        'follow_up': item.get('follow_up'),
        'notes': item.get('notes'),
        'vital_signs': item.get('vital_signs', {}),
        'symptoms': item.get('symptoms', []),
        'fhir_bundle': item.get('fhir_bundle')
    }


def extract_artifact(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract consultation artifact from item.
    
    Args:
        item: DynamoDB item
        
    Returns:
        Consultation artifact dict or None
    """
    return item.get('consultation_artifact')


def is_new_format(item: Dict[str, Any]) -> bool:
    """
    Check if item uses new artifact format.
    
    Args:
        item: DynamoDB item
        
    Returns:
        True if new format, False if legacy
    """
    return 'consultation_artifact' in item and item.get('artifact_version') == '2.0'


def get_task_by_id(item: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    """
    Get specific task by ID.
    
    Args:
        item: DynamoDB item
        task_id: Task identifier
        
    Returns:
        Task dict or None
    """
    tasks = item.get('follow_up_tasks', [])
    for task in tasks:
        if task.get('task_id') == task_id:
            return task
    return None


def get_tasks_by_owner(item: Dict[str, Any], owner_role: str) -> list:
    """
    Get tasks assigned to specific role.
    
    Args:
        item: DynamoDB item
        owner_role: Role to filter by
        
    Returns:
        List of tasks
    """
    tasks = item.get('follow_up_tasks', [])
    return [t for t in tasks if t.get('owner_role') == owner_role]


def get_urgent_tasks(item: Dict[str, Any]) -> list:
    """
    Get urgent/stat tasks.
    
    Args:
        item: DynamoDB item
        
    Returns:
        List of urgent tasks
    """
    tasks = item.get('follow_up_tasks', [])
    return [t for t in tasks if t.get('urgency') in ['stat', 'urgent']]


def update_task_status(
    dynamodb_table,
    audio_key: str,
    task_id: str,
    new_status: str
) -> bool:
    """
    Update status of a specific task.
    
    Args:
        dynamodb_table: boto3 DynamoDB table resource
        audio_key: Item key
        task_id: Task to update
        new_status: New status value
        
    Returns:
        True if successful
    """
    try:
        # Get current item
        response = dynamodb_table.get_item(Key={'audio_key': audio_key})
        if 'Item' not in response:
            return False
        
        item = response['Item']
        tasks = item.get('follow_up_tasks', [])
        
        # Update task status
        updated = False
        for task in tasks:
            if task.get('task_id') == task_id:
                task['status'] = new_status
                updated = True
                break
        
        if not updated:
            return False
        
        # Recalculate counts
        pending_count = len([t for t in tasks if t.get('status') == 'proposed'])
        
        # Update item
        dynamodb_table.update_item(
            Key={'audio_key': audio_key},
            UpdateExpression='SET follow_up_tasks = :tasks, pending_task_count = :pending',
            ExpressionAttributeValues={
                ':tasks': tasks,
                ':pending': pending_count
            }
        )
        
        return True
        
    except Exception as e:
        print(f"Error updating task status: {e}")
        return False
