# Clinical Recorder v2.0 - Process Walkthrough

**Complete patient journey from arrival to handover**

This document explains what happens at each step of the clinical workflow and which files handle each part.

---

## 🏥 Patient Journey Overview

```
Patient Arrives → Consent → Recording → AI Processing → Approval → 
Task Routing → Integration → Notifications → Task Tracking → History
```

---

## Step-by-Step Process

### **1. Patient Arrives at Clinic**

**What Happens:**
- Clinician opens the dashboard in their browser
- Sees list of patients, pending tasks, and consultation history
- Clicks "Start New Consultation"

**Files Involved:**
- `frontend/dashboard.html` - The web interface clinicians interact with
- `frontend/api-service.js` - Handles API communication between browser and AWS

**Technical Flow:**
```
Browser → dashboard.html → api-service.js → Lambda API
```

---

### **2. Clinician Obtains Consent**

**What Happens:**
- Clinician explains recording to patient
- Patient verbally consents
- Clinician clicks "Record Consent" in dashboard
- System logs consent with timestamp

**Files Involved:**
- `integrations/aws_notifications.py` - Records consent in DynamoDB
- `storage/dynamodb/enhanced_storage.py` - Stores consent record

**Technical Flow:**
```
Dashboard → Lambda API → aws_notifications.py → DynamoDB
```

**Compliance:**
- Privacy Act 2020 requirement
- Audit trail created
- Consent linked to patient ID

---

### **3. Recording the Consultation**

**What Happens:**
- Clinician clicks "Start Recording"
- Browser records audio (5-10 minutes typical)
- Audio uploaded to secure S3 bucket
- Processing pipeline triggered

**Files Involved:**
- `backend/api_lambda_enhanced.py` - Generates secure S3 upload URL
- S3 bucket - Stores encrypted audio file
- SQS queue - Triggers processing worker

**Technical Flow:**
```
Browser → Lambda (/get-upload-url) → S3 presigned URL
Browser → S3 (direct upload)
Browser → Lambda (/upload-complete) → SQS message
```

**Security:**
- Audio encrypted at rest (S3 encryption)
- Presigned URLs expire after 1 hour
- No audio stored on clinician's device

---

### **4. AI Processing**

**What Happens:**
- EC2 worker picks up audio file from S3
- Whisper AI transcribes speech to text
- AWS Bedrock extracts structured data:
  - SOAP notes (Subjective, Objective, Assessment, Plan)
  - Diagnoses (ICD-10 codes)
  - Medications (dosage, frequency)
  - Tasks (prescriptions, imaging, labs, referrals)
  - Red flags (urgent issues)

**Files Involved:**
- `docker/whisper_api/worker_openai.py` - Main processing worker
- AWS Bedrock - AI extraction service
- `storage/dynamodb/enhanced_storage.py` - Stores results

**Technical Flow:**
```
SQS → EC2 Worker → Whisper API (transcription)
EC2 Worker → Bedrock (AI extraction)
EC2 Worker → DynamoDB (save results with status: pending_approval)
```

**Processing Time:**
- Transcription: ~30 seconds for 5-minute audio
- AI extraction: ~10 seconds
- Total: ~40 seconds

**Cost:**
- Whisper: $0.006 per consultation
- Bedrock: $0.020 per consultation

---

### **5. Awaiting Approval**

**What Happens:**
- Dashboard shows notification: "Consultation ready for review"
- Clinician clicks "Review"
- Sees AI-generated notes side-by-side with transcription
- Can edit any field before approval

**Files Involved:**
- `backend/api_lambda_enhanced.py` - `/approvals/pending` endpoint
- `storage/dynamodb/enhanced_storage.py` - Retrieves pending consultations
- `frontend/dashboard.html` - Displays review interface

**Technical Flow:**
```
Dashboard → Lambda (/approvals/pending) → DynamoDB query
DynamoDB → Lambda → Dashboard (displays consultation)
```

**Safety Features:**
- Human-in-the-loop approval required
- Red flags highlighted in red
- Missing information alerts
- Edit capability before finalization

---

### **6. Clinician Reviews and Approves**

**What Happens:**
- Clinician reviews all extracted data
- Makes any necessary edits
- Clicks "Approve" or "Reject"
- If approved: triggers automation layer
- If rejected: consultation marked for re-review

**Files Involved:**
- `backend/api_lambda_enhanced.py` - `/approvals/approve` or `/approvals/reject` endpoints
- `storage/dynamodb/enhanced_storage.py` - Updates consultation status
- `automation/task_router.py` - Routes tasks to integrations

