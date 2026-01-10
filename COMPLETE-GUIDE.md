# Complete Guide to Clinical Recorder: From Zero to Expert

## Table of Contents
1. [Introduction & Project Overview](#introduction--project-overview)
2. [Understanding the Technologies](#understanding-the-technologies)
3. [Repository Structure Deep Dive](#repository-structure-deep-dive)
4. [AWS Services Explained](#aws-services-explained)
5. [Code Analysis & AWS Integration](#code-analysis--aws-integration)
6. [Local Development vs Production](#local-development-vs-production)
7. [Real AWS Resources Mapping](#real-aws-resources-mapping)
8. [Complete Data Flow](#complete-data-flow)
9. [Deployment & Operations](#deployment--operations)
10. [Troubleshooting & Monitoring](#troubleshooting--monitoring)

---

## Introduction & Project Overview

### What is the Clinical Recorder?
The Clinical Recorder is an AI-powered system designed for GP (General Practitioner) doctors in New Zealand to automatically transcribe and analyze clinical consultations. Instead of manually typing notes during patient visits, doctors can simply record their conversation, and the system will:

1. **Transcribe** the audio into text using AI
2. **Extract** structured clinical information (diagnosis, medications, follow-up plans)
3. **Store** the results for easy retrieval
4. **Comply** with New Zealand healthcare regulations

### Why This Architecture?
This system uses a **serverless and containerized architecture** on Amazon Web Services (AWS). This means:
- **Cost-effective**: You only pay for what you use
- **Scalable**: Automatically handles more users without manual intervention
- **Reliable**: Built on enterprise-grade cloud infrastructure
- **Secure**: Follows healthcare data protection standards

---

## Understanding the Technologies

Before diving into the code, let's understand each technology used in this project:

### What is AWS (Amazon Web Services)?
AWS is Amazon's cloud computing platform that provides on-demand computing services. Instead of buying and maintaining your own servers, you rent computing power, storage, and services from Amazon's data centers worldwide.

**Key Benefits:**
- **No upfront costs**: Pay only for what you use
- **Global reach**: Data centers worldwide for low latency
- **Reliability**: 99.99% uptime guarantees
- **Security**: Enterprise-grade security and compliance

### What is Docker?
Docker is a platform that packages applications and their dependencies into lightweight, portable containers.

**Think of it like this:**
- A **container** is like a shipping container for software
- It includes everything needed to run an application: code, runtime, libraries, settings
- Containers run the same way on any system (your laptop, a server, the cloud)

**Why use Docker?**
- **Consistency**: "It works on my machine" becomes "It works everywhere"
- **Isolation**: Applications don't interfere with each other
- **Portability**: Easy to move between development, testing, and production

### What is AWS Lambda?
AWS Lambda is a **serverless computing service**. You upload your code, and AWS runs it automatically when triggered.

**Key Concepts:**
- **Serverless**: You don't manage servers; AWS handles everything
- **Event-driven**: Code runs in response to events (HTTP requests, file uploads, etc.)
- **Pay-per-use**: Only charged when your code is actually running
- **Auto-scaling**: Handles 1 request or 1 million requests automatically

### What is Whisper?
Whisper is an AI model created by OpenAI that converts speech to text (Speech-to-Text or STT).

**Key Features:**
- **Multilingual**: Supports 99 languages
- **Robust**: Works with accents, background noise, technical terms
- **Open source**: Free to use and modify
- **High accuracy**: State-of-the-art transcription quality

### What is Amazon Bedrock?
Amazon Bedrock is AWS's service for accessing AI models from companies like Anthropic, AI21, and others.

**In this project:**
- We use **Claude Haiku** (by Anthropic) to analyze transcripts
- Claude reads the transcript and extracts structured medical information
- It outputs JSON with diagnosis, medications, follow-up plans, etc.

### What is API Gateway?
API Gateway is AWS's service for creating and managing APIs (Application Programming Interfaces).

**What's an API?**
- An API is like a waiter in a restaurant
- Your app (customer) makes a request
- The API (waiter) takes it to the kitchen (backend services)
- Returns the response (food) to your app

### What is Amazon S3?
S3 (Simple Storage Service) is AWS's file storage service.

**Key Concepts:**
- **Buckets**: Like folders that hold your files
- **Objects**: The actual files you store
- **Unlimited storage**: Store as much as you need
- **Durability**: 99.999999999% (11 9's) durability guarantee

### What is Amazon SQS?
SQS (Simple Queue Service) is a message queuing service.

**Think of it like:**
- A post office mailbox system
- Applications can send messages to a queue
- Other applications can read and process these messages
- Ensures messages aren't lost and are processed in order

### What is Amazon DynamoDB?
DynamoDB is AWS's NoSQL database service.

**Key Features:**
- **NoSQL**: Stores data as key-value pairs, not traditional tables
- **Serverless**: No servers to manage
- **Fast**: Single-digit millisecond response times
- **Scalable**: Handles any amount of data and traffic

---

## Repository Structure Deep Dive

Let's examine every file in your project and understand its purpose:

```
/Users/thireshannaidoo/Documents/Transcriber/
├── README.md                    # Project overview and architecture diagram
├── index.html                   # Frontend web application
├── backend/
│   └── api_lambda.py           # AWS Lambda function for API endpoints
├── docker/
│   ├── Dockerfile              # Instructions to build Docker container
│   └── worker.py               # Audio processing worker application
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD pipeline
└── AWSCLIV2.pkg               # AWS CLI installer (can be deleted)
```

### File-by-File Analysis

#### 1. `README.md`
- **Purpose**: Documentation with architecture overview
- **Contains**: ASCII diagram showing system flow
- **Audience**: Developers and stakeholders

#### 2. `index.html` - The Frontend Application
This is a **Single Page Application (SPA)** that runs in web browsers.

**What it does:**
- Records audio using the browser's microphone
- Uploads audio files directly to AWS S3
- Polls for processing results
- Displays transcription and analysis results

**Key Technologies Used:**
- **HTML5 MediaRecorder API**: For recording audio
- **JavaScript Fetch API**: For making HTTP requests
- **WebM format**: Modern audio format supported by browsers

#### 3. `backend/api_lambda.py` - The API Server
This is an **AWS Lambda function** that acts as your API server.

**What it does:**
- Generates secure, time-limited URLs for file uploads
- Retrieves processing results from the database
- Handles CORS (Cross-Origin Resource Sharing) for web browsers

**Key AWS Services Used:**
- **boto3**: AWS SDK for Python
- **S3**: For generating presigned upload URLs
- **DynamoDB**: For storing and retrieving results

#### 4. `docker/Dockerfile` - Container Blueprint
This file tells Docker how to build a container for the audio processing worker.

**What it does:**
- Starts with Python 3.12 base image
- Installs ffmpeg (audio processing library)
- Installs Python dependencies (Whisper, boto3)
- Sets up the worker application

#### 5. `docker/worker.py` - The Processing Engine
This is the **heavy lifting** component that processes audio files.

**What it does:**
- Continuously polls SQS queue for new jobs
- Downloads audio files from S3
- Transcribes audio using Whisper AI
- Analyzes transcripts using Amazon Bedrock (Claude)
- Stores results in DynamoDB
- Cleans up processed files

#### 6. `.github/workflows/deploy.yml` - CI/CD Pipeline
This is a **GitHub Actions workflow** that automatically deploys your application.

**What it does:**
- Triggers on code pushes to main branch
- Builds Docker container
- Pushes container to Docker Hub
- Deploys to EC2 instance via SSH

---
## AWS Services Explained

Your Clinical Recorder uses 7 main AWS services. Let's understand each one and how they work together:

### 1. AWS Lambda - Serverless Computing

**What is it?**
Lambda is like having a computer that only turns on when you need it, runs your code, then turns off immediately.

**In your project:**
- **Function Name**: `clinical-api`
- **Runtime**: Python 3.12
- **Memory**: 128MB (very small, just for API calls)
- **Timeout**: 3 seconds (quick responses)

**Code Location**: `backend/api_lambda.py`

**What it handles:**
```
GET /get-upload-url  → Generates secure S3 upload link
GET /result/{key}    → Returns processing results
OPTIONS /*           → Handles browser CORS requests
```

**Why Lambda?**
- **Cost**: Only pay when someone uses your API (could be $0.01/month for light usage)
- **Scaling**: Handles 1 user or 1000 users automatically
- **Maintenance**: No servers to update or patch

### 2. Amazon API Gateway - The Front Door

**What is it?**
API Gateway is like a receptionist for your Lambda functions. It receives requests from the internet and routes them to the right Lambda function.

**Your API Details:**
- **API ID**: `n465kxij69`
- **Type**: HTTP API (simpler and cheaper than REST API)
- **URL**: `https://n465kxij69.execute-api.ap-southeast-2.amazonaws.com`
- **Region**: ap-southeast-2 (Sydney, Australia)

**Why API Gateway?**
- **HTTPS**: Automatically provides secure connections
- **CORS**: Handles cross-origin requests from web browsers
- **Throttling**: Protects your backend from too many requests
- **Monitoring**: Tracks API usage and errors

### 3. Amazon S3 - File Storage

**What is it?**
S3 is like Google Drive or Dropbox, but for applications. It stores files in "buckets."

**Your Bucket:**
- **Name**: `clinical-audio-bucket`
- **Region**: ap-southeast-2
- **Purpose**: Temporary storage for audio files

**How it works:**
1. Frontend requests upload URL from Lambda
2. Lambda generates a "presigned URL" (temporary, secure link)
3. Browser uploads audio directly to S3 (bypasses your servers)
4. S3 notifies SQS queue when file arrives
5. Worker processes file and deletes it

**Why S3?**
- **Durability**: 99.999999999% (your files won't get lost)
- **Speed**: Fast uploads/downloads worldwide
- **Integration**: Works seamlessly with other AWS services
- **Cost**: Very cheap storage (~$0.023 per GB per month)

### 4. Amazon SQS - Message Queue

**What is it?**
SQS is like a to-do list that multiple applications can share. When a file arrives in S3, it adds a "process this file" message to the queue.

**Your Queue:**
- **Name**: `clinical-processing-queue`
- **URL**: `https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue`
- **Type**: Standard queue (at-least-once delivery)

**Message Flow:**
```
S3 file upload → SQS message → Worker picks up message → Processes file → Deletes message
```

**Why SQS?**
- **Reliability**: Messages won't get lost if worker crashes
- **Decoupling**: S3 and worker don't need to communicate directly
- **Retry Logic**: Failed messages can be retried automatically
- **Scaling**: Multiple workers can process messages in parallel

### 5. Amazon DynamoDB - Database

**What is it?**
DynamoDB is a NoSQL database that stores data as key-value pairs instead of traditional rows and columns.

**Your Tables:**
1. **clinical-results**: Stores transcription and analysis results
2. **websocket-connections**: Manages real-time connections (if used)

**clinical-results Schema:**
```json
{
  "audio_key": "uploads/12345.webm",     // Primary key
  "transcript": "Patient complains of...", // Full transcription
  "diagnosis": "Upper respiratory infection", // AI extracted
  "medications": ["Amoxicillin 500mg"],  // AI extracted
  "follow_up": "Return in 1 week",       // AI extracted
  "notes": "Additional observations"      // AI extracted
}
```

**Why DynamoDB?**
- **Speed**: Single-digit millisecond response times
- **Serverless**: No database servers to manage
- **Scaling**: Handles any amount of data automatically
- **Cost**: Pay only for what you use

### 6. Amazon Bedrock - AI Services

**What is it?**
Bedrock provides access to advanced AI models from companies like Anthropic, without you needing to train or host the models yourself.

**Your Configuration:**
- **Model**: `anthropic.claude-3-haiku-20240307-v1:0`
- **Purpose**: Extract structured clinical data from transcripts
- **Region**: ap-southeast-2

**How it works:**
1. Worker sends transcript to Claude with specific prompt
2. Claude analyzes text and extracts medical information
3. Returns structured JSON with diagnosis, medications, etc.

**Why Claude Haiku?**
- **Fast**: Optimized for quick responses
- **Cost-effective**: Cheaper than larger models
- **Medical knowledge**: Trained on medical literature
- **JSON output**: Can format responses as structured data

### 7. Amazon EC2 - Virtual Servers

**What is it?**
EC2 provides virtual computers in the cloud. Unlike Lambda, these run continuously and you have full control over the operating system.

**Your Instance:**
- **Instance ID**: `i-0069540f657963c71`
- **Type**: `c7i-flex.large` (2 vCPUs, 4GB RAM)
- **OS**: Amazon Linux 2
- **Public IP**: `52.63.25.129`
- **Status**: Currently stopped (to save costs)

**Why EC2 for this component?**
- **Heavy processing**: Whisper AI needs significant CPU/memory
- **Long-running**: Continuously polls SQS queue
- **Custom software**: Needs specific AI libraries and models
- **Cost control**: Can stop when not processing files

---

## Code Analysis & AWS Integration

Now let's examine the code and see exactly how it integrates with AWS services:

### Frontend Code Analysis (`index.html`)

#### Key AWS Integration Points:

**Line 23: API Endpoint Configuration**
```javascript
const API_URL = 'https://n465kxij69.execute-api.ap-southeast-2.amazonaws.com';
```
This hardcoded URL points to your API Gateway endpoint.

**Lines 40-44: Getting Upload URL**
```javascript
const urlRes = await fetch(`${API_URL}/get-upload-url`);
const { upload_url, key } = await urlRes.json();
```
Calls your Lambda function to get a presigned S3 URL.

**Lines 47-52: Direct S3 Upload**
```javascript
await fetch(upload_url, {
  method: 'PUT',
  body: blob,
  headers: { 'Content-Type': 'audio/webm' }
});
```
Uploads audio directly to S3, bypassing your servers entirely.

**Lines 55-65: Polling for Results**
```javascript
async function pollForResult(key, maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise(r => setTimeout(r, 2000));
    const res = await fetch(`${API_URL}/result/${encodeURIComponent(key)}`);
    if (res.ok) return await res.json();
  }
}
```
Repeatedly checks Lambda API for processing results.

#### How the Frontend Works:
1. **Audio Recording**: Uses `MediaRecorder` API to capture microphone input
2. **File Format**: Records in WebM format (modern, compressed)
3. **Upload Strategy**: Direct-to-S3 upload (faster, cheaper than going through servers)
4. **User Experience**: Real-time status updates and result polling

### Backend API Code Analysis (`backend/api_lambda.py`)

#### AWS SDK Initialization:
```python
import boto3

REGION = 'ap-southeast-2'
s3 = boto3.client('s3', region_name=REGION, 
                  config=boto3.session.Config(s3={'addressing_style': 'virtual'}))
dynamodb = boto3.resource('dynamodb', region_name=REGION)
```

**What this does:**
- `boto3`: AWS SDK for Python (like a toolkit for AWS services)
- `s3.client()`: Creates connection to S3 service
- `dynamodb.resource()`: Creates connection to DynamoDB service
- `region_name`: Ensures all services use Sydney data center

#### Environment Variables:
```python
BUCKET = os.environ['BUCKET_NAME']  # clinical-audio-bucket
TABLE = os.environ['TABLE_NAME']    # clinical-results
```

**Why environment variables?**
- **Security**: No hardcoded values in source code
- **Flexibility**: Different values for dev/test/prod environments
- **AWS Best Practice**: Lambda automatically provides these from configuration

#### CORS Headers:
```python
headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
}
```

**What is CORS?**
- **Problem**: Browsers block requests from one domain to another (security)
- **Solution**: Server tells browser "it's okay to make cross-origin requests"
- **Your case**: HTML file needs to call API Gateway from different domain

#### Presigned URL Generation:
```python
key = f"uploads/{uuid4()}.webm"
url = s3.generate_presigned_url(
    'put_object',
    Params={'Bucket': BUCKET, 'Key': key, 'ContentType': 'audio/webm'},
    ExpiresIn=300  # 5 minutes
)
```

**How presigned URLs work:**
1. Lambda generates a temporary URL with embedded AWS credentials
2. URL is valid for 5 minutes only
3. Browser can upload directly to S3 using this URL
4. No AWS credentials needed in frontend code

#### Database Query:
```python
table = dynamodb.Table(TABLE)
resp = table.get_item(Key={'audio_key': key})

if 'Item' in resp:
    return {'statusCode': 200, 'body': json.dumps(resp['Item'])}
return {'statusCode': 404, 'body': '{"status": "processing"}'}
```

**How DynamoDB queries work:**
- `get_item()`: Retrieves single item by primary key
- `Key={'audio_key': key}`: Uses audio filename as unique identifier
- Returns 404 if not found (still processing) or 200 with results

### Worker Code Analysis (`docker/worker.py`)

This is the most complex component. Let's break it down:

#### AWS Service Connections:
```python
sqs = boto3.client('sqs', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
bedrock = boto3.client('bedrock-runtime', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
```

#### Whisper Model Loading:
```python
print("Loading Whisper...")
model = whisper.load_model("medium")
print("Ready!")
```

**Whisper Model Sizes:**
- **tiny**: Fastest, least accurate (~39 MB)
- **base**: Good balance (~74 MB)
- **small**: Better accuracy (~244 MB)
- **medium**: High accuracy (~769 MB) ← Your choice
- **large**: Best accuracy (~1550 MB)

#### Main Processing Loop:
```python
while True:
    resp = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=1, WaitTimeSeconds=20)
    for msg in resp.get('Messages', []):
        # Process each message
```

**How SQS polling works:**
- `WaitTimeSeconds=20`: Long polling (waits up to 20 seconds for messages)
- `MaxNumberOfMessages=1`: Process one file at a time
- Infinite loop keeps worker running continuously

#### File Processing Steps:

**1. Parse SQS Message:**
```python
body = json.loads(msg['Body'])
bucket = body['Records'][0]['s3']['bucket']['name']
key = body['Records'][0]['s3']['object']['key']
```

**2. Download from S3:**
```python
local = f"/tmp/{os.path.basename(key)}"
s3.download_file(bucket, key, local)
```

**3. Transcribe with Whisper:**
```python
transcript = model.transcribe(local)["text"]
```

**4. AI Analysis with Bedrock:**
```python
prompt = """Return ONLY valid JSON: {"diagnosis":"string","medications":[],"follow_up":"string","notes":"string"}

Transcript: """ + transcript

resp_ai = bedrock.invoke_model(
    modelId='anthropic.claude-3-haiku-20240307-v1:0',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 1024,
        'messages': [{'role': 'user', 'content': prompt}]
    })
)
```

**5. Store Results:**
```python
dynamodb.Table(TABLE).put_item(Item={
    'audio_key': key, 
    'transcript': transcript, 
    **extracted
})
```

**6. Cleanup:**
```python
s3.delete_object(Bucket=bucket, Key=key)  # Delete S3 file
os.remove(local)                          # Delete local file
sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg['ReceiptHandle'])
```

---

## Local Development vs Production

Understanding the difference between running your application locally (on your computer) versus in production (on AWS) is crucial:

### Local Development Environment

#### What runs locally:
1. **Frontend (`index.html`)**
   - Runs in your web browser
   - Can be served by any web server or opened directly
   - Still calls production AWS APIs (no local mock)

2. **Worker (`docker/worker.py`)**
   - Runs in Docker container on your machine
   - Still connects to real AWS services (S3, SQS, DynamoDB, Bedrock)
   - Uses your AWS credentials from `~/.aws/credentials`

#### What you CANNOT run locally:
1. **Lambda functions** - These only exist in AWS
2. **API Gateway** - AWS-managed service
3. **SQS, S3, DynamoDB** - These are cloud services

#### Local Development Setup:

**Step 1: Install Prerequisites**
```bash
# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# Install AWS CLI
# Download from: https://aws.amazon.com/cli/

# Configure AWS credentials
aws configure
# Enter your Access Key ID, Secret Access Key, Region (ap-southeast-2)
```

**Step 2: Run Frontend Locally**
```bash
# Option 1: Simple HTTP server
cd /Users/thireshannaidoo/Documents/Transcriber
python3 -m http.server 8000
# Open http://localhost:8000/index.html

# Option 2: Direct file access
open index.html  # Opens in default browser
```

**Step 3: Run Worker Locally**
```bash
cd docker

# Build Docker image
docker build -t clinical-worker .

# Run with your AWS credentials
docker run -e AWS_REGION=ap-southeast-2 \
  -e QUEUE_URL=https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue \
  -e TABLE_NAME=clinical-results \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  clinical-worker
```

#### Local Development Limitations:

**Pros:**
- Faster development cycle (no deployment needed)
- Can debug with breakpoints and logs
- No AWS costs for compute (only storage/API calls)

**Cons:**
- Still uses real AWS services (not truly "offline")
- Need AWS credentials configured
- Can't test Lambda functions locally
- Whisper model download takes time on first run

### Production Environment

#### Production Architecture:
```
Internet → CloudFront (optional) → API Gateway → Lambda → DynamoDB
                                                     ↓
S3 ← SQS ← S3 Event Notification              Presigned URL
↓
EC2 (Docker Worker) → Bedrock AI → DynamoDB
```

#### Production Components:

**1. Frontend Hosting Options:**
- **Current**: Static HTML file (can be hosted anywhere)
- **Better**: S3 + CloudFront for global CDN
- **Best**: Amplify for automatic deployments

**2. API Layer:**
- **API Gateway**: Handles HTTPS, CORS, throttling
- **Lambda**: Serverless compute, auto-scaling
- **No servers to manage**: AWS handles everything

**3. Processing Layer:**
- **EC2 Instance**: Runs Docker container
- **Auto Scaling**: Could add more instances based on queue depth
- **Spot Instances**: Could use cheaper, interruptible instances

**4. Storage Layer:**
- **S3**: Temporary file storage with lifecycle policies
- **DynamoDB**: Permanent result storage with backups
- **CloudWatch**: Logs and monitoring

#### Production Deployment Process:

**Automated via GitHub Actions:**
```yaml
# .github/workflows/deploy.yml triggers on git push
1. Build Docker image
2. Push to Docker Hub
3. SSH to EC2 instance
4. Pull latest image
5. Restart container
```

**Manual Lambda Deployment:**
```bash
# Package Lambda function
cd backend
zip -r api_lambda.zip api_lambda.py

# Deploy to AWS
aws lambda update-function-code \
  --function-name clinical-api \
  --zip-file fileb://api_lambda.zip \
  --region ap-southeast-2
```

### Key Differences Summary:

| Aspect | Local Development | Production |
|--------|------------------|------------|
| **Frontend** | Browser (localhost) | Browser (internet) |
| **API** | AWS Lambda (real) | AWS Lambda (real) |
| **Worker** | Docker (local) | Docker (EC2) |
| **Storage** | AWS S3 (real) | AWS S3 (real) |
| **Database** | AWS DynamoDB (real) | AWS DynamoDB (real) |
| **AI** | AWS Bedrock (real) | AWS Bedrock (real) |
| **Cost** | Lower (no EC2) | Higher (EC2 running) |
| **Performance** | Slower (home internet) | Faster (AWS network) |
| **Debugging** | Easy (local logs) | Harder (CloudWatch) |

---

## Real AWS Resources Mapping

Let's map every real AWS resource back to your code and understand what each one does:

### Your AWS Account Details:
- **Account ID**: 958175315966
- **Region**: ap-southeast-2 (Sydney)
- **User**: Thireshan (IAM user with admin access)

### 1. Lambda Functions

#### Function: `clinical-api`
```
ARN: arn:aws:lambda:ap-southeast-2:958175315966:function:clinical-api
Runtime: Python 3.12
Handler: api_lambda_clean.handler
Memory: 128MB
Timeout: 3 seconds
```

**Maps to code**: `backend/api_lambda.py`
**Environment variables**:
- `BUCKET_NAME=clinical-audio-bucket`
- `TABLE_NAME=clinical-results`

**IAM Role**: `ApiLambdaRole`
**Permissions**:
- S3: Generate presigned URLs for clinical-audio-bucket
- DynamoDB: Read/write to clinical-results table
- CloudWatch: Write logs

#### Function: `clinical-websocket`
```
ARN: arn:aws:lambda:ap-southeast-2:958175315966:function:clinical-websocket
Runtime: Python 3.12
Handler: websocket_handler.handler
```

**Purpose**: Handles WebSocket connections (not used in current frontend)
**Maps to code**: Not present in repository (deployed separately)

### 2. API Gateway

#### HTTP API: `clinical-api`
```
API ID: n465kxij69
Endpoint: https://n465kxij69.execute-api.ap-southeast-2.amazonaws.com
Protocol: HTTP (not REST)
```

**Maps to code**: `index.html` line 23
**Routes**:
- `GET /get-upload-url` → clinical-api Lambda
- `GET /result/{key}` → clinical-api Lambda
- `OPTIONS /*` → clinical-api Lambda (CORS)

#### WebSocket APIs:
```
API ID: cmxbu5k037
Endpoint: wss://cmxbu5k037.execute-api.ap-southeast-2.amazonaws.com

API ID: ryikk90doh  
Endpoint: wss://ryikk90doh.execute-api.ap-southeast-2.amazonaws.com
```

**Purpose**: Real-time communication (not used in current implementation)

### 3. S3 Bucket

#### Bucket: `clinical-audio-bucket`
```
Region: ap-southeast-2
Created: 2026-01-03
Purpose: Temporary audio file storage
```

**Maps to code**:
- `backend/api_lambda.py`: Generates presigned URLs
- `docker/worker.py`: Downloads and deletes files
- `index.html`: Uploads files directly

**Configuration needed**:
- Event notification to SQS when objects created
- Lifecycle policy to delete old files
- CORS policy for browser uploads

### 4. SQS Queue

#### Queue: `clinical-processing-queue`
```
URL: https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue
Type: Standard queue
Visibility timeout: 30 seconds (default)
```

**Maps to code**: `docker/worker.py` line 4
**Message source**: S3 event notifications
**Message consumer**: EC2 Docker worker

**Message format**:
```json
{
  "Records": [{
    "s3": {
      "bucket": {"name": "clinical-audio-bucket"},
      "object": {"key": "uploads/12345.webm"}
    }
  }]
}
```

### 5. DynamoDB Tables

#### Table: `clinical-results`
```
Primary key: audio_key (String)
Billing mode: On-demand
Region: ap-southeast-2
```

**Maps to code**:
- `backend/api_lambda.py`: Reads results
- `docker/worker.py`: Writes results

**Item structure**:
```json
{
  "audio_key": "uploads/uuid.webm",
  "transcript": "Full transcription text...",
  "diagnosis": "AI extracted diagnosis",
  "medications": ["List", "of", "medications"],
  "follow_up": "Follow-up instructions",
  "notes": "Additional notes"
}
```

#### Table: `websocket-connections`
```
Purpose: Store WebSocket connection IDs
Status: Created but not used in current code
```

### 6. EC2 Instance

#### Instance: `i-0069540f657963c71`
```
Type: c7i-flex.large (2 vCPU, 4GB RAM)
AMI: ami-0b8d527345fdace59 (Amazon Linux 2)
Key Pair: personal_pair
Security Group: sg-084cb56fa4c5f7e1c
Public IP: 52.63.25.129
Status: STOPPED (to save costs)
```

**Maps to code**: Runs `docker/worker.py` in container
**IAM Role**: `EC2TranscribeRole`
**Permissions**:
- S3: Download/delete from clinical-audio-bucket
- SQS: Receive/delete messages from clinical-processing-queue
- DynamoDB: Write to clinical-results table
- Bedrock: Invoke Claude Haiku model

### 7. IAM Roles

#### Role: `ApiLambdaRole`
```
ARN: arn:aws:iam::958175315966:role/ApiLambdaRole
Used by: Lambda functions
Trust policy: lambda.amazonaws.com
```

**Attached policies** (inferred):
- S3: GetObject, PutObject on clinical-audio-bucket
- DynamoDB: GetItem, PutItem on clinical-results
- Logs: CreateLogGroup, CreateLogStream, PutLogEvents

#### Role: `EC2TranscribeRole`
```
Used by: EC2 instance
Trust policy: ec2.amazonaws.com
```

**Attached policies** (inferred):
- S3: GetObject, DeleteObject on clinical-audio-bucket
- SQS: ReceiveMessage, DeleteMessage on clinical-processing-queue
- DynamoDB: PutItem on clinical-results
- Bedrock: InvokeModel

### Resource Dependencies:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ API Gateway │───▶│   Lambda    │───▶│ DynamoDB    │
│ n465kxij69  │    │clinical-api │    │clinical-    │
└─────────────┘    └─────────────┘    │results      │
                           │           └─────────────┘
                           ▼
                   ┌─────────────┐
                   │     S3      │
                   │clinical-    │◀──┐
                   │audio-bucket │   │
                   └─────────────┘   │
                           │         │
                           ▼         │
                   ┌─────────────┐   │
                   │     SQS     │   │
                   │clinical-    │   │
                   │processing-  │   │
                   │queue        │   │
                   └─────────────┘   │
                           │         │
                           ▼         │
                   ┌─────────────┐   │
                   │     EC2     │───┘
                   │i-0069540f6  │
                   │57963c71     │
                   └─────────────┘
                           │
                           ▼
                   ┌─────────────┐
                   │   Bedrock   │
                   │Claude Haiku │
                   └─────────────┘
```

---

## Complete Data Flow

Let's trace a complete request from start to finish:

### Step-by-Step Process:

#### 1. User Interaction (Frontend)
```
User clicks "Start Recording" → Browser requests microphone access
↓
MediaRecorder API captures audio → Stores in memory as chunks
↓
User clicks "Stop Recording" → Creates WebM blob from chunks
```

#### 2. Upload Preparation (Frontend → Lambda)
```javascript
// Frontend makes API call
fetch('https://n465kxij69.execute-api.ap-southeast-2.amazonaws.com/get-upload-url')
```

```python
# Lambda generates presigned URL
key = f"uploads/{uuid4()}.webm"  # e.g., "uploads/abc123.webm"
url = s3.generate_presigned_url('put_object', 
    Params={'Bucket': 'clinical-audio-bucket', 'Key': key},
    ExpiresIn=300)
return {'upload_url': url, 'key': key}
```

#### 3. Direct Upload (Frontend → S3)
```javascript
// Browser uploads directly to S3
fetch(presigned_url, {
    method: 'PUT',
    body: audio_blob,
    headers: {'Content-Type': 'audio/webm'}
})
```

**What happens in S3:**
- File stored as `clinical-audio-bucket/uploads/abc123.webm`
- S3 event notification triggered
- Message sent to SQS queue

#### 4. Queue Processing (S3 → SQS)
```json
// SQS receives message like this:
{
  "Records": [{
    "eventName": "ObjectCreated:Put",
    "s3": {
      "bucket": {"name": "clinical-audio-bucket"},
      "object": {"key": "uploads/abc123.webm", "size": 245760}
    }
  }]
}
```

#### 5. Worker Processing (EC2 → Multiple AWS Services)

**5a. Message Retrieval:**
```python
# Worker polls SQS
resp = sqs.receive_message(QueueUrl=QUEUE_URL, WaitTimeSeconds=20)
message = resp['Messages'][0]
```

**5b. File Download:**
```python
# Extract S3 details from message
bucket = "clinical-audio-bucket"
key = "uploads/abc123.webm"

# Download to local storage
s3.download_file(bucket, key, "/tmp/abc123.webm")
```

**5c. Speech-to-Text:**
```python
# Whisper transcription
transcript = model.transcribe("/tmp/abc123.webm")["text"]
# Result: "Patient presents with cough and fever for 3 days..."
```

**5d. AI Analysis:**
```python
# Send to Bedrock Claude
prompt = """Return ONLY valid JSON: {"diagnosis":"string","medications":[],"follow_up":"string","notes":"string"}

Transcript: Patient presents with cough and fever for 3 days..."""

response = bedrock.invoke_model(
    modelId='anthropic.claude-3-haiku-20240307-v1:0',
    body=json.dumps({
        'messages': [{'role': 'user', 'content': prompt}]
    })
)

# Claude returns:
{
  "diagnosis": "Upper respiratory tract infection",
  "medications": ["Paracetamol 500mg QID", "Amoxicillin 500mg TDS"],
  "follow_up": "Return if symptoms worsen or persist >7 days",
  "notes": "Patient appears well, no signs of pneumonia"
}
```

**5e. Result Storage:**
```python
# Store in DynamoDB
dynamodb.Table('clinical-results').put_item(Item={
    'audio_key': 'uploads/abc123.webm',
    'transcript': 'Patient presents with cough and fever...',
    'diagnosis': 'Upper respiratory tract infection',
    'medications': ['Paracetamol 500mg QID', 'Amoxicillin 500mg TDS'],
    'follow_up': 'Return if symptoms worsen or persist >7 days',
    'notes': 'Patient appears well, no signs of pneumonia'
})
```

**5f. Cleanup:**
```python
# Delete S3 file (save storage costs)
s3.delete_object(Bucket=bucket, Key=key)

# Delete local file
os.remove("/tmp/abc123.webm")

# Delete SQS message (mark as processed)
sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)
```

#### 6. Result Retrieval (Frontend → Lambda → DynamoDB)

**Frontend polling:**
```javascript
// Poll every 2 seconds for results
async function pollForResult(key) {
    const response = await fetch(`${API_URL}/result/${key}`);
    if (response.ok) {
        return await response.json();  // Got results!
    }
    // Still processing, try again in 2 seconds
}
```

**Lambda query:**
```python
# Lambda checks DynamoDB
table = dynamodb.Table('clinical-results')
response = table.get_item(Key={'audio_key': key})

if 'Item' in response:
    return {
        'statusCode': 200,
        'body': json.dumps(response['Item'])
    }
else:
    return {
        'statusCode': 404,
        'body': '{"status": "processing"}'
    }
```

#### 7. Display Results (Frontend)
```javascript
// Frontend receives and displays results
{
  "audio_key": "uploads/abc123.webm",
  "transcript": "Patient presents with cough and fever for 3 days...",
  "diagnosis": "Upper respiratory tract infection",
  "medications": ["Paracetamol 500mg QID", "Amoxicillin 500mg TDS"],
  "follow_up": "Return if symptoms worsen or persist >7 days",
  "notes": "Patient appears well, no signs of pneumonia"
}
```

### Timing Analysis:

| Step | Duration | Bottleneck |
|------|----------|------------|
| Recording | 30-300 seconds | User interaction |
| Upload URL generation | <100ms | Lambda cold start |
| S3 upload | 1-5 seconds | Internet speed |
| SQS notification | <1 second | AWS internal |
| Worker pickup | 0-20 seconds | Polling interval |
| Whisper transcription | 10-60 seconds | Audio length, CPU |
| Bedrock analysis | 1-5 seconds | Model complexity |
| DynamoDB storage | <100ms | Network latency |
| Result retrieval | <100ms | Polling frequency |

**Total processing time**: 15-90 seconds (mostly Whisper transcription)

### Error Handling:

**What happens if something fails?**

1. **S3 upload fails**: Frontend shows error, user can retry
2. **Worker crashes**: SQS message becomes visible again, retry automatically
3. **Whisper fails**: Error logged, message deleted (manual intervention needed)
4. **Bedrock fails**: Fallback to transcript-only result
5. **DynamoDB fails**: Worker retries, then sends to dead letter queue

### Cost Breakdown (Estimated):

**Per audio file processed:**
- S3 storage: $0.000001 (deleted after processing)
- Lambda invocations: $0.0000002 (2 calls)
- API Gateway: $0.0000035 (2 requests)
- SQS messages: $0.0000004 (1 message)
- DynamoDB write: $0.00000125 (1 item)
- Bedrock Claude: $0.001-0.01 (depends on transcript length)
- EC2 (when running): $0.05/hour

**Total per file**: ~$0.001-0.01 (mostly Bedrock costs)
**Monthly cost (100 files)**: ~$0.10-1.00 + EC2 runtime costs
---

## Deployment & Operations

### Understanding CI/CD (Continuous Integration/Continuous Deployment)

**What is CI/CD?**
CI/CD is like having a robot assistant that automatically tests and deploys your code whenever you make changes.

**Your GitHub Actions Workflow** (`.github/workflows/deploy.yml`):

```yaml
name: Deploy to EC2
on:
  push:
    branches: [main]  # Triggers when you push to main branch
```

**Step-by-step process:**

#### 1. Code Push Trigger
```bash
# When you run these commands:
git add .
git commit -m "Update worker code"
git push origin main

# GitHub automatically starts the deployment process
```

#### 2. Docker Build & Push
```yaml
- name: Build and push Docker image
  run: |
    echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
    docker build -t ${{ secrets.DOCKER_USERNAME }}/clinical-recorder:latest ./docker
    docker push ${{ secrets.DOCKER_USERNAME }}/clinical-recorder:latest
```

**What this does:**
- Logs into Docker Hub using stored credentials
- Builds new Docker image from `docker/` folder
- Tags it as "latest" version
- Pushes to Docker Hub registry (like GitHub for Docker images)

#### 3. EC2 Deployment
```yaml
- name: Deploy to EC2
  uses: appleboy/ssh-action@v1.0.3
  with:
    host: ${{ secrets.EC2_HOST }}        # 52.63.25.129
    username: ${{ secrets.EC2_USER }}    # ec2-user
    key: ${{ secrets.EC2_SSH_KEY }}      # SSH private key
    script: |
      docker pull ${{ secrets.DOCKER_USERNAME }}/clinical-recorder:latest
      docker stop clinical-recorder || true
      docker rm clinical-recorder || true
      docker run -d --name clinical-recorder \
        -e AWS_REGION=${{ secrets.AWS_REGION }} \
        -e QUEUE_URL=${{ secrets.QUEUE_URL }} \
        -e TABLE_NAME=${{ secrets.TABLE_NAME }} \
        -e AWS_ACCESS_KEY_ID=${{ secrets.AWS_ACCESS_KEY_ID }} \
        -e AWS_SECRET_ACCESS_KEY=${{ secrets.AWS_SECRET_ACCESS_KEY }} \
        ${{ secrets.DOCKER_USERNAME }}/clinical-recorder:latest
```

**What this does:**
- SSHs into your EC2 instance
- Downloads latest Docker image
- Stops old container (if running)
- Starts new container with environment variables

### Manual Deployment Options

#### Option 1: Deploy Lambda Function
```bash
# Package your Lambda code
cd backend
zip -r api_lambda.zip api_lambda.py

# Upload to AWS
aws lambda update-function-code \
  --function-name clinical-api \
  --zip-file fileb://api_lambda.zip \
  --region ap-southeast-2

# Update environment variables if needed
aws lambda update-function-configuration \
  --function-name clinical-api \
  --environment Variables='{BUCKET_NAME=clinical-audio-bucket,TABLE_NAME=clinical-results}' \
  --region ap-southeast-2
```

#### Option 2: Deploy Worker to EC2
```bash
# Build and push Docker image manually
cd docker
docker build -t yourusername/clinical-recorder:v1.0 .
docker push yourusername/clinical-recorder:v1.0

# SSH to EC2 and update
ssh -i ~/.ssh/personal_pair.pem ec2-user@52.63.25.129

# On EC2 instance:
docker pull yourusername/clinical-recorder:v1.0
docker stop clinical-recorder
docker rm clinical-recorder
docker run -d --name clinical-recorder \
  -e AWS_REGION=ap-southeast-2 \
  -e QUEUE_URL=https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue \
  -e TABLE_NAME=clinical-results \
  yourusername/clinical-recorder:v1.0
```

### Infrastructure Management

#### Starting/Stopping EC2 (Cost Management)
```bash
# Start EC2 instance when you need processing
aws ec2 start-instances --instance-ids i-0069540f657963c71 --region ap-southeast-2

# Check status
aws ec2 describe-instances --instance-ids i-0069540f657963c71 --region ap-southeast-2 \
  --query 'Reservations[0].Instances[0].State.Name'

# Stop EC2 instance to save money
aws ec2 stop-instances --instance-ids i-0069540f657963c71 --region ap-southeast-2
```

**Cost Impact:**
- **Running**: ~$0.05/hour = $36/month if left on 24/7
- **Stopped**: $0/hour (only pay for EBS storage ~$1/month)

#### Scaling Considerations

**Current Limitations:**
- Single EC2 instance (bottleneck for high volume)
- Manual start/stop (not automated)
- No load balancing

**Scaling Options:**
1. **Auto Scaling Group**: Automatically add/remove instances based on SQS queue depth
2. **Larger Instance**: Use c7i.xlarge for faster processing
3. **GPU Instance**: Use g4dn.xlarge for GPU-accelerated Whisper
4. **Multiple Regions**: Deploy in multiple AWS regions for global coverage

### Security Best Practices

#### IAM (Identity and Access Management)

**Current Setup:**
- **ApiLambdaRole**: Minimal permissions for Lambda functions
- **EC2TranscribeRole**: Permissions for EC2 worker
- **Your User**: Admin access (should be restricted in production)

**Production Recommendations:**
```json
// Lambda role policy (minimal permissions)
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::clinical-audio-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem"
      ],
      "Resource": "arn:aws:dynamodb:ap-southeast-2:958175315966:table/clinical-results"
    }
  ]
}
```

#### Data Protection

**Current Security Measures:**
- **Encryption at rest**: DynamoDB and S3 use AWS default encryption
- **Encryption in transit**: All API calls use HTTPS/TLS
- **Access control**: IAM roles limit service permissions
- **Temporary storage**: Audio files deleted after processing

**Healthcare Compliance Considerations:**
- **HIPAA (US)**: Would need additional encryption, audit logging, BAAs
- **Privacy Act 2020 (NZ)**: Current setup provides reasonable protection
- **Data residency**: All data stays in Australia (ap-southeast-2)

#### Secrets Management

**Current Approach:**
- GitHub Secrets for CI/CD credentials
- Environment variables for configuration
- IAM roles for AWS service access

**Production Improvements:**
- **AWS Secrets Manager**: Store database passwords, API keys
- **Parameter Store**: Store configuration values
- **KMS**: Custom encryption keys for sensitive data

---

## Troubleshooting & Monitoring

### Common Issues and Solutions

#### 1. "Frontend can't upload files"

**Symptoms:**
- Upload fails with CORS error
- Network error in browser console
- 403 Forbidden error

**Diagnosis:**
```bash
# Check if Lambda is working
curl https://n465kxij69.execute-api.ap-southeast-2.amazonaws.com/get-upload-url

# Check S3 bucket permissions
aws s3api get-bucket-cors --bucket clinical-audio-bucket --region ap-southeast-2
```

**Solutions:**
- Verify API Gateway URL in `index.html` line 23
- Check Lambda function CORS headers
- Ensure S3 bucket allows presigned URL uploads

#### 2. "Files uploaded but not processed"

**Symptoms:**
- Files appear in S3 bucket
- No results in DynamoDB
- SQS queue has messages

**Diagnosis:**
```bash
# Check EC2 status
aws ec2 describe-instances --instance-ids i-0069540f657963c71 --region ap-southeast-2

# Check SQS queue
aws sqs get-queue-attributes \
  --queue-url https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-2

# SSH to EC2 and check Docker
ssh -i ~/.ssh/personal_pair.pem ec2-user@52.63.25.129
docker ps
docker logs clinical-recorder
```

**Solutions:**
- Start EC2 instance if stopped
- Restart Docker container if crashed
- Check worker logs for errors
- Verify SQS permissions

#### 3. "Whisper transcription fails"

**Symptoms:**
- Worker logs show ffmpeg errors
- Audio files not supported
- Out of memory errors

**Diagnosis:**
```bash
# Check Docker container resources
docker stats clinical-recorder

# Check audio file format
file /tmp/audio_file.webm
ffprobe /tmp/audio_file.webm
```

**Solutions:**
- Ensure ffmpeg is installed in Docker image
- Use supported audio formats (WebM, MP3, WAV)
- Increase EC2 instance memory if needed
- Check audio file isn't corrupted

#### 4. "Bedrock AI analysis fails"

**Symptoms:**
- Transcription works but no structured data
- Bedrock permission errors
- JSON parsing errors

**Diagnosis:**
```bash
# Check Bedrock model access
aws bedrock list-foundation-models --region ap-southeast-2

# Test Bedrock directly
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-haiku-20240307-v1:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}' \
  --region ap-southeast-2 \
  output.json
```

**Solutions:**
- Verify Bedrock model permissions in IAM role
- Check if model is available in ap-southeast-2 region
- Improve JSON parsing with better regex
- Add fallback for when AI analysis fails

### Monitoring and Logging

#### CloudWatch Logs

**Lambda Logs:**
```bash
# View recent Lambda logs
aws logs tail /aws/lambda/clinical-api --region ap-southeast-2 --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/clinical-api \
  --filter-pattern "ERROR" \
  --region ap-southeast-2
```

**EC2 Logs:**
```bash
# SSH to EC2 and check Docker logs
ssh -i ~/.ssh/personal_pair.pem ec2-user@52.63.25.129
docker logs clinical-recorder --tail 100 --follow
```

#### Performance Monitoring

**Key Metrics to Watch:**
- **Lambda duration**: Should be <1 second for API calls
- **SQS queue depth**: Should be near 0 when processing normally
- **DynamoDB read/write capacity**: Monitor for throttling
- **S3 storage**: Should stay low (files deleted after processing)
- **EC2 CPU/Memory**: Monitor during processing

**CloudWatch Dashboards:**
```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name "ClinicalRecorder" \
  --dashboard-body file://dashboard.json \
  --region ap-southeast-2
```

#### Cost Monitoring

**AWS Cost Explorer:**
- Monitor monthly costs by service
- Set up billing alerts for unexpected charges
- Track costs per processed file

**Typical Monthly Costs (100 files):**
- Lambda: $0.01
- API Gateway: $0.01
- S3: $0.01
- SQS: $0.01
- DynamoDB: $0.25
- Bedrock: $1-10 (depends on transcript length)
- EC2: $0-36 (depends on runtime)

### Performance Optimization

#### Lambda Optimization
```python
# Keep connections outside handler for reuse
s3 = boto3.client('s3', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)

def handler(event, context):
    # Handler code here
    pass
```

#### Worker Optimization
```python
# Load Whisper model once, not per file
model = whisper.load_model("medium")

# Process multiple messages in batch
resp = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=10)
```

#### Database Optimization
```python
# Use batch operations for multiple items
with table.batch_writer() as batch:
    for item in items:
        batch.put_item(Item=item)
```

### Backup and Disaster Recovery

#### Data Backup
```bash
# Export DynamoDB table
aws dynamodb scan --table-name clinical-results --region ap-southeast-2 > backup.json

# Enable point-in-time recovery
aws dynamodb update-continuous-backups \
  --table-name clinical-results \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
  --region ap-southeast-2
```

#### Infrastructure Backup
```bash
# Export Lambda function
aws lambda get-function --function-name clinical-api --region ap-southeast-2

# Backup EC2 instance
aws ec2 create-image \
  --instance-id i-0069540f657963c71 \
  --name "clinical-recorder-backup-$(date +%Y%m%d)" \
  --region ap-southeast-2
```

#### Disaster Recovery Plan
1. **Lambda functions**: Redeploy from source code
2. **API Gateway**: Recreate with same configuration
3. **S3 bucket**: Recreate with event notifications
4. **SQS queue**: Recreate with same settings
5. **DynamoDB**: Restore from backup or point-in-time recovery
6. **EC2**: Launch new instance from AMI backup

---

## Conclusion

You now have a complete understanding of your Clinical Recorder system:

### What You've Learned:
1. **AWS Services**: Lambda, API Gateway, S3, SQS, DynamoDB, Bedrock, EC2
2. **Technologies**: Docker, Whisper AI, Python, JavaScript
3. **Architecture**: Serverless + containerized hybrid approach
4. **Data Flow**: From audio recording to structured clinical data
5. **Operations**: Deployment, monitoring, troubleshooting

### Key Takeaways:
- **Serverless**: Lambda and API Gateway handle variable load automatically
- **Event-driven**: S3 → SQS → EC2 provides reliable processing pipeline
- **Cost-effective**: Pay only for what you use, stop EC2 when not needed
- **Scalable**: Can handle more users by adding EC2 instances
- **Secure**: IAM roles, encryption, and temporary storage protect data

### Next Steps for Production:
1. **Infrastructure as Code**: Use Terraform or CloudFormation
2. **Auto Scaling**: Implement EC2 Auto Scaling based on SQS depth
3. **Monitoring**: Set up CloudWatch dashboards and alerts
4. **Security**: Implement proper healthcare compliance measures
5. **Testing**: Add automated tests for all components

This system demonstrates modern cloud architecture principles and provides a solid foundation for a healthcare AI application. The combination of serverless and containerized components gives you the best of both worlds: automatic scaling for the API layer and full control for the AI processing layer.
