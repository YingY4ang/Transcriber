# Clinical Recorder

AI-powered clinical transcription and workflow automation system for GP doctors in New Zealand.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   API Gateway    │    │   Lambda API    │
│                 │───▶│                  │───▶│                 │
│ - Record audio  │    │ - CORS enabled   │    │ - Generate      │
│ - Upload to S3  │    │ - /get-upload-url│    │   presigned URL │
│ - Poll results  │    │ - /result/{key}  │    │ - Return results│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                               │
         │                                               │
         ▼                                               ▼
┌─────────────────┐                            ┌─────────────────┐
│   S3 Bucket     │                            │   DynamoDB      │
│                 │                            │                 │
│ - Store audio   │                            │ - Store results │
│ - Event notify  │                            │ - Transcript    │
│ - Auto delete   │                            │ - AI analysis   │
└─────────────────┘                            └─────────────────┘
         │                                               ▲
         │ S3 Event                                      │
         ▼                                               │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SQS Queue     │    │   EC2 Instance   │    │   Bedrock AI    │
│                 │───▶│                  │───▶│                 │
│ - Queue jobs    │    │ - Docker worker  │    │ - Claude Haiku  │
│ - Message retry │    │ - Whisper STT    │    │ - Extract data  │
│ - Dead letter   │    │ - Process audio  │    │ - JSON format   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Flow

1. Browser records → API gets upload URL → uploads to S3
2. S3 triggers event → SQS queues job
3. EC2 worker polls SQS → downloads audio → transcribes with Whisper
4. Worker sends transcript to Bedrock → gets structured data
5. Worker saves to DynamoDB → deletes S3 file
6. Browser polls API → gets results from DynamoDB

## Components

- **Frontend**: HTML/JS audio recorder with real-time transcription
- **Backend**: AWS Lambda API for file upload and result retrieval
- **Processing**: Docker container with Whisper STT and Bedrock AI
- **Storage**: S3 for audio files, DynamoDB for structured results
- **Queue**: SQS for reliable job processing

## Compliance

Built for New Zealand healthcare compliance:
- Privacy Act 2020
- HISO standards
- Human-in-the-loop approval for clinical decisions