**Technical Flow:**
```
Dashboard → Lambda (/approvals/approve) → DynamoDB (update status)
Lambda → task_router.py (process tasks)
task_router.py → Integration adapters
```

**Approval Actions:**
- Status changed: `pending_approval` → `approved`
- Timestamp recorded
- Clinician ID logged (audit trail)
- Tasks extracted and routed

---

### **7. Task Routing (Automation Layer)**

**What Happens:**
- System reads approved consultation
- Identifies tasks:
  - Prescriptions → Pharmacy
  - Imaging orders → Radiology
  - Lab tests → Laboratory
  - Referrals → HealthLink
  - PMS notes → Medtech
- Routes each task to appropriate adapter

**Files Involved:**
- `automation/task_router.py` - Intelligent task routing logic
- `integrations/base_adapter.py` - Base interface for all adapters

**Technical Flow:**
```
task_router.py → Reads consultation
task_router.py → Identifies task types
task_router.py → Calls appropriate adapter for each task
```

**Current Behavior (INTEGRATIONS_ENABLED=false):**
- Tasks created in DynamoDB with status: `pending`
- Clinician completes manually
- System tracks completion

**Future Behavior (INTEGRATIONS_ENABLED=true):**
- Tasks sent automatically to external systems
- System tracks success/failure
- Retries on failure

---

### **8. Integration Adapters (Currently Dormant)**

**What Happens:**
- Each adapter handles communication with external system
- Formats data according to system requirements
- Handles authentication, retries, errors
- Reports success/failure back to task router

**Files Involved:**

#### `integrations/medtech_adapter.py`
- **Purpose:** Save consultation notes to Medtech PMS
- **Status:** Dormant (waiting for API key)
- **Future:** Automatic note saving

#### `integrations/pharmacy_adapter.py`
- **Purpose:** Send prescriptions to pharmacy system
- **Status:** Dormant
- **Future:** Automatic prescription delivery

#### `integrations/radiology_adapter.py`
- **Purpose:** Book imaging appointments
- **Status:** Dormant
- **Future:** Automatic radiology booking

#### `integrations/lab_adapter.py`
- **Purpose:** Submit lab test orders
- **Status:** Dormant
- **Future:** Automatic lab ordering

#### `integrations/healthlink_adapter.py`
- **Purpose:** Send referrals to specialists
- **Status:** Dormant
- **Future:** Automatic referral delivery via HealthLink

**Technical Flow (when enabled):**
```
task_router.py → medtech_adapter.py → Medtech API
task_router.py → pharmacy_adapter.py → Pharmacy API
task_router.py → radiology_adapter.py → Radiology API
task_router.py → lab_adapter.py → Lab API
task_router.py → healthlink_adapter.py → HealthLink API
```

**Error Handling:**
- Retry logic (3 attempts)
- Exponential backoff
- Fallback to manual task if all retries fail
- Error notifications to clinician

---

### **9. Notifications Sent**

**What Happens:**
- System sends email to clinician with task summary
- Example: "3 pending tasks for John Doe"
- Can also send SMS (if enabled)

**Files Involved:**
- `integrations/aws_notifications.py` - Email/SMS sending

**Technical Flow:**
```
task_router.py → aws_notifications.py → AWS SES (email)
task_router.py → aws_notifications.py → AWS SNS (SMS)
```

**Current Status:**
- ✅ Email notifications work immediately (AWS SES)
- ⏸️ SMS notifications available (AWS SNS, disabled by default)

**Configuration:**
```bash
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_SMS_NOTIFICATIONS=false
SES_FROM_EMAIL=noreply@yourdomain.com
```

---

### **10. Task Tracking**

**What Happens:**
- Dashboard shows all pending tasks
- Clinician sees: task type, patient, due date, status
- Clicks checkbox to mark task complete
- System updates task status

**Files Involved:**
- `backend/api_lambda_enhanced.py` - `/tasks/pending` and `/tasks/update` endpoints
- `storage/dynamodb/enhanced_storage.py` - Task storage and retrieval
- `frontend/dashboard.html` - Task list interface

**Technical Flow:**
```
Dashboard → Lambda (/tasks/pending) → DynamoDB query
Dashboard displays task list
Clinician clicks "Complete" → Lambda (/tasks/update) → DynamoDB update
```

**Task States:**
- `pending` - Awaiting action
- `in_progress` - Being worked on
- `completed` - Finished
- `failed` - Error occurred (integration mode only)

---

### **11. Patient History**

**What Happens:**
- System links all consultations to patient ID
- Clinician clicks patient name in dashboard
- Sees complete timeline:
  - Previous consultations
  - Diagnoses history
  - Medication history
  - Past tasks

