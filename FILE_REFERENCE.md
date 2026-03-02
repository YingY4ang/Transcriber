# Complete File Reference - Clinical Recorder v2.0

## Production System Files (What Actually Runs)

### 1. Lambda API (Backend)
**File:** `backend/api_lambda_enhanced.py`
**Purpose:** Main API Gateway Lambda function
**Endpoints:**
- `/config` - System configuration
- `/get-upload-url` - S3 presigned URL for audio upload
- `/upload-complete` - Trigger processing
- `/result/{key}` - Get consultation result
- `/approvals/pending` - Get pending approvals
- `/approvals/approve` - Approve consultation
- `/approvals/reject` - Reject consultation
- `/patient/{id}` - Patient history
- `/tasks/pending` - All pending tasks
- `/tasks/update` - Update task status
- `/handover` - Generate handover report
- `/consent/record` - Record consent
- `/consent/check` - Check consent
- `/integration/status` - Integration status

**Dependencies:**
- `config/settings.py` - Feature flags
- `storage/dynamodb/enhanced_storage.py` - Database operations
- Boto3 for AWS services

**Deployment:** Via `deploy.sh`

---

### 2. EC2 Worker (Processing)
**File:** `docker/whipser_api/worker_openai.py`
**Purpose:** Processes audio files from SQS queue
**Flow:**
1. Polls SQS for new audio uploads
2. Downloads audio from S3
3. Applies VAD (voice activity detection) to remove silence
4. Transcribes with OpenAI Whisper API
5. Sends transcript to AWS Bedrock (Claude) for extraction
6. Generates PDF from extracted data
7. Creates FHIR bundle
8. Saves to DynamoDB with approval_status='pending_approval'
9. Notifies via WebSocket (if configured)
10. Deletes audio from S3
11. Deletes SQS message

**Dependencies:**
- `analysis/prompts/bedrock_prompt.py` - AI prompt
- `pdf/templates/consultation_pdf.py` - PDF generation
- `storage/dynamodb/consultation_storage.py` - Storage helpers
- OpenAI API (Whisper)
- AWS Bedrock (Claude)
- librosa, soundfile (audio processing)

**Deployment:** Docker container on EC2

---

### 3. Frontend Dashboard
**File:** `frontend/dashboard.html`
**Purpose:** Web UI for clinicians
**Features:**
- **Pending Approvals Tab:** Review AI-generated consultations
- **Tasks Tab:** Manage all pending tasks
- **Patients Tab:** Search patient history
- **Record Tab:** Record new consultations with consent

**Dependencies:**
- `frontend/api-service.js` - API client
- Tailwind CSS (via CDN)

**Deployment:** Static HTML file, can be hosted anywhere

---

## Configuration & Settings

### 4. Feature Flags
**File:** `config/settings.py`
**Purpose:** Central configuration for entire system
**Key Settings:**
```python
INTEGRATIONS_ENABLED = false  # Master switch
ENABLE_MEDTECH = false        # Medtech PMS
ENABLE_PHARMACY = false       # Pharmacy
ENABLE_RADIOLOGY = false      # Radiology
ENABLE_LAB = false            # Lab
ENABLE_HEALTHLINK = false     # HealthLink
ENABLE_EMAIL_NOTIFICATIONS = true   # AWS SES
ENABLE_SMS_NOTIFICATIONS = false    # AWS SNS
```

**Functions:**
- `get_integration_status()` - Returns current integration status
- `is_integration_ready(name)` - Checks if integration configured

**Used by:** All backend code, adapters, task router

---

## Database Layer

### 5. Enhanced Storage
**File:** `storage/dynamodb/enhanced_storage.py`
**Purpose:** Database operations for v2.0 features
**Classes:**

**ConsultationStore:**
- `save_consultation_with_approval()` - Save with approval_status
- `approve_consultation()` - Approve and optionally edit
- `get_patient_history()` - All consultations for patient
- `get_pending_approvals()` - All pending approvals
- `get_all_pending_tasks()` - All tasks across patients
- `update_task_status()` - Update task status
- `get_handover_data()` - Generate handover report

**ConsentStore:**
- `record_consent()` - Record patient consent
- `check_consent()` - Check if consent granted

**AuditLog:**
- `log_action()` - Log action for audit trail

**Used by:** `api_lambda_enhanced.py`

---

