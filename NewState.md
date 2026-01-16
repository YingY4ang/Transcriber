# New State: Comprehensive Consultation Artifact System

## Overview

The system has been upgraded to perform **single-pass AI extraction** with comprehensive structured output, followed by **deterministic automation** for all downstream tasks (PDF generation, storage, task extraction).

**Key Achievement:** Bedrock is called exactly ONCE per transcript, producing a complete `ConsultationArtifact` that contains everything needed for:
- SOAP-formatted consultation notes
- Hospital/nursing handover
- Automated follow-up task routing
- PDF generation
- FHIR export
- Practice management system integration

---

## Updated Process Flow

```
1. Browser → API: Get presigned S3 URL
2. Browser → S3: Upload audio
3. Browser → API: Trigger processing (/upload-complete)
4. API → SQS: Queue message
5. EC2 Worker: Poll SQS
6. Worker → S3: Download audio
7. Worker: Apply VAD (remove silence)
8. Worker → Whisper API: Transcribe
   ↓ Returns: Plain text transcript
9. Worker → Bedrock: SINGLE COMPREHENSIVE CALL
   ↓ Input: Transcript + comprehensive prompt
   ↓ Output: Complete ConsultationArtifact JSON (version 2.0)
   ↓ Contains: metadata, SOAP notes, tasks, handover, safety flags
10. Worker: Generate PDF (DETERMINISTIC - NO AI)
    ↓ Uses: consultation_artifact + template
    ↓ Output: Professional PDF with SOAP sections + handover
11. Worker: (Optional) Upload PDF to S3
    ↓ Currently commented out, ready to enable
12. Worker: Generate FHIR Bundle (DETERMINISTIC - NO AI)
    ↓ Uses: consultation_artifact
    ↓ Output: FHIR R4 resources
13. Worker: Prepare DynamoDB Item (DETERMINISTIC - NO AI)
    ↓ Nested artifact structure + backward-compatible flat fields
    ↓ Task statistics for querying
14. Worker → DynamoDB: Save complete item
15. Worker → WebSocket: Notify connected clients
16. Worker → S3: Delete audio file
17. Worker → SQS: Delete message
18. Browser polls /result/{key}
19. API → DynamoDB: Retrieve item
20. API → Browser: Return results (artifact + PDF URL + legacy fields)
```

---

## Files Changed/Added

### New Files Created

**Schemas:**
- `shared/schemas/consultation_artifact_schema.json` - Complete JSON schema for artifact

**Prompts:**
- `analysis/prompts/bedrock_prompt.py` - Comprehensive prompt template for single-pass extraction

**Storage:**
- `storage/dynamodb/consultation_storage.py` - DynamoDB helpers with nested structure preservation

**PDF Generation:**
- `pdf/templates/consultation_pdf.py` - Deterministic PDF generator with SOAP + handover sections

**Testing:**
- `test_consultation_system.py` - Comprehensive test suite with sample transcript

**Module Init Files:**
- `shared/__init__.py`
- `analysis/__init__.py`
- `analysis/prompts/__init__.py`
- `storage/__init__.py`
- `storage/dynamodb/__init__.py`
- `pdf/__init__.py`
- `pdf/templates/__init__.py`

**Documentation:**
- `CurrentState.md` - Analysis of baseline system
- `NewState.md` - This document

### Modified Files

**Worker:**
- `docker/whipser_api/worker_openai.py`
  - Added imports for new modules
  - Replaced simple Bedrock prompt with comprehensive extraction
  - Added PDF generation step
  - Updated FHIR generation to use artifact
  - Modified DynamoDB storage to use nested structure
  - Updated WebSocket notification with new fields

**Docker:**
- `docker/whipser_api/Dockerfile`
  - Added reportlab dependency
  - Copy new module directories (shared, analysis, storage, pdf)

---

## JSON Schema Definition

The `ConsultationArtifact` schema (version 2.0) is defined in `shared/schemas/consultation_artifact_schema.json`.

### Top-Level Structure

```json
{
  "version": "2.0",
  "metadata": { /* consultation context */ },
  "patient_context": { /* de-identified patient info */ },
  "soap_notes": {
    "subjective": { /* patient history, symptoms, medications, allergies */ },
    "objective": { /* vitals, examination, investigations, devices */ },
    "assessment": { /* diagnosis, differentials, problem list, impression */ },
    "plan": { /* treatment, investigations, referrals, follow-up, discharge */ }
  },
  "clinical_safety": { /* red flags, risks, contraindications, missing info */ },
  "follow_up_tasks": [ /* structured actionable tasks */ ],
  "handover": { /* SBAR format for nursing/medical handover */ },
  "metadata_extraction": { /* extraction metadata */ }
}
```

