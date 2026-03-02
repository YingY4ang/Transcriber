"""
AWS-based notification adapter - WORKS IMMEDIATELY
Uses AWS SES (email) and SNS (SMS)
"""

import boto3
from typing import Dict, Any
from integrations.base_adapter import NotificationAdapter, IntegrationResponse, IntegrationStatus


class AWSNotificationAdapter(NotificationAdapter):
    """
    AWS notification adapter using SES and SNS
    
    SETUP:
    1. Verify email in SES: aws ses verify-email-identity --email-address your@email.com
    2. Create SNS topic: aws sns create-topic --name clinical-notifications
    3. Set environment variables:
       - SES_FROM_EMAIL
       - SNS_TOPIC_ARN
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.region = config.get('region', 'ap-southeast-2')
        self.from_email = config.get('from_email', 'noreply@clinicalrecorder.com')
        self.sns_topic_arn = config.get('sns_topic_arn', '')
        
        self.ses = boto3.client('ses', region_name=self.region)
        self.sns = boto3.client('sns', region_name=self.region)
    
    def get_adapter_name(self) -> str:
        return "AWS Notifications (SES/SNS)"
    
    def test_connection(self) -> IntegrationResponse:
        """Test AWS services"""
        try:
            # Test SES
            self.ses.get_send_quota()
            return IntegrationResponse(
                IntegrationStatus.SUCCESS,
                "AWS notification services ready"
            )
        except Exception as e:
            return IntegrationResponse(
                IntegrationStatus.FAILED,
                "AWS notification test failed",
                error=str(e)
            )
    
    def send_notification(
        self,
        recipient: str,
        message: str,
        notification_type: str = 'email'
    ) -> IntegrationResponse:
        """Send email or SMS notification"""
        if notification_type == 'email':
            return self.send_email(recipient, message)
        elif notification_type == 'sms':
            return self.send_sms(recipient, message)
        else:
            return IntegrationResponse(
                IntegrationStatus.FAILED,
                f"Unknown notification type: {notification_type}"
            )
    
    def send_email(
        self,
        to_email: str,
        message: str,
        subject: str = "Clinical Recorder Notification"
    ) -> IntegrationResponse:
        """Send email via SES"""
        try:
            response = self.ses.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': message}}
                }
            )
            
            return IntegrationResponse(
                IntegrationStatus.SUCCESS,
                "Email sent",
                data={'message_id': response['MessageId']}
            )
        except Exception as e:
            return IntegrationResponse(
                IntegrationStatus.FAILED,
                "Failed to send email",
                error=str(e)
            )
    
    def send_sms(self, phone_number: str, message: str) -> IntegrationResponse:
        """Send SMS via SNS"""
        if not self.sns_topic_arn:
            return IntegrationResponse(
                IntegrationStatus.NOT_CONFIGURED,
                "SNS not configured"
            )
        
        try:
            response = self.sns.publish(
                PhoneNumber=phone_number,
                Message=message
            )
            
            return IntegrationResponse(
                IntegrationStatus.SUCCESS,
                "SMS sent",
                data={'message_id': response['MessageId']}
            )
        except Exception as e:
            return IntegrationResponse(
                IntegrationStatus.FAILED,
                "Failed to send SMS",
                error=str(e)
            )
    
    def send_task_notification(
        self,
        task: Dict[str, Any],
        recipient_email: str
    ) -> IntegrationResponse:
        """Send task notification email"""
        subject = f"[{task.get('urgency', 'ROUTINE').upper()}] New Clinical Task"
        
        message = f"""
New clinical task assigned:

Task: {task.get('description')}
Urgency: {task.get('urgency', 'routine').upper()}
Due: {task.get('due_at', 'Not specified')}
Patient: {task.get('patient_id', 'Unknown')}

Details:
{task.get('transcript_evidence', 'No additional details')}

Please log in to the Clinical Recorder to view full details and mark as complete.
"""
        
        return self.send_email(recipient_email, message, subject)
    
    def send_prescription_notification(
        self,
        prescription: Dict[str, Any],
        pharmacy_email: str
    ) -> IntegrationResponse:
        """Send prescription to pharmacy via email"""
        subject = "New Prescription Order"
        
        message = f"""
New prescription order:

Patient ID: {prescription.get('patient_id')}
Medication: {prescription.get('medication')}
Dose: {prescription.get('dose')}
Route: {prescription.get('route')}
Frequency: {prescription.get('frequency')}
Duration: {prescription.get('duration')}
Repeats: {prescription.get('repeats', 0)}

Indication: {prescription.get('indication')}

Prescriber: {prescription.get('prescriber')}
Date: {prescription.get('date')}
"""
        
        return self.send_email(pharmacy_email, message, subject)
    
    def send_referral_notification(
        self,
        referral: Dict[str, Any],
        specialist_email: str
    ) -> IntegrationResponse:
        """Send referral notification"""
        subject = f"[{referral.get('urgency', 'ROUTINE').upper()}] New Patient Referral"
        
        message = f"""
New patient referral:

Patient ID: {referral.get('patient_id')}
Specialty: {referral.get('specialty')}
Urgency: {referral.get('urgency', 'routine').upper()}

Reason for referral:
{referral.get('reason')}

Clinical summary:
{referral.get('clinical_summary', 'See attached')}

Referring clinician: {referral.get('referring_clinician')}
Contact: {referral.get('contact_info')}
"""
        
        return self.send_email(specialist_email, message, subject)