**Files Involved:**
- `backend/api_lambda_enhanced.py` - `/patient/{id}` endpoint
- `storage/dynamodb/enhanced_storage.py` - Patient history retrieval
- `frontend/dashboard.html` - History display

**Technical Flow:**
```
Dashboard → Lambda (/patient/TEST001) → DynamoDB query
DynamoDB → Lambda → Dashboard (displays timeline)
```

**Future Enhancement:**
- Pre-load patient history before consultation starts
- Show relevant past diagnoses during recording
- Medication interaction warnings

---

### **12. End of Shift - Handover**

**What Happens:**
- Clinician clicks "Generate Handover Report"
- System creates summary:
  - Patients seen today
  - Pending tasks
  - Outstanding items
  - Red flags requiring follow-up
- Report displayed and can be printed/emailed

**Files Involved:**
- `backend/api_lambda_enhanced.py` - `/handover` endpoint
- `storage/dynamodb/enhanced_storage.py` - Aggregates shift data

**Technical Flow:**
```
Dashboard → Lambda (/handover?date=2026-03-03) → DynamoDB query
Lambda aggregates data → Returns formatted report
Dashboard displays report
```

**Report Contents:**
- Total consultations: 12
- Pending approvals: 2
- Pending tasks: 5
- Red flags: 1 (urgent follow-up needed)

---

### **13. Audit & Compliance**

**What Happens (Background):**
- Every action logged automatically
- Tracks: who, what, when, where
- Immutable audit trail
- Required for Privacy Act 2020 compliance

**Files Involved:**
- `storage/dynamodb/enhanced_storage.py` - Audit logging

**What's Logged:**
- Consent obtained (timestamp, clinician)
- Recording started/stopped
- AI processing completed
- Consultation approved/rejected (who, when)
- Tasks created/completed
- Patient history accessed (who, when)
- Data modifications (before/after values)

**Compliance Standards:**
- Privacy Act 2020 (NZ)
- HISO 10029 (Clinical documentation)
- HISO 10064 (Audit trail requirements)

---

## Configuration & Control

### Feature Flags

**File: `config/settings.py`**

Controls system behavior via environment variables:

```python
# Master switch
INTEGRATIONS_ENABLED = false  # Manual mode (current)

# Individual integrations (only active if INTEGRATIONS_ENABLED=true)
ENABLE_MEDTECH = false
ENABLE_PHARMACY = false
ENABLE_RADIOLOGY = false
ENABLE_LAB = false
ENABLE_HEALTHLINK = false

# Notifications (work immediately)
ENABLE_EMAIL_NOTIFICATIONS = true
ENABLE_SMS_NOTIFICATIONS = false
```

**Current Mode:** Manual workflow
- Tasks created in system
- Clinician completes manually
- Full tracking and history

**Future Mode:** Automatic workflow
- Tasks sent to external systems automatically
- Human approval still required before automation
- Fallback to manual if integration fails

---

## System Architecture Summary

### Data Flow

```
┌─────────────┐
│   Browser   │ (dashboard.html, api-service.js)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Lambda API  │ (api_lambda_enhanced.py)
└──────┬──────┘
       │
       ├─────────────────┬─────────────────┬─────────────────┐
       ▼                 ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  DynamoDB   │   │   S3 + SQS  │   │ Task Router │   │Notifications│
│ (Storage)   │   │ (Processing)│   │ (Automation)│   │  (AWS SES)  │
└─────────────┘   └──────┬──────┘   └──────┬──────┘   └─────────────┘
                         │                 │
                         ▼                 ▼
                  ┌─────────────┐   ┌─────────────┐
                  │ EC2 Worker  │   │ Integration │
                  │(Whisper+AI) │   │  Adapters   │
                  └─────────────┘   └──────┬──────┘
                                           │
                                           ▼
                                    ┌─────────────┐
                                    │  External   │
                                    │  Systems    │
                                    │  (Dormant)  │
                                    └─────────────┘
```

### File Responsibilities