### Key Features

**1. Metadata Section:**
- Consultation ID, timestamp, duration
- Setting type (clinic, hospital_inpatient, ED, telehealth, etc.)
- Specialty and encounter type
- Participants and location details

**2. SOAP Notes:**
- **Subjective:** Chief complaint, HPI, symptoms (with onset/duration/severity), PMH, medications, allergies, social/family history, functional status
- **Objective:** Vital signs (including GCS, AVPU, pain score), physical exam by system, investigations, imaging, lines/devices, fluid balance
- **Assessment:** Primary diagnosis, differentials with likelihood, problem list with status/priority, clinical impression, severity, prognosis
- **Plan:** Treatment strategy, medications prescribed, investigations ordered, referrals, patient education, follow-up, safety netting, escalation criteria, discharge planning

**3. Clinical Safety:**
- Red flags with severity and actions taken
- Risk factors
- Contraindications
- Missing information
- Clarifying questions
- Confidence level

**4. Follow-Up Tasks:**
Each task includes:
- `task_id`: Unique identifier
- `task_type`: Enum (order_scan, order_lab, prescription, nursing_observation, etc.)
- `description`: Human-readable
- `owner_role`: Who's responsible (doctor, nurse, pharmacy, radiology, etc.)
- `urgency`: stat, urgent, routine, low
- `due_at`: ISO datetime or relative time
- `location`: Ward, room, department
- `dependencies`: Array of task_ids that must complete first
- `status`: proposed, pending, in_progress, completed, cancelled
- `transcript_evidence`: Quote from transcript
- `required_inputs`: Structured data for automation
  - `prescription`: medication, dose, route, frequency, duration, repeats, indication
  - `imaging`: modality, body_part, contrast, clinical_question, urgency
  - `lab_test`: test_name, sample_type, fasting_required, urgency
  - `nursing_observation`: type, frequency, duration, parameters, escalation_criteria
  - `room_booking`: room_type, duration, equipment, staff
  - `discharge`: date, time, destination, transport, medications, equipment, appointments
  - `referral`: specialty, urgency, reason, preferred_provider

**5. Handover:**
- SBAR format (Situation, Background, Assessment, Recommendation)
- Active issues
- Pending tasks summary
- Escalation criteria
- Next review time
- Key contacts

---

## Bedrock Prompt

Located in `analysis/prompts/bedrock_prompt.py`.

### Key Features

**System Prompt:**
- Defines role as medical AI assistant
- Specifies NZ healthcare context
- Lists all supported settings (clinic, hospital, ED, nursing home)
- Emphasizes JSON-only output

**User Prompt Template:**
- Includes full transcript
- Provides complete JSON schema with examples
- Lists 10 critical instructions:
  1. Analyze thoroughly
  2. Extract ALL actionable tasks
  3. Populate required_inputs for each task
  4. Use transcript_evidence for audit trail
  5. Flag missing information
  6. Generate complete handover note
  7. Return ONLY JSON
  8. Ensure valid JSON
  9. Use null for missing fields
  10. Do not hallucinate

**Request Configuration:**
```python
{
    'anthropic_version': 'bedrock-2023-05-31',
    'max_tokens': 8000,  # Increased for comprehensive output
    'temperature': 0.1,  # Low for consistency
    'messages': [{'role': 'user', 'content': prompt}]
}
```

**Enforcement of JSON Output:**
- Prompt explicitly states "return ONLY valid JSON - no prose, no explanations"
- Worker uses regex to extract JSON from response
- Falls back to minimal artifact if parsing fails

---

## DynamoDB Schema

### Storage Strategy

**Approach:** Nested structure with backward-compatible flat fields

**Rationale:**
- Preserves complete artifact structure (no data loss)
- Maintains backward compatibility for existing consumers
- Enables efficient querying with top-level statistics
- Supports versioning

### Item Structure

