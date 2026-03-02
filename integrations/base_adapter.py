"""
Base adapter interface for all external integrations.
All adapters implement this interface for consistency.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum


class IntegrationStatus(Enum):
    """Status of integration operations"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    NOT_CONFIGURED = "not_configured"


class IntegrationResponse:
    """Standardized response from integration operations"""
    
    def __init__(
        self,
        status: IntegrationStatus,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        self.status = status
        self.message = message
        self.data = data or {}
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status.value,
            'message': self.message,
            'data': self.data,
            'error': self.error
        }
    
    def is_success(self) -> bool:
        return self.status == IntegrationStatus.SUCCESS


class BaseAdapter(ABC):
    """Base class for all integration adapters"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', False)
    
    @abstractmethod
    def test_connection(self) -> IntegrationResponse:
        """Test if integration is properly configured and accessible"""
        pass
    
    @abstractmethod
    def get_adapter_name(self) -> str:
        """Return name of this adapter"""
        pass


class PMSAdapter(BaseAdapter):
    """Base adapter for Practice Management Systems"""
    
    @abstractmethod
    def save_consultation(
        self,
        patient_id: str,
        consultation_artifact: Dict[str, Any]
    ) -> IntegrationResponse:
        """Save consultation notes to PMS"""
        pass
    
    @abstractmethod
    def get_patient_context(
        self,
        patient_id: str
    ) -> IntegrationResponse:
        """Fetch patient history and context from PMS"""
        pass
    
    @abstractmethod
    def create_appointment(
        self,
        patient_id: str,
        appointment_details: Dict[str, Any]
    ) -> IntegrationResponse:
        """Create follow-up appointment"""
        pass


class PharmacyAdapter(BaseAdapter):
    """Base adapter for pharmacy systems"""
    
    @abstractmethod
    def send_prescription(
        self,
        patient_id: str,
        prescription: Dict[str, Any]
    ) -> IntegrationResponse:
        """Send prescription to pharmacy"""
        pass
    
    @abstractmethod
    def check_prescription_status(
        self,
        prescription_id: str
    ) -> IntegrationResponse:
        """Check if prescription has been filled"""
        pass


class RadiologyAdapter(BaseAdapter):
    """Base adapter for radiology/imaging systems"""
    
    @abstractmethod
    def order_imaging(
        self,
        patient_id: str,
        imaging_order: Dict[str, Any]
    ) -> IntegrationResponse:
        """Order imaging study"""
        pass
    
    @abstractmethod
    def check_imaging_status(
        self,
        order_id: str
    ) -> IntegrationResponse:
        """Check imaging order status"""
        pass


class LabAdapter(BaseAdapter):
    """Base adapter for laboratory systems"""
    
    @abstractmethod
    def order_lab_test(
        self,
        patient_id: str,
        lab_order: Dict[str, Any]
    ) -> IntegrationResponse:
        """Order laboratory test"""
        pass
    
    @abstractmethod
    def get_lab_results(
        self,
        order_id: str
    ) -> IntegrationResponse:
        """Retrieve lab results"""
        pass


class HealthLinkAdapter(BaseAdapter):
    """Base adapter for HealthLink (NZ health information exchange)"""
    
    @abstractmethod
    def send_referral(
        self,
        patient_id: str,
        referral: Dict[str, Any]
    ) -> IntegrationResponse:
        """Send referral via HealthLink"""
        pass
    
    @abstractmethod
    def send_discharge_summary(
        self,
        patient_id: str,
        summary: Dict[str, Any]
    ) -> IntegrationResponse:
        """Send discharge summary"""
        pass
    
    @abstractmethod
    def check_message_status(
        self,
        message_id: str
    ) -> IntegrationResponse:
        """Check if message was delivered"""
        pass


class NotificationAdapter(BaseAdapter):
    """Base adapter for notifications (email/SMS)"""
    
    @abstractmethod
    def send_notification(
        self,
        recipient: str,
        message: str,
        notification_type: str
    ) -> IntegrationResponse:
        """Send notification"""
        pass
