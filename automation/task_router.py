"""
Task router - orchestrates task execution based on configuration
Supports both manual mode (fully functional now) and automatic mode (when integrations enabled)
"""

from typing import Dict, Any, List
from config.settings import INTEGRATIONS_ENABLED, is_integration_ready
from integrations.base_adapter import IntegrationResponse, IntegrationStatus


class TaskRouter:
    """
    Routes tasks to appropriate systems based on configuration
    
    MODES:
    - Manual (INTEGRATIONS_ENABLED=false): Tasks queued for manual completion
    - Automatic (INTEGRATIONS_ENABLED=true): Tasks automatically routed to external systems
    """
    
    def __init__(self, adapters: Dict[str, Any]):
        """
        Initialize router with available adapters
        
        Args:
            adapters: Dict of adapter instances {
                'pms': MedtechAdapter,
                'pharmacy': PharmacyAdapter,
                'notifications': AWSNotificationAdapter,
                etc.
            }
        """
        self.adapters = adapters
        self.mode = 'automatic' if INTEGRATIONS_ENABLED else 'manual'
    
    def route_task(self, task: Dict[str, Any], patient_id: str) -> IntegrationResponse:
        """
        Route a single task to appropriate system
        
        Args:
            task: Task dict from consultation_artifact
            patient_id: Patient identifier
            
        Returns:
            IntegrationResponse with routing result
        """
        task_type = task.get('task_type')
        
        # Route based on task type
        if task_type == 'prescription':
            return self._route_prescription(task, patient_id)
        
        elif task_type == 'order_scan':
            return self._route_imaging(task, patient_id)
        
        elif task_type == 'order_lab':
            return self._route_lab_test(task, patient_id)
        
        elif task_type == 'referral':
            return self._route_referral(task, patient_id)
        
        elif task_type == 'follow_up_appointment':
            return self._route_appointment(task, patient_id)
        
        elif task_type == 'nursing_observation':
            return self._route_nursing_task(task, patient_id)
        
        else:
            # Generic task - just notify
            return self._route_generic_task(task, patient_id)
    
    def route_all_tasks(
        self,
        tasks: List[Dict[str, Any]],
        patient_id: str
    ) -> Dict[str, Any]:
        """
        Route all tasks from a consultation
        
        Returns:
            Summary of routing results
        """
        results = {
            'total': len(tasks),
            'routed': 0,
            'queued': 0,
            'failed': 0,
            'details': []
        }
        
        for task in tasks:
            response = self.route_task(task, patient_id)
            
            result_entry = {
                'task_id': task.get('task_id'),
                'task_type': task.get('task_type'),
                'description': task.get('description'),
                'status': response.status.value,
                'message': response.message
            }
            
            if response.is_success():
                if self.mode == 'automatic':
                    results['routed'] += 1
                else:
                    results['queued'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append(result_entry)
        
        return results
    
    def _route_prescription(self, task: Dict[str, Any], patient_id: str) -> IntegrationResponse:
        """Route prescription task"""
        prescription_data = task.get('required_inputs', {}).get('prescription', {})
        
        if not prescription_data:
            return IntegrationResponse(
                IntegrationStatus.FAILED,
                "No prescription data in task"
            )
        
        # Add patient ID and metadata
        prescription_data['patient_id'] = patient_id
        prescription_data['task_id'] = task.get('task_id')
        
        # If integrations enabled and pharmacy adapter available
        if self.mode == 'automatic' and 'pharmacy' in self.adapters:
            pharmacy = self.adapters['pharmacy']
            if pharmacy.enabled:
                return pharmacy.send_prescription(patient_id, prescription_data)
        
        # Otherwise, send notification if available
        if 'notifications' in self.adapters:
            notifications = self.adapters['notifications']
            # In manual mode, notify pharmacy via email
            pharmacy_email = prescription_data.get('pharmacy_email', 'pharmacy@example.com')
            return notifications.send_prescription_notification(prescription_data, pharmacy_email)
        
        # Fallback: queue for manual processing
        return IntegrationResponse(
            IntegrationStatus.PENDING,
            "Prescription queued for manual processing",
            data={'task_id': task.get('task_id')}
        )
    
    def _route_imaging(self, task: Dict[str, Any], patient_id: str) -> IntegrationResponse:
        """Route imaging order"""
        imaging_data = task.get('required_inputs', {}).get('imaging', {})
        
        if not imaging_data:
            return IntegrationResponse(
                IntegrationStatus.FAILED,
                "No imaging data in task"
            )
        
        imaging_data['patient_id'] = patient_id
        imaging_data['task_id'] = task.get('task_id')
        
        # If integrations enabled and radiology adapter available
        if self.mode == 'automatic' and 'radiology' in self.adapters:
            radiology = self.adapters['radiology']
            if radiology.enabled:
                return radiology.order_imaging(patient_id, imaging_data)
        
        # Otherwise, send notification
        if 'notifications' in self.adapters:
            notifications = self.adapters['notifications']
            radiology_email = imaging_data.get('radiology_email', 'radiology@example.com')
            
            message = f"""
New imaging order:

Patient: {patient_id}
Modality: {imaging_data.get('modality')}
Body Part: {imaging_data.get('body_part')}
Urgency: {imaging_data.get('urgency', 'routine').upper()}
Contrast: {'Yes' if imaging_data.get('contrast') else 'No'}

Clinical Question: {imaging_data.get('clinical_question')}
"""
            return notifications.send_email(radiology_email, message, "New Imaging Order")
        
        return IntegrationResponse(
            IntegrationStatus.PENDING,
            "Imaging order queued for manual processing"
        )
    
    def _route_lab_test(self, task: Dict[str, Any], patient_id: str) -> IntegrationResponse:
        """Route lab test order"""
        lab_data = task.get('required_inputs', {}).get('lab_test', {})
        
        if not lab_data:
            return IntegrationResponse(
                IntegrationStatus.FAILED,
                "No lab test data in task"
            )
        
        lab_data['patient_id'] = patient_id
        
        # If integrations enabled and lab adapter available
        if self.mode == 'automatic' and 'lab' in self.adapters:
            lab = self.adapters['lab']
            if lab.enabled:
                return lab.order_lab_test(patient_id, lab_data)
        
        # Otherwise, send notification
        if 'notifications' in self.adapters:
            notifications = self.adapters['notifications']
            lab_email = lab_data.get('lab_email', 'lab@example.com')
            
            message = f"""
New lab test order:

Patient: {patient_id}
Test: {lab_data.get('test_name')}
Sample Type: {lab_data.get('sample_type')}
Urgency: {lab_data.get('urgency', 'routine').upper()}
Fasting Required: {'Yes' if lab_data.get('fasting_required') else 'No'}
"""
            return notifications.send_email(lab_email, message, "New Lab Test Order")
        
        return IntegrationResponse(
            IntegrationStatus.PENDING,
            "Lab test queued for manual processing"
        )
    
    def _route_referral(self, task: Dict[str, Any], patient_id: str) -> IntegrationResponse:
        """Route referral"""
        referral_data = task.get('required_inputs', {}).get('referral', {})
        
        if not referral_data:
            return IntegrationResponse(
                IntegrationStatus.FAILED,
                "No referral data in task"
            )
        
        referral_data['patient_id'] = patient_id
        
        # If HealthLink enabled
        if self.mode == 'automatic' and 'healthlink' in self.adapters:
            healthlink = self.adapters['healthlink']
            if healthlink.enabled:
                return healthlink.send_referral(patient_id, referral_data)
        
        # Otherwise, send email notification
        if 'notifications' in self.adapters:
            notifications = self.adapters['notifications']
            specialist_email = referral_data.get('specialist_email', 'specialist@example.com')
            return notifications.send_referral_notification(referral_data, specialist_email)
        
        return IntegrationResponse(
            IntegrationStatus.PENDING,
            "Referral queued for manual processing"
        )
    
    def _route_appointment(self, task: Dict[str, Any], patient_id: str) -> IntegrationResponse:
        """Route follow-up appointment"""
        appointment_data = task.get('required_inputs', {}).get('appointment', {})
        
        # If PMS integration enabled
        if self.mode == 'automatic' and 'pms' in self.adapters:
            pms = self.adapters['pms']
            if pms.enabled:
                return pms.create_appointment(patient_id, appointment_data)
        
        # Otherwise, queue for manual booking
        return IntegrationResponse(
            IntegrationStatus.PENDING,
            "Appointment queued for manual booking"
        )
    
    def _route_nursing_task(self, task: Dict[str, Any], patient_id: str) -> IntegrationResponse:
        """Route nursing task"""
        # Send notification to nursing staff
        if 'notifications' in self.adapters:
            notifications = self.adapters['notifications']
            nurse_email = task.get('required_inputs', {}).get('nurse_email', 'nursing@example.com')
            return notifications.send_task_notification(task, nurse_email)
        
        return IntegrationResponse(
            IntegrationStatus.PENDING,
            "Nursing task queued"
        )
    
    def _route_generic_task(self, task: Dict[str, Any], patient_id: str) -> IntegrationResponse:
        """Route generic task"""
        owner_role = task.get('owner_role', 'doctor')
        
        # Send notification to task owner
        if 'notifications' in self.adapters:
            notifications = self.adapters['notifications']
            owner_email = task.get('required_inputs', {}).get('owner_email', f'{owner_role}@example.com')
            return notifications.send_task_notification(task, owner_email)
        
        return IntegrationResponse(
            IntegrationStatus.PENDING,
            f"Task queued for {owner_role}"
        )