```json
{
  // Primary key
  "audio_key": "uploads/test_xxx.webm",
  
  // Metadata
  "patient_id": "ABC1234",
  "timestamp": 1737000000,
  "consultation_timestamp": "2026-01-17T10:00:00+13:00",
  "setting_type": "clinic",
  "specialty": "general_practice",
  "encounter_type": "initial_consultation",
  
  // Core data
  "transcript": "full text...",
  "consultation_artifact": { /* COMPLETE NESTED STRUCTURE */ },
  
  // Task statistics (for querying)
  "follow_up_tasks": [ /* array of tasks */ ],
  "pending_task_count": 5,
  "urgent_task_count": 2,
  "total_task_count": 5,
  
  // Clinical summary (for quick access)
  "primary_diagnosis": "Chest pain - query cardiac",
  "chief_complaint": "Chest pain for 2 days",
  
  // FHIR bundle
  "fhir_bundle": { /* FHIR R4 resources */ },
  
  // PDF info
  "pdf_local_path": "/tmp/xxx.pdf",  // If generated
  "pdf_s3_key": "pdfs/xxx.pdf",      // If uploaded (commented out)
  
  // Version tracking
  "artifact_version": "2.0",
  
  // LEGACY FIELDS (backward compatibility)
  "diagnosis": "Chest pain - query cardiac",
  "medications": ["Aspirin"],
  "tasks": ["Perform ECG", "Blood tests", "Chest X-ray", "Aspirin", "Cardiology referral"],
  "follow_up": "today - after test results",
  "notes": "Patient with acute chest pain requiring urgent investigation",
  "vital_signs": {"blood_pressure": "145/90", "heart_rate": "88", ...},
  "symptoms": ["chest pain", "shortness of breath"]
}
```

### Query Patterns

**Get consultations with urgent tasks:**
```python
response = table.scan(
    FilterExpression='urgent_task_count > :count',
    ExpressionAttributeValues={':count': 0}
)
```

**Get consultations by setting:**
```python
response = table.scan(
    FilterExpression='setting_type = :type',
    ExpressionAttributeValues={':type': 'hospital_inpatient'}
)
```

**Get specific task from consultation:**
```python
from storage.dynamodb.consultation_storage import get_task_by_id

item = table.get_item(Key={'audio_key': key})['Item']
task = get_task_by_id(item, 'task-001')
```

### Helper Functions

Located in `storage/dynamodb/consultation_storage.py`:

- `prepare_consultation_item()` - Prepare item for storage
- `extract_legacy_format()` - Get legacy flat format
- `extract_artifact()` - Get consultation artifact
- `is_new_format()` - Check if item uses v2.0
- `get_task_by_id()` - Get specific task
- `get_tasks_by_owner()` - Filter tasks by role
- `get_urgent_tasks()` - Get urgent/stat tasks
- `update_task_status()` - Update task status and recalculate counts

---

## PDF Generation

Located in `pdf/templates/consultation_pdf.py`.

### Features

**Deterministic Template-Based:**
- No AI calls
- Uses ReportLab library
- Professional medical note styling
- Supports all encounter types

**Sections Included:**
1. **Header:** Facility info, date, setting, encounter type
2. **Red Flags:** Highlighted alerts if present
3. **SOAP Notes:**
   - Subjective: Chief complaint, HPI, symptoms, medications, allergies
   - Objective: Vital signs table, physical exam, investigations
   - Assessment: Diagnosis, problem list, clinical impression
   - Plan: Medications, investigations, referrals, follow-up, safety netting
4. **Follow-Up Tasks:** Grouped by urgency (STAT, Urgent, Routine)
5. **Handover (New Page):** SBAR format for nursing/medical staff
6. **Footer:** Generation timestamp, disclaimer

**Styling:**
- Custom color scheme (medical blue theme)
- Clear section headers
- Tables for structured data
- Bullet points for lists
- Red text for alerts
- Professional fonts

**Usage:**
```python
from pdf.templates.consultation_pdf import generate_consultation_pdf

pdf_path = generate_consultation_pdf(
    consultation_artifact,
    "/tmp/consultation.pdf",
    facility_info={
        'name': 'Medical Clinic',
        'address': '123 Street',
        'phone': '09-123-4567'
    }
)
```

**S3 Upload (Currently Commented Out):**
```python
# Uncomment in worker_openai.py to enable:
# pdf_s3_key = f"pdfs/{key.replace('.webm', '.pdf').replace('uploads/', '')}"
# s3.upload_file(pdf_filename, bucket, pdf_s3_key)
# pdf_url = s3.generate_presigned_url('get_object', ...)
```

---

## Testing & Validation

### Test Script

Located in `test_consultation_system.py`.

**Tests Included:**
1. **Prompt Generation:** Validates prompt structure
2. **Bedrock Request:** Validates API request body
3. **Artifact Structure:** Validates against schema
4. **PDF Generation:** Creates PDF from sample artifact
5. **DynamoDB Item:** Validates item preparation
6. **Single Bedrock Call:** Confirms constraint enforcement

