# Complete Guide: Clinical Recorder System

## Table of Contents
1. [System Overview](#system-overview)
2. [User Interface](#user-interface)
3. [Data Flow](#data-flow)
4. [Technical Architecture](#technical-architecture)
5. [SOAP Notes Structure](#soap-notes-structure)
6. [Follow-up Tasks](#follow-up-tasks)
7. [PDF Generation](#pdf-generation)
8. [Configuration](#configuration)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

---

## System Overview

### What is the Clinical Recorder?

The Clinical Recorder is an AI-powered system that transcribes clinical consultations and extracts comprehensive structured data. Built for New Zealand healthcare professionals including GPs, hospital doctors, and nurses.

**Key Features:**
- **Single AI Pass**: One Bedrock call extracts everything (cost-efficient)
- **Comprehensive Output**: SOAP notes, follow-up tasks, handover notes
- **3-Button Interface**: PDF download, task management, full JSON access
- **Multi-Context Support**: Clinic, hospital, ED, nursing home consultations
- **Professional PDF**: Formatted consultation notes with SOAP structure
- **Task Automation**: Structured data ready for system integration

### How It Works

1. **Record**: Healthcare professional records consultation audio
2. **Upload**: Audio uploaded to secure cloud storage
3. **Process**: AI transcribes and extracts structured clinical data
4. **Present**: Results shown as 3 actionable buttons
5. **Act**: Download PDF, manage tasks, or access full data

---

## User Interface

### 3-Button Interface

After processing completes, users see three buttons:

#### 1. Download PDF Button
- **Purpose**: Get professional consultation notes
- **Content**: Complete SOAP notes, handover, follow-up tasks
- **Format**: Medical-grade PDF with facility header
- **Use Cases**: Clinical records, patient files, handover documentation

#### 2. Follow-up Tasks Button
- **Purpose**: View and manage actionable items
- **Summary**: Shows total tasks and urgent count
- **Details**: Each task includes:
  - Description and urgency level
  - Assigned role (nurse, doctor, pharmacy, etc.)
  - Due date/time
  - Complete automation data
- **Use Cases**: Task assignment, workflow management, system integration

#### 3. Full JSON Button
- **Purpose**: Access complete structured data
- **Content**: 
  - Original transcript
  - Complete SOAP notes
  - All follow-up tasks with automation data
  - FHIR bundle
  - Processing metadata
- **Use Cases**: System integration, data analysis, audit trail

### Task Management Interface

When clicking on Follow-up Tasks:

**Task Summary View:**
```
5 Follow-up Tasks (2 urgent)

[STAT] Perform ECG immediately → nurse
[URGENT] Blood tests - troponin, FBC → nurse  
[URGENT] Chest X-ray → radiology
[ROUTINE] Aspirin 300mg stat → nurse
[ROUTINE] Cardiology referral → doctor
```

**Task Detail View:**
```
Task: Perform ECG immediately
Evidence: "I'm going to order an ECG right now"
Owner: nurse
Due: immediately
Status: proposed

Automation Data:
- Test Name: 12-lead ECG
- Sample Type: N/A
- Urgency: stat
- Location: Room 1, clinic
```

---

## Data Flow

### Complete Process Flow

```
1. Browser Records Audio
   ↓
2. API Gateway → Lambda: Get presigned S3 URL
   ↓
3. Browser → S3: Upload audio file
   ↓
4. Browser → API: Trigger processing
   ↓
5. Lambda → SQS: Queue processing job
   ↓
6. EC2 Worker: Poll SQS queue
   ↓
7. Worker → S3: Download audio
   ↓
8. Worker: Apply VAD (remove silence)
   ↓
9. Worker → Whisper API: Transcribe audio
   ↓ Returns: Plain text transcript
10. Worker → Bedrock: SINGLE COMPREHENSIVE CALL
    ↓ Input: Transcript + comprehensive prompt
    ↓ Output: Complete ConsultationArtifact JSON
    ↓ Contains: SOAP notes, tasks, handover, safety flags
11. Worker: Generate PDF (DETERMINISTIC - NO AI)
    ↓ Uses: consultation_artifact + template
    ↓ Output: Professional PDF
12. Worker: Generate FHIR Bundle (DETERMINISTIC - NO AI)
    ↓ Uses: consultation_artifact
13. Worker → DynamoDB: Save structured data
14. Worker → WebSocket: Notify completion
15. Worker: Cleanup (delete audio, SQS message)
16. Browser polls API → Gets 3-button interface
```

### Single AI Pass Constraint

**Bedrock Called Once:**
- Input: Complete transcript
- Output: Comprehensive structured JSON
- Contains: Everything needed for downstream processing

**All Other Steps Are Deterministic:**
- PDF generation: Template-based (ReportLab)
- FHIR generation: Data transformation
- Task extraction: JSON parsing
- Storage: Structure preservation

---

## Technical Architecture

### AWS Services Used

| Service | Purpose | Cost Impact |
|---------|---------|-------------|
| **S3** | Audio + PDF storage | ~$0.0001/consultation |
| **DynamoDB** | Structured data storage | ~$0.0001/consultation |
| **SQS** | Job queue | ~$0.0001/consultation |
| **Lambda** | API endpoints | ~$0.0001/consultation |
| **API Gateway** | HTTP API | ~$0.0001/consultation |
| **EC2** | Worker processing | ~$0.05/hour |
| **Bedrock** | AI extraction | ~$0.020/consultation |
| **Whisper API** | Transcription | ~$0.006/consultation |

**Total Cost:** ~$0.026 per consultation

### Project Structure

```
Transcriber/
├── backend/                    # AWS Lambda functions
│   ├── api_lambda_clean.py    # Main API (returns 3-button interface)
│   └── websocket_handler.py   # WebSocket connections
├── shared/
│   └── schemas/
│       └── consultation_artifact_schema.json  # JSON schema
├── analysis/
│   └── prompts/
│       └── bedrock_prompt.py  # Comprehensive AI prompt
├── storage/
│   └── dynamodb/
│       └── consultation_storage.py  # DynamoDB helpers
├── pdf/
│   └── templates/
│       └── consultation_pdf.py  # PDF generator
├── docker/whipser_api/        # EC2 worker container
│   ├── worker_openai.py       # Main processing logic
│   └── Dockerfile             # Container definition
└── test_consultation_system.py  # Test suite
```

### DynamoDB Schema

```json
{
  "audio_key": "uploads/test_xxx.webm",  // Partition key
  "consultation_artifact": {             // Complete nested structure
    "version": "2.0",
    "metadata": {...},
    "soap_notes": {...},
    "follow_up_tasks": [...],
    "handover": {...}
  },
  "follow_up_tasks": [...],              // Duplicate for easy access
  "pending_task_count": 5,               // Query optimization
  "urgent_task_count": 2,                // Query optimization
  "pdf_url": "https://s3.../test.pdf",   // PDF download link
  "artifact_version": "2.0",             // Version tracking
  // Legacy fields for backward compatibility
  "diagnosis": "...",
  "medications": [...],
  "tasks": [...]
}
```

---

## SOAP Notes Structure

### Complete SOAP Format

The AI extracts comprehensive SOAP (Subjective, Objective, Assessment, Plan) notes:

#### Subjective
- **Chief Complaint**: Primary reason for consultation
- **History of Presenting Complaint**: Detailed narrative
- **Symptoms**: Onset, duration, severity, characteristics
- **Past Medical History**: Relevant conditions
- **Current Medications**: With doses and indications
- **Allergies**: With reaction types and severity
- **Social History**: Smoking, alcohol, occupation, living situation
- **Family History**: Relevant family conditions
- **Functional Status**: Mobility, ADLs, cognitive status

#### Objective
- **Vital Signs**: BP, HR, temp, RR, O2 sats, weight, pain score, GCS
- **Physical Examination**: By system with findings and abnormalities
- **Investigations**: Lab results, imaging results with interpretations
- **Lines and Devices**: IV lines, catheters, drains, monitors
- **Fluid Balance**: Input/output if applicable

#### Assessment
- **Primary Diagnosis**: Main working diagnosis
- **Differential Diagnoses**: With likelihood and reasoning
- **Problem List**: Active issues with status and priority
- **Clinical Impression**: Overall assessment and reasoning
- **Severity Assessment**: Stable, improving, deteriorating, critical
- **Prognosis**: Expected outcome

#### Plan
- **Treatment Plan**: Overall strategy
- **Medications Prescribed**: Drug, dose, route, frequency, duration, indication
- **Investigations Ordered**: Tests with urgency and indication
- **Referrals**: Specialty, urgency, reason
- **Patient Education**: Advice given
- **Follow-up**: Required timeframe and reason
- **Safety Netting**: Red flags to watch for
- **Escalation Criteria**: When to seek urgent care
- **Discharge Planning**: Date, destination, criteria, medications, equipment

---

## Follow-up Tasks

### Task Types Supported

1. **Prescriptions**
   - Medication, dose, route, frequency, duration
   - Indication, special instructions
   - Contraindications checking

2. **Imaging Orders**
   - Modality (CT, MRI, X-ray, ultrasound)
   - Body part, contrast requirements
   - Clinical question, urgency

3. **Lab Tests**
   - Test name, sample type
   - Fasting requirements, urgency
   - Special instructions

4. **Nursing Observations**
   - Observation type (vital signs, neuro obs, wound check)
   - Frequency, duration, parameters
   - Escalation criteria

5. **Discharge Planning**
   - Estimated date/time, destination
   - Transport requirements
   - Discharge medications and equipment
   - Follow-up appointments to book

6. **Procedures**
   - Procedure name, location
   - Consent requirements, equipment needed
   - Pre-procedure checks

7. **Referrals**
   - Specialty, urgency, reason
   - Preferred provider if mentioned

8. **Room Bookings**
   - Room type, duration
   - Equipment and staff required

### Task Automation Data

Each task includes complete `required_inputs` for automation:

```json
{
  "task_id": "task-001",
  "task_type": "prescription",
  "description": "Administer aspirin 300mg stat",
  "owner_role": "nurse",
  "urgency": "stat",
  "due_at": "immediately",
  "status": "proposed",
  "transcript_evidence": "I'm going to start you on aspirin 300mg now",
  "required_inputs": {
    "prescription": {
      "medication": "Aspirin",
      "dose": "300mg",
      "route": "PO",
      "frequency": "stat",
      "duration": "once",
      "indication": "chest pain - cardiac precaution",
      "contraindications_checked": true
    }
  }
}
```

### Task Dependencies

Tasks can have dependencies:

```json
{
  "task_id": "task-005",
  "description": "Cardiology referral",
  "dependencies": ["task-001", "task-002"],  // Wait for ECG and bloods
  "status": "proposed"
}
```

---

## PDF Generation

### Professional Medical Document

The PDF generator creates professional consultation notes with:

#### Header Section
- Facility name, address, phone
- Consultation date and type
- Setting (clinic, hospital, ED)
- Specialty and encounter type

#### Clinical Content
- **Red Flags**: Highlighted alerts if present
- **SOAP Sections**: Complete subjective, objective, assessment, plan
- **Vital Signs Table**: Formatted vital signs
- **Follow-up Tasks**: Grouped by urgency (STAT, Urgent, Routine)

#### Handover Section (Separate Page)
- **SBAR Format**: Situation, Background, Assessment, Recommendation
- **Active Issues**: Current problems
- **Escalation Criteria**: When to call for help
- **Next Review Time**: When to reassess

#### Footer
- Generation timestamp
- Disclaimer about automated generation

### Styling Features
- Medical blue color scheme
- Clear section headers
- Tables for structured data
- Bullet points for lists
- Red text for alerts and red flags
- Professional fonts (Helvetica)

---

## Configuration

### Environment Variables (EC2 Worker)

```bash
AWS_REGION=ap-southeast-2
QUEUE_URL=https://sqs.ap-southeast-2.amazonaws.com/.../clinical-processing-queue
TABLE_NAME=clinical-results
BUCKET_NAME=clinical-audio-uploads
OPENAI_API_KEY=sk-...
```

### Bedrock Prompt Configuration

Located in `analysis/prompts/bedrock_prompt.py`:

**Key Settings:**
- Model: `anthropic.claude-3-haiku-20240307-v1:0`
- Max tokens: 8000 (for comprehensive output)
- Temperature: 0.1 (for consistency)
- System prompt: Defines medical AI role and NZ context
- User prompt: Complete JSON schema with examples

### PDF Configuration

Located in `pdf/templates/consultation_pdf.py`:

**Customizable Elements:**
- Facility information (name, address, phone)
- Color scheme and fonts
- Section layouts and styling
- Page margins and spacing

---

## Deployment

### Prerequisites

- AWS Account with appropriate permissions
- OpenAI API key
- Docker installed locally
- AWS CLI configured

### Build and Deploy

```bash
# 1. Build Docker image
cd docker/whipser_api
docker build -t clinical-worker:latest .

# 2. Push to ECR
aws ecr get-login-password --region ap-southeast-2 | \
  docker login --username AWS --password-stdin <ecr-url>
docker tag clinical-worker:latest <ecr-url>/clinical-worker:latest
docker push <ecr-url>/clinical-worker:latest

# 3. Update EC2 instance
ssh ec2-user@<instance-ip>
docker pull <ecr-url>/clinical-worker:latest
docker stop clinical-worker && docker rm clinical-worker
docker run -d --name clinical-worker \
  --restart unless-stopped \
  -e AWS_REGION=ap-southeast-2 \
  -e QUEUE_URL=<sqs-url> \
  -e TABLE_NAME=clinical-results \
  -e BUCKET_NAME=<bucket-name> \
  -e OPENAI_API_KEY=<key> \
  <ecr-url>/clinical-worker:latest

# 4. Deploy Lambda function
cd backend
zip -r api_lambda.zip api_lambda_clean.py
aws lambda update-function-code \
  --function-name clinical-api \
  --zip-file fileb://api_lambda.zip
```

### Testing

```bash
# Run comprehensive test suite
python test_consultation_system.py

# Test specific components
python -c "from pdf.templates.consultation_pdf import generate_consultation_pdf; print('PDF module OK')"
python -c "from analysis.prompts.bedrock_prompt import get_bedrock_prompt; print('Prompt module OK')"
```

---

## Troubleshooting

### Common Issues

#### Worker Not Processing
**Symptoms:** SQS messages not being consumed
**Solutions:**
1. Check EC2 instance is running: `aws ec2 describe-instances`
2. Check Docker container: `ssh ec2-user@<ip> && docker ps`
3. View worker logs: `docker logs clinical-worker`
4. Verify environment variables: `docker exec clinical-worker env`

#### Bedrock Extraction Fails
**Symptoms:** Error in worker logs, incomplete data in DynamoDB
**Solutions:**
1. Check Bedrock model access in AWS Console
2. Verify IAM permissions for `bedrock:InvokeModel`
3. Check prompt format in `analysis/prompts/bedrock_prompt.py`
4. Review token limits (current: 8000 max tokens)

#### PDF Generation Fails
**Symptoms:** No PDF URL in results, worker errors
**Solutions:**
1. Check reportlab installation: `docker exec clinical-worker pip list | grep reportlab`
2. Verify S3 bucket permissions for PDF upload
3. Check PDF generation logs in worker
4. Test locally: `python test_consultation_system.py`

#### API Returns Wrong Format
**Symptoms:** Frontend gets raw JSON instead of 3-button interface
**Solutions:**
1. Check DynamoDB item has `artifact_version: "2.0"`
2. Verify `consultation_artifact` field exists
3. Check Lambda function logs for API errors
4. Test API endpoint directly: `curl https://api-url/result/test-key`

### Monitoring

#### CloudWatch Metrics to Watch
- **SQS**: `ApproximateNumberOfMessagesVisible` (should be low)
- **EC2**: `CPUUtilization` (should be reasonable)
- **Lambda**: `Invocations`, `Duration`, `Errors`
- **DynamoDB**: `ConsumedReadCapacityUnits`, `ConsumedWriteCapacityUnits`

#### CloudWatch Logs
- `/aws/lambda/clinical-api` - API requests and responses
- `/aws/ec2/clinical-worker` - Worker processing logs
- Custom application logs from worker container

#### Health Checks
```bash
# Check SQS queue depth
aws sqs get-queue-attributes \
  --queue-url <queue-url> \
  --attribute-names ApproximateNumberOfMessages

# Check recent DynamoDB items
aws dynamodb scan \
  --table-name clinical-results \
  --limit 5 \
  --projection-expression "audio_key, artifact_version, pending_task_count"

# Check worker container health
ssh ec2-user@<instance-ip>
docker exec clinical-worker ps aux
docker exec clinical-worker df -h
```

### Performance Optimization

#### Cost Optimization
- Monitor Bedrock token usage
- Adjust max_tokens if responses are truncated
- Consider using Claude Sonnet for complex cases
- Implement audio compression to reduce Whisper costs

#### Speed Optimization
- Use VAD (Voice Activity Detection) to remove silence
- Optimize Docker image size
- Consider multiple worker instances for high volume
- Implement result caching for repeated requests

#### Quality Optimization
- Review and refine Bedrock prompt based on results
- Add validation for extracted data
- Implement confidence scoring
- Create feedback loop for prompt improvement

---

## Summary

The Clinical Recorder provides a comprehensive solution for clinical documentation with:

- **Single AI Pass**: Cost-efficient extraction of all clinical data
- **3-Button Interface**: User-friendly access to PDF, tasks, and full data
- **Professional Output**: Medical-grade PDF consultation notes
- **Task Automation**: Structured data ready for system integration
- **Multi-Context Support**: Works across all healthcare settings
- **FHIR Compliance**: Standards-based healthcare data exchange

The system balances cost efficiency, clinical utility, and technical robustness to provide a practical solution for modern healthcare documentation needs.
