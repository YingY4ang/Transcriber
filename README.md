# Clinical Recorder v2.0

**AI-powered clinical workflow automation system for New Zealand healthcare**

Reduces administrative overhead through intelligent automation while maintaining compliance with NZ healthcare regulations.

---

## 🎯 What This System Does

### Current Capabilities (Works Immediately)

✅ **Record & Transcribe** - Audio recording with AI transcription (Whisper)  
✅ **AI Extraction** - Structured SOAP notes, diagnoses, medications, tasks (Bedrock)  
✅ **Approval Workflow** - Clinician reviews and approves before finalization  
✅ **Task Management** - Track and complete follow-up tasks  
✅ **Patient History** - View complete consultation timeline  
✅ **Email Notifications** - Automatic task notifications via AWS SES  
✅ **Handover Reports** - End-of-shift summaries  
✅ **Consent Tracking** - Privacy Act 2020 compliance  
✅ **Audit Logging** - Complete action trail  

### Future Capabilities (When Integrations Enabled)

🔄 **Auto-save to PMS** - Consultation notes appear in Medtech automatically  
🔄 **Auto-send Prescriptions** - Pharmacy receives orders automatically  
🔄 **Auto-book Imaging** - Radiology appointments created automatically  
🔄 **Auto-order Labs** - Lab tests ordered automatically  
🔄 **Auto-send Referrals** - HealthLink delivers referrals automatically  
🔄 **Pre-consultation Context** - Patient history loaded before consultation  

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLINICAL RECORDER v2.0                        │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Browser    │───▶│  Lambda API  │───▶│   DynamoDB   │      │
│  │  Dashboard   │    │  (Enhanced)  │    │  (Enhanced)  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                    │                    │              │
│         │                    ▼                    │              │
│         │            ┌──────────────┐             │              │
│         │            │  S3 + SQS    │             │              │
│         │            └──────────────┘             │              │
│         │                    │                    │              │
│         │                    ▼                    │              │
│         │            ┌──────────────┐             │              │
│         │            │ EC2 Worker   │             │              │
│         │            │ (Whisper+AI) │             │              │
│         │            └──────────────┘             │              │
│         │                                         │              │
│         └─────────────────────────────────────────┘              │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              INTEGRATION LAYER (Dormant)                   │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │ Medtech  │  │ Pharmacy │  │ Radiology│  │HealthLink│  │  │
│  │  │ Adapter  │  │ Adapter  │  │ Adapter  │  │ Adapter  │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  │  (Ready for API keys - currently dormant)                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         NOTIFICATIONS (Active)                             │  │
│  │  ┌──────────┐  ┌──────────┐                               │  │
│  │  │   SES    │  │   SNS    │                               │  │
│  │  │  Email   │  │   SMS    │                               │  │
│  │  └──────────┘  └──────────┘                               │  │
│  │  (Works immediately with AWS)                             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Transcriber/
├── config/
│   └── settings.py                 # Feature flags & configuration
├── backend/
│   ├── api_lambda_enhanced.py      # Enhanced Lambda API (NEW)
│   └── api_lambda_clean.py         # Original API (legacy)
├── storage/
│   └── dynamodb/
│       ├── consultation_storage.py # Original storage
│       └── enhanced_storage.py     # Approval workflow, history (NEW)
├── integrations/                   # NEW
│   ├── base_adapter.py            # Base interface
│   ├── medtech_adapter.py         # Medtech PMS (ready for API key)
│   ├── aws_notifications.py       # Email/SMS (works now)
│   └── [pharmacy, radiology, lab, healthlink adapters]
├── automation/                     # NEW
│   └── task_router.py             # Intelligent task routing
├── frontend/                       # NEW
│   ├── dashboard.html             # Modern UI
│   └── api-service.js             # API client
├── docker/
│   └── whipser_api/
│       └── worker_openai.py       # Processing worker
├── SETUP_GUIDE.md                 # Complete setup instructions (NEW)
└── README.md                      # This file
```

---

## 🚀 Quick Start

### 1. Deploy Enhanced Backend

```bash
# Package and deploy
cd /Users/thireshannaidoo/Documents/Transcriber
./deploy.sh  # See SETUP_GUIDE.md for details
```

### 2. Configure Environment

```bash
# Set Lambda environment variables
aws lambda update-function-configuration \
    --function-name clinical-recorder-api \
    --environment Variables="{
        INTEGRATIONS_ENABLED=false,
        ENABLE_EMAIL_NOTIFICATIONS=true,
        SES_FROM_EMAIL=noreply@yourdomain.com
    }"
```

### 3. Setup Email Notifications

```bash
# Verify your email in SES
aws ses verify-email-identity --email-address noreply@yourdomain.com
```

### 4. Open Dashboard

```bash
# Update API URL in dashboard.html
# Open frontend/dashboard.html in browser
```

---

## 🎛️ Feature Flags

Control system behavior via environment variables:

```python
# Master switch
INTEGRATIONS_ENABLED = false  # false = Manual mode, true = Automatic mode