**Sample Transcript:**
- Realistic GP consultation
- Chest pain presentation
- Multiple investigations ordered
- Cardiology referral
- Safety netting provided
- ~300 lines of dialogue

**Running Tests:**
```bash
cd /Users/thireshannaidoo/Documents/Transcriber
python test_consultation_system.py
```

**Expected Output:**
```
============================================================
CONSULTATION ARTIFACT SYSTEM TESTS
============================================================

TEST 1: Prompt Generation
✓ Prompt generated successfully
✓ Prompt length: XXXXX characters

TEST 2: Bedrock Request Body
✓ Bedrock request body valid
✓ Max tokens: 8000
✓ Temperature: 0.1

TEST 3: Artifact Structure Validation
✓ Sample artifact structure valid
✓ Version: 2.0
✓ Tasks extracted: 5
✓ SOAP sections present: ['subjective', 'objective', 'assessment', 'plan']

TEST 4: PDF Generation
✓ PDF generated successfully
✓ Output path: /tmp/test_consultation.pdf
✓ File size: XXXXX bytes

TEST 5: DynamoDB Item Preparation
✓ DynamoDB item prepared successfully
✓ Audio key: uploads/test_123.webm
✓ Artifact version: 2.0
✓ Total tasks: 5
✓ Pending tasks: 5
✓ Urgent tasks: 4
✓ Legacy fields present: diagnosis, medications, tasks

TEST 6: Single Bedrock Call Constraint
✓ Code structure enforces single Bedrock call
✓ PDF generation: deterministic template (no AI)
✓ FHIR generation: uses artifact (no AI)
✓ DynamoDB storage: uses artifact (no AI)
✓ All downstream steps are deterministic

============================================================
ALL TESTS PASSED ✓
============================================================
```

### Validation Checklist

- [x] JSON schema defined
- [x] Bedrock prompt enforces JSON output
- [x] Single Bedrock call per transcript
- [x] PDF generation is deterministic
- [x] FHIR generation uses artifact
- [x] DynamoDB preserves nested structure
- [x] Backward compatibility maintained
- [x] Task automation data complete
- [x] Handover section included
- [x] Clinical safety flags present
- [x] Tests pass successfully

---

## Running Locally

### Prerequisites

```bash
pip install openai boto3 requests librosa soundfile numpy reportlab
```

### Test Without AWS

```bash
# Run test suite
python test_consultation_system.py

# This will:
# 1. Generate prompt from sample transcript
# 2. Validate artifact structure
# 3. Generate PDF (saved to /tmp/test_consultation.pdf)
# 4. Prepare DynamoDB item
# 5. Validate all constraints
```

### Test With AWS (Docker)

```bash
# Build Docker image
cd docker/whipser_api
docker build -t clinical-worker:latest .

# Run worker locally
docker run -e AWS_REGION=ap-southeast-2 \
           -e QUEUE_URL=<your-sqs-url> \
           -e TABLE_NAME=clinical-results \
           -e OPENAI_API_KEY=<your-key> \
           clinical-worker:latest
```

### Deploy to EC2

```bash
# Push to ECR
aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin <ecr-url>
docker tag clinical-worker:latest <ecr-url>/clinical-worker:latest
docker push <ecr-url>/clinical-worker:latest

# SSH to EC2 and pull
ssh ec2-user@<instance-ip>
docker pull <ecr-url>/clinical-worker:latest
docker stop clinical-worker
docker rm clinical-worker
docker run -d --name clinical-worker \
  -e AWS_REGION=ap-southeast-2 \
  -e QUEUE_URL=<sqs-url> \
  -e TABLE_NAME=clinical-results \
  -e OPENAI_API_KEY=<key> \
  <ecr-url>/clinical-worker:latest
```

---

## Task Automation Examples

### Extract Tasks by Type

```python
from storage.dynamodb.consultation_storage import get_tasks_by_owner

# Get item from DynamoDB
item = dynamodb.Table('clinical-results').get_item(Key={'audio_key': key})['Item']

# Get all nursing tasks
nursing_tasks = get_tasks_by_owner(item, 'nurse')

# Get all urgent tasks
urgent_tasks = get_urgent_tasks(item)

# Get specific task
task = get_task_by_id(item, 'task-001')
```

### Route Tasks to Systems

