# Clinical Recorder

AI-powered clinical transcription and workflow automation system for GP doctors in New Zealand.

## Features

- 🎤 **Audio Recording & Transcription** - Record consultations or upload audio files
- 📝 **AI Clinical Notes** - Automatically converts transcriptions to structured SOAP notes
- 📋 **Task Extraction** - AI suggests conditions, medications, and follow-ups to add
- 👥 **Patient Management** - Search, view, and manage patient records
- 📄 **Clinical Handovers** - Generate AI-assisted handover summaries
- 🏥 **FHIR Integration** - Store all data in standard FHIR format

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   EC2 API       │────▶│   FHIR Server   │
│   (index.html)  │     │   (Flask:5000)  │     │   (HAPI:8080)   │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │                      │
         │ Upload audio         │ AI summaries/notes
         ▼                      ▼
┌─────────────────┐     ┌─────────────────┐
│   S3 Bucket     │     │   AWS Bedrock   │
│   (Audio)       │     │   (Claude AI)   │
└────────┬────────┘     └─────────────────┘
         │ S3 Event
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   SQS Queue     │────▶│   EC2 Worker    │────▶│   DynamoDB      │
│                 │     │ (Whisper+Bedrock)│     │   (Results)     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 │ WebSocket
                                 ▼
                        ┌─────────────────┐
                        │   Frontend      │
                        │   (Real-time)   │
                        └─────────────────┘
```

## Flow

1. **Upload**: Frontend uploads audio to S3 via presigned URL
2. **Queue**: S3 event triggers SQS message
3. **Process**: EC2 Worker polls SQS, transcribes with Whisper, extracts data with Bedrock
4. **Store**: Results saved to DynamoDB
5. **Notify**: WebSocket pushes result to frontend in real-time
6. **Display**: Frontend shows transcription, clinical notes, and suggested tasks

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/get-upload-url` | GET | Get presigned S3 URL for audio upload |
| `/upload-complete` | POST | Trigger transcription processing |
| `/result/{key}` | GET | Get transcription results |
| `/ai-summary` | POST | Generate patient history summary |
| `/handover-summary` | POST | Generate clinical handover |
| `/generate-notes` | POST | Convert transcription to clinical notes |
| `/extract-tasks` | POST | Extract conditions/medications from transcription |

## Patient Data (FHIR Resources)

| Data Type | FHIR Resource | Description |
|-----------|---------------|-------------|
| Demographics | `Patient` | Name, DOB, NHI, gender |
| Diagnoses | `Condition` | Active medical conditions |
| Medications | `MedicationRequest` | Current prescriptions |
| Visits | `Encounter` | Consultations, follow-ups |
| Notes | `DocumentReference` | Clinical notes, handovers |

## Quick Start

### Prerequisites
- Docker
- AWS CLI configured
- FHIR server running on port 8080

### Start EC2 & Containers
```bash
./start-ec2.sh
```

### Manual Container Start
```bash
docker start clinical-api clinical-recorder
```

### Run Frontend Locally
```bash
cd /path/to/clinical-recorder
python -m http.server 8000
# Open http://localhost:8000
```

## Configuration

Update `API_URL` in `index.html` to point to your EC2 instance:
```javascript
const API_URL = 'http://<your-ec2-ip>:5000';
```

## NZ Healthcare Compliance

- ✅ **Privacy Act 2020** - Audit logging, data minimisation
- ✅ **HISO Standards** - NHI integration, NZ terminology
- ✅ **Human-in-the-loop** - All AI suggestions require clinician approval
- ✅ **Data Sovereignty** - AWS ap-southeast-2 (Sydney) region

## Project Structure

```
clinical-recorder/
├── index.html              # Main frontend application
├── docker/
│   ├── fhir_api/
│   │   └── ec2_api.py      # Flask API server
│   └── whisper_api/
│       └── worker_openai.py # Transcription worker
├── backend/
│   └── api_lambda.py       # Lambda functions
├── start-ec2.sh            # EC2 startup script
└── docker-compose.yml      # Container orchestration
```

## Docker Images

- `kaido23/clinical-api:latest` - Flask API server
- `kaido23/clinical-recorder:openai` - Whisper transcription worker