### 6. Original Storage Helpers
**File:** `storage/dynamodb/consultation_storage.py`
**Purpose:** Helper functions for DynamoDB items
**Functions:**
- `prepare_consultation_item()` - Prepare item with nested structure
- `extract_legacy_format()` - Get legacy flat format
- `extract_artifact()` - Get consultation artifact
- `is_new_format()` - Check if v2.0 format
- `get_task_by_id()` - Get specific task
- `get_tasks_by_owner()` - Filter tasks by role
- `get_urgent_tasks()` - Get urgent tasks
- `update_task_status()` - Update task status

**Used by:** Worker, enhanced_storage.py

---

## Integration Layer

### 7. Base Adapter Interface
**File:** `integrations/base_adapter.py`
**Purpose:** Defines interface for all integrations
**Classes:**
- `IntegrationStatus` - Enum (SUCCESS, FAILED, PENDING, NOT_CONFIGURED)
- `IntegrationResponse` - Standardized response
- `BaseAdapter` - Base class for all adapters
- `PMSAdapter` - Practice Management System interface
- `PharmacyAdapter` - Pharmacy system interface
- `RadiologyAdapter` - Radiology system interface
- `LabAdapter` - Lab system interface
- `HealthLinkAdapter` - HealthLink interface
- `NotificationAdapter` - Notification interface

**Used by:** All adapter implementations

---

### 8. Medtech PMS Adapter
**File:** `integrations/medtech_adapter.py`
**Purpose:** Integration with Medtech Evolution PMS
**Status:** Ready for API credentials (dormant)
**Methods:**
- `test_connection()` - Test API connection
- `save_consultation()` - Save consultation notes to Medtech
- `get_patient_context()` - Fetch patient history from Medtech
- `create_appointment()` - Create follow-up appointment

**Configuration Required:**
- `MEDTECH_API_URL`
- `MEDTECH_API_KEY`
- `MEDTECH_CLIENT_ID`

**Used by:** Task router (when enabled)

---

### 9. AWS Notifications Adapter
**File:** `integrations/aws_notifications.py`
**Purpose:** Email and SMS notifications via AWS
**Status:** WORKS IMMEDIATELY
**Methods:**
- `send_email()` - Send email via SES
- `send_sms()` - Send SMS via SNS
- `send_task_notification()` - Send task notification email
- `send_prescription_notification()` - Send prescription to pharmacy
- `send_referral_notification()` - Send referral notification

**Configuration Required:**
- `SES_FROM_EMAIL` - Verified email in SES
- `SNS_TOPIC_ARN` - SNS topic for SMS (optional)

**Used by:** Task router

---

## Automation Layer

### 10. Task Router
**File:** `automation/task_router.py`
**Purpose:** Routes tasks to appropriate systems
**Modes:**
- **Manual (INTEGRATIONS_ENABLED=false):** Queues tasks, sends email notifications
- **Automatic (INTEGRATIONS_ENABLED=true):** Routes to external systems

**Methods:**
- `route_task()` - Route single task
- `route_all_tasks()` - Route all tasks from consultation
- `_route_prescription()` - Route prescription to pharmacy
- `_route_imaging()` - Route imaging order to radiology
- `_route_lab_test()` - Route lab test to lab
- `_route_referral()` - Route referral via HealthLink
- `_route_appointment()` - Route appointment to PMS
- `_route_nursing_task()` - Route nursing task
- `_route_generic_task()` - Route generic task

**Used by:** After consultation approval (future enhancement)

---

## AI & Analysis

### 11. Bedrock Prompt
**File:** `analysis/prompts/bedrock_prompt.py`
**Purpose:** Prompt template for AI extraction
**Constants:**
- `SYSTEM_PROMPT` - System instructions for Claude
- `build_extraction_prompt(transcript)` - Builds complete prompt

**Output:** Complete ConsultationArtifact JSON with:
- Metadata (consultation context)
- Patient context (de-identified)
- SOAP notes (Subjective, Objective, Assessment, Plan)
- Clinical safety (red flags, risks)
- Follow-up tasks (with automation data)
- Handover (SBAR format)

**Used by:** Worker

---

## PDF Generation

### 12. PDF Template
**File:** `pdf/templates/consultation_pdf.py`
**Purpose:** Generate professional consultation PDFs
**Function:** `generate_consultation_pdf(artifact, output_path, facility_info)`
**Sections:**
- Header with facility info
- Red flags (if any)
- SOAP notes
- Follow-up tasks (grouped by urgency)
- Handover note
- Footer with timestamp