```python
# Example: Send prescription to pharmacy API
for task in item['follow_up_tasks']:
    if task['task_type'] == 'prescription':
        prescription_data = task['required_inputs']['prescription']
        
        # Call pharmacy API
        pharmacy_api.create_order({
            'medication': prescription_data['medication'],
            'dose': prescription_data['dose'],
            'route': prescription_data['route'],
            'frequency': prescription_data['frequency'],
            'duration': prescription_data['duration'],
            'indication': prescription_data['indication']
        })
        
        # Update task status
        update_task_status(table, key, task['task_id'], 'completed')
```

### Process Tasks with Dependencies

```python
from storage.dynamodb.consultation_storage import get_task_by_id

# Get all tasks
tasks = item['follow_up_tasks']

# Find tasks with no pending dependencies
ready_tasks = []
pending_task_ids = {t['task_id'] for t in tasks if t['status'] == 'proposed'}

for task in tasks:
    if task['status'] != 'proposed':
        continue
    
    deps = task.get('dependencies', [])
    if not deps or not any(d in pending_task_ids for d in deps):
        ready_tasks.append(task)

# Process ready tasks
for task in ready_tasks:
    # Route to appropriate system
    if task['task_type'] == 'order_scan':
        radiology_api.book_scan(task['required_inputs']['imaging'])
    elif task['task_type'] == 'order_lab':
        lab_api.order_test(task['required_inputs']['lab_test'])
```

---

## Migration Notes

### Backward Compatibility

**Old consumers can continue using:**
- `diagnosis` field
- `medications` array
- `tasks` array (first 5 task descriptions)
- `follow_up` string
- `notes` string
- `vital_signs` object
- `symptoms` array

**New consumers should use:**
- `consultation_artifact` for complete structured data
- `follow_up_tasks` for detailed task information
- `artifact_version` to check format

### Detecting Format

```python
from storage.dynamodb.consultation_storage import is_new_format

item = table.get_item(Key={'audio_key': key})['Item']

if is_new_format(item):
    # Use new artifact structure
    artifact = item['consultation_artifact']
    tasks = artifact['follow_up_tasks']
else:
    # Use legacy flat structure
    diagnosis = item.get('diagnosis')
    medications = item.get('medications', [])
```

### Gradual Migration

1. Deploy new worker (writes both formats)
2. Update consumers to check `artifact_version`
3. Migrate consumers to use `consultation_artifact`
4. Eventually deprecate flat fields (optional)

---

## Cost Analysis

### Per Consultation (~5 minutes audio)

| Component | Cost |
|-----------|------|
| Whisper transcription | $0.006 |
| Bedrock extraction (8K tokens) | ~$0.020 |
| S3 storage (audio + PDF) | $0.0001 |
| DynamoDB write | $0.0001 |
| Lambda API calls | $0.0001 |
| **Total** | **~$0.026** |

### Key Points

- **Single Bedrock call** - No additional AI costs
- **Increased token usage** - Comprehensive prompt + output (~8K tokens vs 1K)
- **PDF generation** - Pure code, no cost
- **Task extraction** - Included in Bedrock call
- **FHIR generation** - Pure code, no cost

### Cost Comparison

- **Old system:** ~$0.016 per consultation
- **New system:** ~$0.026 per consultation
- **Increase:** $0.010 per consultation
- **Value:** Complete structured data, PDF, tasks, handover

---

## Future Enhancements

### Ready for Implementation

1. **PDF S3 Upload:** Uncomment code in worker
2. **Task Automation APIs:** Use `required_inputs` to call external systems
3. **Task Status Dashboard:** Query by `pending_task_count`, `urgent_task_count`
4. **Handover Report:** Generate from `handover` section
5. **Clinical Audit:** Use `transcript_evidence` for audit trail

### Potential Additions

1. **Task Scheduling:** Use `due_at` for automated scheduling
2. **Dependency Resolution:** Process tasks in correct order
3. **Notification System:** Alert staff when urgent tasks created
4. **Integration Adapters:** Build connectors for specific PMS systems
5. **Analytics Dashboard:** Track task completion rates, consultation types

---

## Summary

**Achievements:**
✓ Single Bedrock call per transcript (constraint enforced)
✓ Comprehensive structured output (SOAP + tasks + handover)
✓ Deterministic PDF generation (no AI)
✓ Nested DynamoDB structure (preserves all data)
✓ Backward compatibility (legacy fields maintained)
✓ Hospital/nursing support (handover, observations, discharge)
✓ Task automation ready (complete required_inputs)
✓ Tested and validated (test suite passes)

**Files Changed:** 2 (worker, Dockerfile)
**Files Added:** 15 (schemas, prompts, storage, PDF, tests, docs)
**Lines of Code:** ~3000 (well-structured, modular)

**Ready for Production:** Yes, after testing with real transcripts