# Individual integrations (only active if INTEGRATIONS_ENABLED=true)
ENABLE_MEDTECH = false        # Medtech PMS integration
ENABLE_PHARMACY = false       # Pharmacy system integration
ENABLE_RADIOLOGY = false      # Radiology booking integration
ENABLE_LAB = false            # Lab ordering integration
ENABLE_HEALTHLINK = false     # HealthLink messaging

# Notifications (work immediately)
ENABLE_EMAIL_NOTIFICATIONS = true   # AWS SES
ENABLE_SMS_NOTIFICATIONS = false    # AWS SNS
```

**Current Mode:** Manual workflow (fully functional)  
**Future Mode:** Full automation (when you add API keys)

---

## 📋 API Endpoints

### New Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/approvals/pending` | GET | Get consultations pending approval |
| `/approvals/approve` | POST | Approve consultation |
| `/approvals/reject` | POST | Reject consultation |
| `/patient/{id}` | GET | Get patient consultation history |
| `/tasks/pending` | GET | Get all pending tasks |
| `/tasks/update` | POST | Update task status |
| `/handover` | GET | Generate handover report |
| `/consent/record` | POST | Record patient consent |
| `/consent/check` | GET | Check consent status |
| `/integration/status` | GET | Get integration status |

### Existing Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/config` | GET | Get system configuration |
| `/get-upload-url` | GET | Get S3 presigned URL |
| `/upload-complete` | POST | Trigger processing |
| `/result/{key}` | GET | Get consultation result |

---

## 🔐 Compliance Features

### Privacy Act 2020
- ✅ Consent tracking before recording
- ✅ Data retention policies
- ✅ Audit logging of all access
- ✅ De-identification in storage

### HISO Standards
- ✅ Clinical documentation standards (HISO 10029)
- ✅ Structured data formats
- ✅ Audit trail requirements

### Clinical Safety
- ✅ Human-in-the-loop approval
- ✅ Clinician review before finalization
- ✅ Red flag highlighting
- ✅ Missing information alerts

---

## 🔌 Integration Setup

### When You Get API Access

#### Medtech PMS
```bash
# 1. Contact Medtech for API access
# 2. Set environment variables:
INTEGRATIONS_ENABLED=true
ENABLE_MEDTECH=true
MEDTECH_API_URL=https://api.medtech.co.nz
MEDTECH_API_KEY=your_key
MEDTECH_CLIENT_ID=your_client_id
```

#### HealthLink
```bash
# 1. Apply at https://www.healthlink.net/
# 2. Complete certification
# 3. Set environment variables:
ENABLE_HEALTHLINK=true
HEALTHLINK_API_URL=https://api.healthlink.net
HEALTHLINK_USERNAME=your_username
HEALTHLINK_PASSWORD=your_password
```

See `SETUP_GUIDE.md` for complete instructions.

---

## 💰 Cost Estimate

### Per Consultation (~5 minutes)

| Component | Cost |
|-----------|------|
| Whisper transcription | $0.006 |
| Bedrock AI extraction | $0.020 |
| S3 storage | $0.0001 |
| DynamoDB operations | $0.0001 |
| Lambda execution | $0.0001 |
| SES email (optional) | $0.0001 |
| **Total** | **~$0.026** |

### Monthly (100 consultations)
- **Total:** ~$2.60/month
- **Per patient:** ~$0.03

---

## 🧪 Testing

```bash
# Test integration status
curl https://your-api-url/integration/status

# Test pending approvals
curl https://your-api-url/approvals/pending

# Test patient history
curl https://your-api-url/patient/TEST001

# Test pending tasks
curl https://your-api-url/tasks/pending
```

---

## 📚 Documentation

- **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Complete setup instructions
- **[Detailed Documentation/](./Detailed%20Documentation/)** - Technical details
- **[frontend/dashboard.html](./frontend/dashboard.html)** - UI documentation

---

## 🛠️ Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_consultation_system.py

# Test integrations
python -m integrations.medtech_adapter
```

### Deploy Updates

```bash
# Update Lambda
./deploy.sh

# Update frontend
# Just edit dashboard.html - no build process needed
```

---

## 🎯 Roadmap

### Phase 1: ✅ Complete
- Core transcription & AI extraction
- Approval workflow
- Task management
- Patient history
- Email notifications

### Phase 2: 🔄 In Progress
- Medtech API integration
- HealthLink integration
- Advanced task routing

### Phase 3: 📅 Planned
- Mobile app
- Real-time collaboration
- Analytics dashboard
- Multi-clinic support

---

## 🤝 Support

For issues or questions:
1. Check `SETUP_GUIDE.md`
2. Review Lambda logs: `aws logs tail /aws/lambda/clinical-recorder-api --follow`
3. Check integration status: `curl https://your-api-url/integration/status`

---

## 📄 License

Proprietary - All rights reserved

---

## 🌟 Key Features

- **Fully Functional Today** - Works in manual mode without external integrations
- **Future-Proof** - Ready for automation when you get API access
- **NZ Healthcare Compliant** - Privacy Act 2020, HISO standards
- **Cost-Effective** - ~$0.03 per patient consultation
- **Scalable** - Serverless architecture, handles any load
- **Secure** - Encryption, audit logging, consent tracking

**Built for New Zealand healthcare. Ready to change how clinicians work.**