**Dependencies:** ReportLab
**Used by:** Worker

---

## Schemas

### 13. Consultation Artifact Schema
**File:** `shared/schemas/consultation_artifact_schema.json`
**Purpose:** JSON schema for ConsultationArtifact v2.0
**Defines:**
- Complete structure of AI-extracted data
- All required and optional fields
- Data types and formats
- Validation rules

**Used by:** Validation, documentation

---

## Frontend

### 14. API Service
**File:** `frontend/api-service.js`
**Purpose:** JavaScript API client
**Class:** `APIService`
**Methods:**
- `getConfig()` - Get configuration
- `getUploadURL()` - Get S3 upload URL
- `uploadAudio()` - Upload audio to S3
- `triggerProcessing()` - Trigger processing
- `getResult()` - Get consultation result
- `getPendingApprovals()` - Get pending approvals
- `approveConsultation()` - Approve consultation
- `rejectConsultation()` - Reject consultation
- `getPatientHistory()` - Get patient history
- `getPendingTasks()` - Get pending tasks
- `updateTask()` - Update task status
- `getHandover()` - Get handover report
- `recordConsent()` - Record consent
- `checkConsent()` - Check consent
- `getIntegrationStatus()` - Get integration status

**Used by:** `dashboard.html`

---

## Deployment

### 15. Deployment Script
**File:** `deploy.sh`
**Purpose:** Automated Lambda deployment
**Steps:**
1. Create Lambda layer with dependencies
2. Publish layer to AWS
3. Package Lambda function code
4. Update Lambda function code
5. Attach layer to function
6. Set environment variables
7. Update handler to `backend.api_lambda_enhanced.handler`
8. Cleanup temporary files

**Usage:** `./deploy.sh`

---

## Testing

### 16. Test Suite
**File:** `test_consultation_system.py`
**Purpose:** Comprehensive testing
**Tests:**
1. Prompt generation
2. Bedrock request body
3. Artifact structure validation
4. PDF generation
5. DynamoDB item preparation
6. Single Bedrock call constraint

**Usage:** `python test_consultation_system.py`

---

## Documentation

### 17. README
**File:** `README.md`
**Purpose:** Project overview
**Contents:**
- What the system does
- Architecture diagram
- Feature list
- Quick start
- API endpoints
- Cost estimate

---

### 18. Setup Guide
**File:** `SETUP_GUIDE.md`
**Purpose:** Complete setup instructions
**Contents:**
- AWS infrastructure setup
- Lambda deployment
- SES email configuration
- DynamoDB indexes
- Environment variables
- Integration enablement
- Testing procedures

---

### 19. Deployment Checklist
**File:** `DEPLOYMENT_CHECKLIST.md`
**Purpose:** Step-by-step deployment guide
**Contents:**
- Pre-deployment checks
- Deployment steps
- Post-deployment testing
- Troubleshooting
- Success criteria

---

### 20. Quick Start
**File:** `QUICK_START.md`
**Purpose:** 15-minute quick start
**Contents:**
- Minimal deployment steps
- Fast testing
- Next steps

---

## Legacy Files (Kept for Compatibility)

### 21. Original Lambda API
**File:** `backend/api_lambda_clean.py`
**Purpose:** Original Lambda API
**Status:** Kept for backward compatibility
**Endpoints:** Basic endpoints only
**Note:** Can be removed once fully migrated to enhanced API

---

## Dependencies

### 22. Requirements
**File:** `requirements.txt`
**Purpose:** Python dependencies
**Packages:**
- boto3 - AWS SDK
- requests - HTTP requests
- reportlab - PDF generation
- openai - Whisper API
- librosa - Audio processing
- soundfile - Audio I/O
- numpy - Numerical operations
- pytest - Testing

---

## Summary

### Total Files: 22 essential files
- **3 Production files** (API, Worker, Frontend)
- **2 Configuration files** (Settings, Requirements)
- **2 Database files** (Enhanced storage, Helpers)
- **3 Integration files** (Base, Medtech, Notifications)
- **1 Automation file** (Task router)
- **2 AI files** (Prompt, Schema)
- **1 PDF file** (Template)
- **2 Frontend files** (Dashboard, API service)
- **1 Deployment file** (Script)
- **1 Testing file** (Test suite)
- **4 Documentation files** (README, Setup, Checklist, Quick Start)

### All files serve a clear purpose
- No redundancy
- No obsolete code
- Production-ready
- Well-documented
