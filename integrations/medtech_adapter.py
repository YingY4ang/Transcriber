"""
Medtech PMS Adapter - Ready for API credentials
Most common PMS in NZ GP clinics
"""

import requests
from typing import Dict, Any
from integrations.base_adapter import PMSAdapter, IntegrationResponse, IntegrationStatus


class MedtechAdapter(PMSAdapter):
    """
    Adapter for Medtech Evolution/32 PMS
    
    SETUP INSTRUCTIONS:
    1. Contact Medtech to get API access
    2. Obtain: API_URL, API_KEY, CLIENT_ID
    3. Set environment variables:
       - MEDTECH_API_URL
       - MEDTECH_API_KEY
       - MEDTECH_CLIENT_ID
    4. Set ENABLE_MEDTECH=true
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_url = config.get('api_url', '')
        self.api_key = config.get('api_key', '')
        self.client_id = config.get('client_id', '')
    
    def get_adapter_name(self) -> str:
        return "Medtech Evolution"
    
    def test_connection(self) -> IntegrationResponse:
        """Test Medtech API connection"""
        if not self.enabled or not self.api_key:
            return IntegrationResponse(
                IntegrationStatus.NOT_CONFIGURED,
                "Medtech not configured. Add API credentials to enable."
            )
        
        try:
            # Test API endpoint
            response = requests.get(
                f"{self.api_url}/api/health",
                headers=self._get_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                return IntegrationResponse(
                    IntegrationStatus.SUCCESS,
                    "Medtech connection successful"
                )
            else:
                return IntegrationResponse(
                    IntegrationStatus.FAILED,
                    f"Medtech connection failed: {response.status_code}"
                )
        except Exception as e:
            return IntegrationResponse(
                IntegrationStatus.FAILED,
                "Medtech connection failed",
                error=str(e)
            )
    
    def save_consultation(
        self,
        patient_id: str,
        consultation_artifact: Dict[str, Any]
    ) -> IntegrationResponse:
        """Save consultation notes to Medtech"""
        if not self.enabled:
            return IntegrationResponse(
                IntegrationStatus.NOT_CONFIGURED,
                "Medtech integration not enabled"
            )
        
        try:
            # Extract SOAP notes from artifact
            soap = consultation_artifact.get('soap_notes', {})
            metadata = consultation_artifact.get('metadata', {})
            
            # Format for Medtech API
            consultation_data = {
                'patient_id': patient_id,
                'consultation_date': metadata.get('timestamp'),
                'consultation_type': metadata.get('encounter_type'),
                'subjective': self._format_subjective(soap.get('subjective', {})),
                'objective': self._format_objective(soap.get('objective', {})),
                'assessment': self._format_assessment(soap.get('assessment', {})),
                'plan': self._format_plan(soap.get('plan', {}))
            }
            
            # POST to Medtech API
            response = requests.post(
                f"{self.api_url}/api/consultations",
                headers=self._get_headers(),
                json=consultation_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return IntegrationResponse(
                    IntegrationStatus.SUCCESS,
                    "Consultation saved to Medtech",
                    data={'consultation_id': response.json().get('id')}
                )
            else:
                return IntegrationResponse(
                    IntegrationStatus.FAILED,
                    f"Failed to save to Medtech: {response.status_code}",
                    error=response.text
                )
        
        except Exception as e:
            return IntegrationResponse(
                IntegrationStatus.FAILED,
                "Error saving to Medtech",
                error=str(e)
            )
    
    def get_patient_context(self, patient_id: str) -> IntegrationResponse:
        """Fetch patient history from Medtech"""
        if not self.enabled:
            return IntegrationResponse(
                IntegrationStatus.NOT_CONFIGURED,
                "Medtech integration not enabled"
            )
        
        try:
            # GET patient data from Medtech
            response = requests.get(
                f"{self.api_url}/api/patients/{patient_id}/summary",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                patient_data = response.json()
                
                # Extract relevant context
                context = {
                    'active_conditions': patient_data.get('conditions', []),
                    'current_medications': patient_data.get('medications', []),
                    'allergies': patient_data.get('allergies', []),
                    'recent_encounters': patient_data.get('recent_consultations', []),
                    'last_vitals': patient_data.get('last_vitals', {})
                }
                
                return IntegrationResponse(
                    IntegrationStatus.SUCCESS,
                    "Patient context retrieved",
                    data=context
                )
            else:
                return IntegrationResponse(
                    IntegrationStatus.FAILED,
                    f"Failed to fetch patient context: {response.status_code}"
                )
        
        except Exception as e:
            return IntegrationResponse(
                IntegrationStatus.FAILED,
                "Error fetching patient context",
                error=str(e)
            )
    
    def create_appointment(
        self,
        patient_id: str,
        appointment_details: Dict[str, Any]
    ) -> IntegrationResponse:
        """Create follow-up appointment in Medtech"""
        if not self.enabled:
            return IntegrationResponse(
                IntegrationStatus.NOT_CONFIGURED,
                "Medtech integration not enabled"
            )
        
        try:
            response = requests.post(
                f"{self.api_url}/api/appointments",
                headers=self._get_headers(),
                json={
                    'patient_id': patient_id,
                    'appointment_type': appointment_details.get('type', 'follow_up'),
                    'duration_minutes': appointment_details.get('duration', 15),
                    'notes': appointment_details.get('notes', '')
                },
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return IntegrationResponse(
                    IntegrationStatus.SUCCESS,
                    "Appointment created",
                    data=response.json()
                )
            else:
                return IntegrationResponse(
                    IntegrationStatus.FAILED,
                    f"Failed to create appointment: {response.status_code}"
                )
        
        except Exception as e:
            return IntegrationResponse(
                IntegrationStatus.FAILED,
                "Error creating appointment",
                error=str(e)
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'X-Client-ID': self.client_id,
            'Content-Type': 'application/json'
        }
    
    def _format_subjective(self, subjective: Dict[str, Any]) -> str:
        """Format subjective section for Medtech"""
        parts = []
        if subjective.get('chief_complaint'):
            parts.append(f"Chief Complaint: {subjective['chief_complaint']}")
        if subjective.get('history_present_illness'):
            parts.append(f"HPI: {subjective['history_present_illness']}")
        return '\n'.join(parts)
    
    def _format_objective(self, objective: Dict[str, Any]) -> str:
        """Format objective section for Medtech"""
        parts = []
        vitals = objective.get('vital_signs', {})
        if vitals:
            parts.append(f"Vitals: {vitals}")
        exam = objective.get('physical_examination', {})
        if exam:
            parts.append(f"Examination: {exam}")
        return '\n'.join(parts)
    
    def _format_assessment(self, assessment: Dict[str, Any]) -> str:
        """Format assessment section for Medtech"""
        parts = []
        if assessment.get('primary_diagnosis'):
            parts.append(f"Diagnosis: {assessment['primary_diagnosis']}")
        if assessment.get('clinical_impression'):
            parts.append(f"Impression: {assessment['clinical_impression']}")
        return '\n'.join(parts)
    
    def _format_plan(self, plan: Dict[str, Any]) -> str:
        """Format plan section for Medtech"""
        parts = []
        if plan.get('treatment_strategy'):
            parts.append(f"Treatment: {plan['treatment_strategy']}")
        meds = plan.get('medications_prescribed', [])
        if meds:
            parts.append(f"Medications: {', '.join([m.get('medication', '') for m in meds])}")
        return '\n'.join(parts)
