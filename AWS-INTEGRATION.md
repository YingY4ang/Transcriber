# AWS Integration Guide

## AWS Services Used

### 1. AWS Lambda
**Functions:**
- `clinical-api` (arn:aws:lambda:ap-southeast-2:958175315966:function:clinical-api)
- `clinical-websocket` (arn:aws:lambda:ap-southeast-2:958175315966:function:clinical-websocket)

**Code References:**
- `backend/api_lambda.py` - Main API handler
- Lines 7-8: boto3 S3 and DynamoDB clients

**Configuration:**
- Runtime: Python 3.12
- Memory: 128MB
- Timeout: 3 seconds
- Environment Variables:
  - `BUCKET_NAME=clinical-audio-bucket`
  - `TABLE_NAME=clinical-results`

**IAM Role:** `ApiLambdaRole`

### 2. Amazon S3
**Bucket:** `clinical-audio-bucket`

**Code References:**
- `backend/api_lambda.py:30` - Generate presigned upload URLs
- `docker/worker.py:8` - S3 client for file operations
- `docker/worker.py:25` - Download audio files
- `docker/worker.py:40` - Delete processed files
- `index.html:47-52` - Direct browser upload

**Usage:**
- Store temporary audio files (WebM format)
- Event notifications trigger SQS messages
- Auto-cleanup after processing

**Configuration Required:**
- Bucket name in Lambda environment variables
- S3 event notification to SQS queue
- Public read/write permissions for presigned URLs

### 3. Amazon SQS
**Queue:** `clinical-processing-queue`
**URL:** `https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue`

**Code References:**
- `docker/worker.py:4` - Queue URL configuration
- `docker/worker.py:7` - SQS client initialization
- `docker/worker.py:14` - Message polling loop
- `docker/worker.py:42` - Message deletion after processing

**Usage:**
- Queue audio processing jobs from S3 events
- Reliable message delivery with retry logic
- Dead letter queue for failed messages

**Configuration Required:**
- Queue URL in worker environment variables
- S3 bucket event notification configuration
- IAM permissions for EC2 to read/delete messages

### 4. Amazon DynamoDB
**Tables:**
- `clinical-results` - Store transcription and AI analysis results
- `websocket-connections` - WebSocket connection management

**Code References:**
- `backend/api_lambda.py:8` - DynamoDB resource initialization
- `backend/api_lambda.py:44-49` - Query results by audio key
- `docker/worker.py:10` - DynamoDB resource initialization
- `docker/worker.py:39` - Store processing results

**Schema:**
```
clinical-results:
  - audio_key (String, Primary Key)
  - transcript (String)
  - diagnosis (String)
  - medications (List)
  - follow_up (String)
  - notes (String)
```

**Configuration Required:**
- Table name in environment variables
- On-demand billing mode
- IAM permissions for read/write access

### 5. Amazon Bedrock
**Model:** `anthropic.claude-3-haiku-20240307-v1:0`

**Code References:**
- `docker/worker.py:9` - Bedrock runtime client
- `docker/worker.py:28-37` - AI model invocation for clinical data extraction

**Usage:**
- Extract structured clinical data from transcripts
- JSON format output with diagnosis, medications, follow-up, notes

**Configuration Required:**
- Model access permissions in IAM role
- Region: ap-southeast-2

### 6. Amazon API Gateway
**APIs:**
- `clinical-api` (n465kxij69) - HTTP API
  - Endpoint: `https://n465kxij69.execute-api.ap-southeast-2.amazonaws.com`
- `clinical-websocket` (cmxbu5k037, ryikk90doh) - WebSocket APIs
  - Endpoints: `wss://cmxbu5k037.execute-api.ap-southeast-2.amazonaws.com`

**Code References:**
- `index.html:23` - API endpoint configuration
- `backend/api_lambda.py:16-20` - CORS headers

**Configuration Required:**
- Lambda function integration
- CORS configuration for web browser access
- Route configuration for REST endpoints

### 7. Amazon EC2
**Instance:** `i-0069540f657963c71` (currently stopped)
- Type: c7i-flex.large
- AMI: ami-0b8d527345fdace59
- Public IP: 52.63.25.129
- Key Pair: personal_pair
- Security Group: sg-084cb56fa4c5f7e1c

**Code References:**
- `docker/worker.py` - Entire worker application
- `.github/workflows/deploy.yml:23-33` - EC2 deployment via SSH

**Usage:**
- Run Docker container with Whisper STT processing
- Poll SQS for audio processing jobs
- Heavy compute workload for AI transcription

**IAM Instance Profile:** `EC2TranscribeRole`

## Environment Variables Summary

### Lambda Functions
```bash
BUCKET_NAME=clinical-audio-bucket
TABLE_NAME=clinical-results
```

### EC2 Worker Container
```bash
AWS_REGION=ap-southeast-2
QUEUE_URL=https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue
TABLE_NAME=clinical-results
AWS_ACCESS_KEY_ID=<from-secrets>
AWS_SECRET_ACCESS_KEY=<from-secrets>
```

## IAM Permissions Required

### ApiLambdaRole (Lambda Functions)
- S3: GetObject, PutObject, DeleteObject on clinical-audio-bucket
- DynamoDB: GetItem, PutItem, Query on clinical-results table
- Logs: CreateLogGroup, CreateLogStream, PutLogEvents

### EC2TranscribeRole (EC2 Instance)
- S3: GetObject, DeleteObject on clinical-audio-bucket
- SQS: ReceiveMessage, DeleteMessage on clinical-processing-queue
- DynamoDB: PutItem on clinical-results table
- Bedrock: InvokeModel on Claude Haiku model
- Logs: CreateLogGroup, CreateLogStream, PutLogEvents

## Regional Configuration
- **Primary Region:** ap-southeast-2 (Sydney)
- All resources deployed in single region for latency optimization
- Bedrock Claude Haiku available in ap-southeast-2

## Cost Optimization
- Lambda: Pay per request (minimal cost for API calls)
- S3: Lifecycle policy for automatic deletion after processing
- DynamoDB: On-demand billing for variable workloads
- EC2: Stopped when not processing (manual start/stop)
- SQS: Pay per message (minimal cost)
- Bedrock: Pay per token (Claude Haiku is cost-effective model)

## Security Best Practices
- IAM roles with least privilege access
- No hardcoded credentials in code
- Presigned URLs for time-limited S3 access
- VPC security groups for EC2 network isolation
- Encryption at rest for DynamoDB and S3
- HTTPS/WSS for all API communications
