"""
Enhanced DynamoDB storage for approval workflow, patient history, and task management.
"""

import time
from typing import Dict, Any, List, Optional
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr


class ConsultationStore:
    """Enhanced storage operations for consultations"""
    
    def __init__(self, table_name: str, region: str = 'ap-southeast-2'):
        dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = dynamodb.Table(table_name)
    
    def save_consultation_with_approval(
        self,
        audio_key: str,
        patient_id: str,
        transcript: str,
        consultation_artifact: Dict[str, Any],
        fhir_bundle: Optional[Dict[str, Any]] = None,
        approval_status: str = 'pending_approval'
    ) -> bool:
        """Save consultation with approval workflow status"""
        from storage.dynamodb.consultation_storage import prepare_consultation_item
        
        item = prepare_consultation_item(
            audio_key, patient_id, transcript, consultation_artifact, fhir_bundle
        )
        
        # Add approval workflow fields
        item.update({
            'approval_status': approval_status,  # pending_approval, approved, rejected
            'approval_timestamp': None,
            'approved_by': None,
            'approval_notes': None,
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        })
        
        try:
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error saving consultation: {e}")
            return False
    
    def approve_consultation(
        self,
        audio_key: str,
        approved_by: str,
        notes: Optional[str] = None,
        modified_artifact: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Approve consultation and optionally update artifact"""
        try:
            update_expr = "SET approval_status = :status, approval_timestamp = :ts, approved_by = :by, updated_at = :updated"
            expr_values = {
                ':status': 'approved',
                ':ts': int(time.time()),
                ':by': approved_by,
                ':updated': int(time.time())
            }
            
            if notes:
                update_expr += ", approval_notes = :notes"
                expr_values[':notes'] = notes
            
            if modified_artifact:
                update_expr += ", consultation_artifact = :artifact"
                expr_values[':artifact'] = modified_artifact
            
            self.table.update_item(
                Key={'audio_key': audio_key},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            return True
        except Exception as e:
            print(f"Error approving consultation: {e}")
            return False
    
    def get_patient_history(self, patient_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all consultations for a patient, ordered by most recent"""
        try:
            # Scan with filter (in production, use GSI on patient_id)
            response = self.table.scan(
                FilterExpression=Attr('patient_id').eq(patient_id),
                Limit=limit
            )
            
            items = response.get('Items', [])
            # Sort by timestamp descending
            items.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return items
        except Exception as e:
            print(f"Error fetching patient history: {e}")
            return []
    
    def get_pending_approvals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all consultations pending approval"""
        try:
            response = self.table.scan(
                FilterExpression=Attr('approval_status').eq('pending_approval'),
                Limit=limit
            )
            
            items = response.get('Items', [])
            # Sort by created_at descending
            items.sort(key=lambda x: x.get('created_at', 0), reverse=True)
            return items
        except Exception as e:
            print(f"Error fetching pending approvals: {e}")
            return []
    
    def get_all_pending_tasks(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Get all pending tasks across all approved consultations"""
        try:
            response = self.table.scan(
                FilterExpression=Attr('approval_status').eq('approved') & Attr('pending_task_count').gt(0),
                Limit=limit
            )
            
            # Extract and flatten tasks
            all_tasks = []
            for item in response.get('Items', []):
                tasks = item.get('follow_up_tasks', [])
                for task in tasks:
                    if task.get('status') in ['proposed', 'pending']:
                        all_tasks.append({
                            **task,
                            'consultation_key': item.get('audio_key'),
                            'patient_id': item.get('patient_id'),
                            'consultation_date': item.get('consultation_timestamp')
                        })
            
            # Sort by urgency then due date
            urgency_order = {'stat': 0, 'urgent': 1, 'routine': 2, 'low': 3}
            all_tasks.sort(key=lambda x: (
                urgency_order.get(x.get('urgency', 'routine'), 2),
                x.get('due_at', 'zzz')
            ))
            
            return all_tasks
        except Exception as e:
            print(f"Error fetching pending tasks: {e}")
            return []
    
    def update_task_status(
        self,
        audio_key: str,
        task_id: str,
        new_status: str,
        completed_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Update task status with optional completion info"""
        try:
            response = self.table.get_item(Key={'audio_key': audio_key})
            if 'Item' not in response:
                return False
            
            item = response['Item']
            tasks = item.get('follow_up_tasks', [])
            
            updated = False
            for task in tasks:
                if task.get('task_id') == task_id:
                    task['status'] = new_status
                    task['updated_at'] = int(time.time())
                    if completed_by:
                        task['completed_by'] = completed_by
                    if notes:
                        task['completion_notes'] = notes
                    updated = True
                    break
            
            if not updated:
                return False
            
            # Recalculate counts
            pending_count = len([t for t in tasks if t.get('status') in ['proposed', 'pending']])
            
            self.table.update_item(
                Key={'audio_key': audio_key},
                UpdateExpression='SET follow_up_tasks = :tasks, pending_task_count = :pending, updated_at = :updated',
                ExpressionAttributeValues={
                    ':tasks': tasks,
                    ':pending': pending_count,
                    ':updated': int(time.time())
                }
            )
            
            return True
        except Exception as e:
            print(f"Error updating task: {e}")
            return False
    
    def get_handover_data(self, clinician_id: str, date: Optional[str] = None) -> Dict[str, Any]:
        """Get handover data for a clinician's shift"""
        try:
            # Get today's consultations (in production, use GSI)
            if not date:
                from datetime import datetime
                date = datetime.now().strftime('%Y-%m-%d')
            
            response = self.table.scan(
                FilterExpression=Attr('approval_status').eq('approved')
            )
            
            items = response.get('Items', [])
            
            # Filter by date and extract relevant info
            handover_patients = []
            total_pending_tasks = 0
            urgent_tasks = []
            
            for item in items:
                consultation_date = item.get('consultation_timestamp', '')
                if not consultation_date.startswith(date):
                    continue
                
                patient_id = item.get('patient_id')
                artifact = item.get('consultation_artifact', {})
                tasks = item.get('follow_up_tasks', [])
                
                pending_tasks = [t for t in tasks if t.get('status') in ['proposed', 'pending']]
                urgent = [t for t in pending_tasks if t.get('urgency') in ['stat', 'urgent']]
                
                total_pending_tasks += len(pending_tasks)
                urgent_tasks.extend(urgent)
                
                handover_patients.append({
                    'patient_id': patient_id,
                    'consultation_time': consultation_date,
                    'chief_complaint': item.get('chief_complaint'),
                    'primary_diagnosis': item.get('primary_diagnosis'),
                    'pending_tasks': len(pending_tasks),
                    'urgent_tasks': len(urgent),
                    'handover_note': artifact.get('handover', {})
                })
            
            return {
                'date': date,
                'clinician_id': clinician_id,
                'total_patients': len(handover_patients),
                'total_pending_tasks': total_pending_tasks,
                'urgent_task_count': len(urgent_tasks),
                'patients': handover_patients,
                'urgent_tasks': urgent_tasks
            }
        except Exception as e:
            print(f"Error generating handover: {e}")
            return {}


class ConsentStore:
    """Store and track patient consent"""
    
    def __init__(self, table_name: str, region: str = 'ap-southeast-2'):
        dynamodb = boto3.resource('dynamodb', region_name=region)
        # In production, create separate consent table
        # For now, we'll add to main table with consent_ prefix
        self.table = dynamodb.Table(table_name)
    
    def record_consent(
        self,
        patient_id: str,
        consent_type: str,
        granted: bool,
        recorded_by: str,
        notes: Optional[str] = None
    ) -> str:
        """Record patient consent"""
        consent_id = f"consent_{patient_id}_{int(time.time())}"
        
        item = {
            'audio_key': consent_id,  # Using audio_key as partition key
            'patient_id': patient_id,
            'consent_type': consent_type,  # recording, ai_processing, data_storage
            'granted': granted,
            'recorded_by': recorded_by,
            'recorded_at': int(time.time()),
            'notes': notes,
            'item_type': 'consent'  # Distinguish from consultations
        }
        
        try:
            self.table.put_item(Item=item)
            return consent_id
        except Exception as e:
            print(f"Error recording consent: {e}")
            return None
    
    def check_consent(self, patient_id: str, consent_type: str) -> bool:
        """Check if patient has granted specific consent"""
        try:
            response = self.table.scan(
                FilterExpression=Attr('patient_id').eq(patient_id) & 
                                Attr('item_type').eq('consent') &
                                Attr('consent_type').eq(consent_type) &
                                Attr('granted').eq(True)
            )
            return len(response.get('Items', [])) > 0
        except Exception as e:
            print(f"Error checking consent: {e}")
            return False


class AuditLog:
    """Audit logging for compliance"""
    
    def __init__(self, table_name: str, region: str = 'ap-southeast-2'):
        dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = dynamodb.Table(table_name)
    
    def log_action(
        self,
        action: str,
        user_id: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log an action for audit trail"""
        audit_id = f"audit_{int(time.time())}_{user_id}"
        
        item = {
            'audio_key': audit_id,
            'action': action,  # view, edit, approve, delete, export
            'user_id': user_id,
            'resource_id': resource_id,
            'timestamp': int(time.time()),
            'details': details or {},
            'item_type': 'audit'
        }
        
        try:
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error logging audit: {e}")
            return False
