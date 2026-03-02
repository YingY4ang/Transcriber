"""
Central configuration for Clinical Recorder system.
Feature flags control which capabilities are enabled.
"""

import os
from typing import Dict, Any

# ============================================================================
# FEATURE FLAGS
# ============================================================================

# Master switch for external integrations
# False = Fully functional workflow system (works immediately)
# True = Full automation with external APIs (requires API keys)
INTEGRATIONS_ENABLED = os.environ.get('INTEGRATIONS_ENABLED', 'false').lower() == 'true'

# Individual integration toggles (only active if INTEGRATIONS_ENABLED = True)
ENABLE_MEDTECH = os.environ.get('ENABLE_MEDTECH', 'false').lower() == 'true'
ENABLE_PHARMACY = os.environ.get('ENABLE_PHARMACY', 'false').lower() == 'true'
ENABLE_RADIOLOGY = os.environ.get('ENABLE_RADIOLOGY', 'false').lower() == 'true'
ENABLE_LAB = os.environ.get('ENABLE_LAB', 'false').lower() == 'true'
ENABLE_HEALTHLINK = os.environ.get('ENABLE_HEALTHLINK', 'false').lower() == 'true'

# Notification integrations (work immediately with AWS)
ENABLE_EMAIL_NOTIFICATIONS = os.environ.get('ENABLE_EMAIL_NOTIFICATIONS', 'true').lower() == 'true'
ENABLE_SMS_NOTIFICATIONS = os.environ.get('ENABLE_SMS_NOTIFICATIONS', 'true').lower() == 'true'

# Compliance features
ENABLE_CONSENT_TRACKING = True
ENABLE_AUDIT_LOGGING = True
ENABLE_DATA_RETENTION = True

# ============================================================================
# AWS CONFIGURATION
# ============================================================================

AWS_REGION = os.environ.get('AWS_REGION', 'ap-southeast-2')

# Existing resources
S3_BUCKET = os.environ.get('BUCKET_NAME', 'clinical-audio-bucket')
DYNAMODB_TABLE = os.environ.get('TABLE_NAME', 'clinical-results')
SQS_QUEUE_URL = os.environ.get('QUEUE_URL', 'https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue')
WEBSOCKET_URL = os.environ.get('WEBSOCKET_URL', 'wss://cmxbu5k037.execute-api.ap-southeast-2.amazonaws.com/prod')

# New resources (you'll create these)
EVENTBRIDGE_BUS = os.environ.get('EVENTBRIDGE_BUS', 'clinical-events')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')  # For SMS notifications
SES_FROM_EMAIL = os.environ.get('SES_FROM_EMAIL', 'noreply@clinicalrecorder.com')

# ============================================================================
# INTEGRATION API CREDENTIALS
# ============================================================================

# Medtech API (add when you get access)
MEDTECH_API_URL = os.environ.get('MEDTECH_API_URL', '')
MEDTECH_API_KEY = os.environ.get('MEDTECH_API_KEY', '')
MEDTECH_CLIENT_ID = os.environ.get('MEDTECH_CLIENT_ID', '')

# Pharmacy API
PHARMACY_API_URL = os.environ.get('PHARMACY_API_URL', '')
PHARMACY_API_KEY = os.environ.get('PHARMACY_API_KEY', '')

# Radiology API
RADIOLOGY_API_URL = os.environ.get('RADIOLOGY_API_URL', '')
RADIOLOGY_API_KEY = os.environ.get('RADIOLOGY_API_KEY', '')

# Lab API
LAB_API_URL = os.environ.get('LAB_API_URL', '')
LAB_API_KEY = os.environ.get('LAB_API_KEY', '')

# HealthLink
HEALTHLINK_API_URL = os.environ.get('HEALTHLINK_API_URL', '')
HEALTHLINK_USERNAME = os.environ.get('HEALTHLINK_USERNAME', '')
HEALTHLINK_PASSWORD = os.environ.get('HEALTHLINK_PASSWORD', '')
HEALTHLINK_FACILITY_ID = os.environ.get('HEALTHLINK_FACILITY_ID', '')

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================

# Approval workflow
REQUIRE_CLINICIAN_APPROVAL = True
AUTO_APPROVE_LOW_RISK_TASKS = False  # Future feature

# Task routing
TASK_ROUTING_MODE = 'manual' if not INTEGRATIONS_ENABLED else 'automatic'

# Data retention (days)
AUDIO_RETENTION_DAYS = 30
CONSULTATION_RETENTION_DAYS = 2555  # 7 years (NZ requirement)

# Compliance
REQUIRE_PATIENT_CONSENT = True
REQUIRE_CLINICIAN_SIGNATURE = True

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_integration_status() -> Dict[str, Any]:
    """Get current status of all integrations"""
    return {
        'integrations_enabled': INTEGRATIONS_ENABLED,
        'active_integrations': {
            'medtech': INTEGRATIONS_ENABLED and ENABLE_MEDTECH and bool(MEDTECH_API_KEY),
            'pharmacy': INTEGRATIONS_ENABLED and ENABLE_PHARMACY and bool(PHARMACY_API_KEY),
            'radiology': INTEGRATIONS_ENABLED and ENABLE_RADIOLOGY and bool(RADIOLOGY_API_KEY),
            'lab': INTEGRATIONS_ENABLED and ENABLE_LAB and bool(LAB_API_KEY),
            'healthlink': INTEGRATIONS_ENABLED and ENABLE_HEALTHLINK and bool(HEALTHLINK_USERNAME),
            'email': ENABLE_EMAIL_NOTIFICATIONS,
            'sms': ENABLE_SMS_NOTIFICATIONS and bool(SNS_TOPIC_ARN)
        },
        'mode': TASK_ROUTING_MODE
    }

def is_integration_ready(integration_name: str) -> bool:
    """Check if specific integration is configured and ready"""
    status = get_integration_status()
    return status['active_integrations'].get(integration_name, False)