| File | Purpose | Status |
|------|---------|--------|
| `frontend/dashboard.html` | Web UI | ✅ Active |
| `frontend/api-service.js` | API client | ✅ Active |
| `backend/api_lambda_enhanced.py` | Main API | ✅ Active |
| `storage/dynamodb/enhanced_storage.py` | Data persistence | ✅ Active |
| `docker/whisper_api/worker_openai.py` | AI processing | ✅ Active |
| `automation/task_router.py` | Task routing | ✅ Active (manual mode) |
| `integrations/base_adapter.py` | Adapter interface | ✅ Ready |
| `integrations/aws_notifications.py` | Email/SMS | ✅ Active |
| `integrations/medtech_adapter.py` | Medtech PMS | ⏸️ Dormant |
| `integrations/pharmacy_adapter.py` | Pharmacy | ⏸️ Dormant |
| `integrations/radiology_adapter.py` | Radiology | ⏸️ Dormant |
| `integrations/lab_adapter.py` | Laboratory | ⏸️ Dormant |
| `integrations/healthlink_adapter.py` | HealthLink | ⏸️ Dormant |
| `config/settings.py` | Feature flags | ✅ Active |

---

## Key Differences: Old vs New System

### Old System
```
Audio → Transcription → Done
```
- No approval workflow
- No task management
- No patient history
- No integrations
- No compliance tracking

### New System
```
Audio → Transcription → Approval → Task Routing → Integration → Tracking
```
- ✅ Human-in-the-loop approval
- ✅ Complete task management
- ✅ Patient timeline
- ✅ Integration layer (ready for automation)
- ✅ Full compliance (Privacy Act 2020, HISO)
- ✅ Audit trail
- ✅ Notifications

---

## Cost Breakdown

### Per Consultation (~5 minutes)

| Component | Cost | File Responsible |
|-----------|------|------------------|
| Whisper transcription | $0.006 | `worker_openai.py` |
| Bedrock AI extraction | $0.020 | `worker_openai.py` |
| S3 storage | $0.0001 | AWS S3 |
| DynamoDB operations | $0.0001 | `enhanced_storage.py` |
| Lambda execution | $0.0001 | `api_lambda_enhanced.py` |
| SES email | $0.0001 | `aws_notifications.py` |
| **Total** | **~$0.026** | |

### Monthly (100 consultations)
- **Total:** ~$2.60/month
- **Per patient:** ~$0.03

---

## Testing the System

### Check Integration Status
```bash
curl https://your-api-url/integration/status
```

### Check Pending Approvals
```bash
curl https://your-api-url/approvals/pending
```

### Check Patient History
```bash
curl https://your-api-url/patient/TEST001
```

### Check Pending Tasks
```bash
curl https://your-api-url/tasks/pending
```

### Generate Handover Report
```bash
curl https://your-api-url/handover?date=2026-03-03
```

---

## Future Enhancements

### When Integrations Enabled

1. **Pre-consultation Context**
   - Load patient history before consultation starts
   - Display previous diagnoses, medications
   - Show relevant alerts

2. **Real-time Automation**
   - Prescriptions sent to pharmacy immediately after approval
   - Imaging appointments booked automatically
   - Lab orders submitted instantly
   - Referrals delivered via HealthLink

3. **Advanced Features**
   - Mobile app for on-the-go access
   - Real-time collaboration (multiple clinicians)
   - Analytics dashboard (consultation trends, common diagnoses)
   - Multi-clinic support

---

## Security & Privacy

### Data Protection
- Audio encrypted at rest (S3)
- Data encrypted in transit (HTTPS)
- Presigned URLs expire after 1 hour
- No data stored on clinician devices

### Access Control
- Clinician authentication required
- Role-based access (future)
- Audit trail of all access

### Compliance
- Privacy Act 2020 (NZ)
- HISO 10029 (Clinical documentation)
- HISO 10064 (Audit trails)
- Consent tracking
- Data retention policies

---

## Support & Troubleshooting

### Check Lambda Logs
```bash
aws logs tail /aws/lambda/clinical-recorder-api --follow
```

### Check Worker Logs
```bash
ssh ec2-worker
tail -f /var/log/whisper-worker.log
```

### Common Issues

**Problem:** Consultation stuck in "processing"
- **Check:** EC2 worker status
- **File:** `worker_openai.py`

**Problem:** Tasks not appearing
- **Check:** `INTEGRATIONS_ENABLED` flag
- **File:** `config/settings.py`

**Problem:** Email notifications not sending
- **Check:** SES email verification
- **File:** `aws_notifications.py`

---

## Summary

The Clinical Recorder v2.0 system provides a complete clinical workflow automation solution:

1. **Works Today** - Full functionality in manual mode
2. **Future-Proof** - Ready for automation when API access obtained
3. **Compliant** - Privacy Act 2020, HISO standards
4. **Cost-Effective** - ~$0.03 per consultation
5. **Scalable** - Serverless architecture
6. **Secure** - Encryption, audit logging, consent tracking

**Built for New Zealand healthcare. Ready to transform clinical workflows.**
