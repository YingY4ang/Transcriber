# Clinical Recorder Architecture

## Overview
AI-powered clinical transcription system for GP doctors in New Zealand, built on AWS serverless and containerized architecture.

## System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   API Gateway    │    │   Lambda API    │
│                 │───▶│                  │───▶│                 │
│ - Record audio  │    │ - CORS enabled   │    │ - Generate      │
│ - Upload to S3  │    │ - /get-upload-url│    │   presigned URL │
│ - Poll results  │    │ - /result/{key}  │    │ - Return results│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                               │
         │ Direct S3 Upload                              │
         ▼                                               ▼
┌─────────────────┐                            ┌─────────────────┐
│   S3 Bucket     │                            │   DynamoDB      │
│                 │                            │                 │
│ - Store audio   │                            │ - Store results │
│ - Event notify  │                            │ - Transcript    │
│ - Auto delete   │                            │ - AI analysis   │
└─────────────────┘                            └─────────────────┘
         │                                               ▲
         │ S3 Event Notification                         │
         ▼                                               │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SQS Queue     │    │   EC2 Instance   │    │   Bedrock AI    │
│                 │───▶│                  │───▶│                 │
│ - Queue jobs    │    │ - Docker worker  │    │ - Claude Haiku  │
│ - Message retry │    │ - Whisper STT    │    │ - Extract data  │
│ - Dead letter   │    │ - Process audio  │    │ - JSON format   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Component Details

### 1. Frontend (index.html)
- **Purpose**: Web-based audio recorder interface
- **Runtime**: Browser JavaScript
- **Key Features**:
  - MediaRecorder API for audio capture
  - Direct S3 upload via presigned URLs
  - Polling for processing results
  - Real-time status updates
- **Dependencies**: None (vanilla HTML/JS)

### 2. Backend API (backend/api_lambda.py)
- **Purpose**: REST API for file upload coordination and result retrieval
- **Runtime**: AWS Lambda (Python 3.12)
- **Entrypoints**:
  - `GET /get-upload-url` - Generate S3 presigned upload URL
  - `GET /result/{key}` - Retrieve processing results
- **Dependencies**: boto3
- **Environment Variables**:
  - `BUCKET_NAME`: S3 bucket for audio files
  - `TABLE_NAME`: DynamoDB table for results

### 3. Processing Worker (docker/worker.py)
- **Purpose**: Audio transcription and AI analysis
- **Runtime**: Docker container on EC2
- **Key Features**:
  - OpenAI Whisper for speech-to-text
  - AWS Bedrock Claude Haiku for clinical data extraction
  - SQS message processing loop
  - Automatic cleanup of processed files
- **Dependencies**: whisper, boto3, ffmpeg
- **Environment Variables**:
  - `QUEUE_URL`: SQS queue URL
  - `TABLE_NAME`: DynamoDB results table
  - `AWS_REGION`: AWS region

### 4. Container Infrastructure (docker/Dockerfile)
- **Base Image**: python:3.12-slim
- **System Dependencies**: ffmpeg for audio processing
- **Python Dependencies**: openai-whisper, boto3
- **Entrypoint**: Continuous SQS polling loop

## Data Flow

1. **Audio Capture**: Browser records audio using MediaRecorder API
2. **Upload Coordination**: Frontend requests presigned URL from Lambda API
3. **Direct Upload**: Audio file uploaded directly to S3 bucket
4. **Event Trigger**: S3 event notification sends message to SQS queue
5. **Processing**: EC2 worker polls SQS, downloads audio, transcribes with Whisper
6. **AI Analysis**: Transcript sent to Bedrock Claude for clinical data extraction
7. **Storage**: Results saved to DynamoDB, S3 file deleted
8. **Retrieval**: Frontend polls Lambda API for results from DynamoDB

## Deployment Architecture

### Current Deployment
- **Frontend**: Static HTML served from local file or web server
- **API**: AWS Lambda functions behind API Gateway HTTP API
- **Processing**: Docker container on EC2 instance (currently stopped)
- **CI/CD**: GitHub Actions for Docker build/push and EC2 deployment

### Resource Naming Convention
- S3 Bucket: `clinical-audio-bucket`
- SQS Queue: `clinical-processing-queue`
- DynamoDB Tables: `clinical-results`, `websocket-connections`
- Lambda Functions: `clinical-api`, `clinical-websocket`
- EC2 Instance: Tagged as "Transcribe"
- IAM Roles: `ApiLambdaRole`, `EC2TranscribeRole`

## Scalability Considerations

- **Lambda**: Auto-scales with API requests
- **SQS**: Handles message queuing and retry logic
- **EC2**: Single instance (manual scaling required)
- **DynamoDB**: On-demand billing, auto-scales
- **S3**: Unlimited storage, auto-cleanup after processing

## Security Features

- **IAM Roles**: Least privilege access for Lambda and EC2
- **Presigned URLs**: Time-limited S3 upload access
- **CORS**: Configured for cross-origin requests
- **VPC**: EC2 instance in default VPC with security groups
- **Encryption**: Default AWS service encryption
