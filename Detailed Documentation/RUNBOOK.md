# Clinical Recorder Runbook

## Quick Start

### Prerequisites
- AWS CLI configured with credentials
- Docker installed (for local development)
- Python 3.12+ (for local Lambda testing)

### Current Status Check
```bash
# Check AWS authentication
aws sts get-caller-identity --region ap-southeast-2

# Check EC2 instance status
aws ec2 describe-instances --instance-ids i-0069540f657963c71 --region ap-southeast-2 --query 'Reservations[0].Instances[0].State.Name'

# Check SQS queue
aws sqs get-queue-attributes --queue-url https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue --region ap-southeast-2
```

## Local Development

### Running Frontend Locally
```bash
# Serve static HTML file
python3 -m http.server 8000
# Open http://localhost:8000/index.html

# Or open directly in browser
open index.html
```

### Testing Lambda API Locally
```bash
cd backend
pip install boto3

# Set environment variables
export BUCKET_NAME=clinical-audio-bucket
export TABLE_NAME=clinical-results
export AWS_REGION=ap-southeast-2

# Test locally (requires AWS credentials)
python3 -c "
import api_lambda
event = {'rawPath': '/get-upload-url', 'requestContext': {'http': {'method': 'GET'}}}
print(api_lambda.handler(event, {}))
"
```

### Running Worker Locally (Docker)
```bash
cd docker

# Build container
docker build -t clinical-worker .

# Run with AWS credentials
docker run -e AWS_REGION=ap-southeast-2 \
  -e QUEUE_URL=https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue \
  -e TABLE_NAME=clinical-results \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  clinical-worker
```

### Local vs AWS Services

**What runs locally:**
- Frontend HTML/JS (static files)
- Docker worker container (with AWS API calls)
- Lambda function code (for testing)

**What requires AWS:**
- S3 bucket for file storage
- SQS queue for job processing
- DynamoDB for results storage
- Bedrock AI for clinical analysis
- API Gateway for production endpoints

**Mock/Stub Options:**
- Use LocalStack for S3/SQS/DynamoDB simulation
- Mock Bedrock calls with static JSON responses
- Use local file system instead of S3 for development

## Production Deployment

### Deploy Lambda Functions
```bash
# Package and deploy API Lambda
cd backend
zip -r api_lambda.zip api_lambda.py
aws lambda update-function-code \
  --function-name clinical-api \
  --zip-file fileb://api_lambda.zip \
  --region ap-southeast-2
```

### Deploy Worker to EC2
```bash
# Automated via GitHub Actions on push to main branch
git add .
git commit -m "Deploy worker updates"
git push origin main

# Manual deployment
docker build -t your-dockerhub/clinical-recorder:latest ./docker
docker push your-dockerhub/clinical-recorder:latest

# SSH to EC2 and update
ssh -i ~/.ssh/personal_pair.pem ec2-user@52.63.25.129
docker pull your-dockerhub/clinical-recorder:latest
docker stop clinical-recorder || true
docker rm clinical-recorder || true
docker run -d --name clinical-recorder \
  -e AWS_REGION=ap-southeast-2 \
  -e QUEUE_URL=https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue \
  -e TABLE_NAME=clinical-results \
  your-dockerhub/clinical-recorder:latest
```

### Start/Stop EC2 Processing
```bash
# Start EC2 instance
aws ec2 start-instances --instance-ids i-0069540f657963c71 --region ap-southeast-2

# Check status
aws ec2 describe-instances --instance-ids i-0069540f657963c71 --region ap-southeast-2 --query 'Reservations[0].Instances[0].State.Name'

# Stop EC2 instance (to save costs)
aws ec2 stop-instances --instance-ids i-0069540f657963c71 --region ap-southeast-2
```

## Monitoring & Troubleshooting

### Check System Health
```bash
# Lambda function logs
aws logs tail /aws/lambda/clinical-api --region ap-southeast-2 --follow

# SQS queue depth
aws sqs get-queue-attributes \
  --queue-url https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-2

# DynamoDB item count
aws dynamodb scan --table-name clinical-results --select COUNT --region ap-southeast-2

# S3 bucket contents
aws s3 ls s3://clinical-audio-bucket/uploads/ --region ap-southeast-2
```

### Common Issues

**1. EC2 Worker Not Processing**
```bash
# Check if EC2 is running
aws ec2 describe-instances --instance-ids i-0069540f657963c71 --region ap-southeast-2

# SSH and check Docker container
ssh -i ~/.ssh/personal_pair.pem ec2-user@52.63.25.129
docker ps
docker logs clinical-recorder

# Restart container if needed
docker restart clinical-recorder
```

**2. Frontend Upload Fails**
- Check API Gateway endpoint in index.html (line 23)
- Verify CORS configuration in Lambda function
- Check S3 bucket permissions for presigned URLs

**3. No Results Returned**
- Check SQS queue for stuck messages
- Verify DynamoDB table has items
- Check Bedrock model permissions and quotas

**4. Audio Processing Errors**
- Check ffmpeg installation in Docker container
- Verify Whisper model download (first run takes time)
- Check audio file format compatibility (WebM supported)

### Performance Tuning

**Lambda Optimization:**
- Increase memory if processing large requests
- Enable provisioned concurrency for consistent performance
- Monitor cold start times

**EC2 Optimization:**
- Use larger instance type for faster Whisper processing
- Consider GPU instances for Whisper acceleration
- Implement auto-scaling based on SQS queue depth

**Cost Optimization:**
- Stop EC2 when not processing
- Set S3 lifecycle policy for automatic cleanup
- Use DynamoDB on-demand billing
- Monitor Bedrock token usage

## Configuration Management

### Environment Variables
```bash
# Production secrets (stored in GitHub Secrets)
AWS_REGION=ap-southeast-2
QUEUE_URL=https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue
TABLE_NAME=clinical-results
BUCKET_NAME=clinical-audio-bucket
EC2_HOST=52.63.25.129
EC2_USER=ec2-user
```

### API Endpoints
```bash
# Production API Gateway
API_URL=https://n465kxij69.execute-api.ap-southeast-2.amazonaws.com

# WebSocket endpoints
WSS_URL=wss://cmxbu5k037.execute-api.ap-southeast-2.amazonaws.com
```

### Resource Identifiers
```bash
# AWS Account: 958175315966
# Region: ap-southeast-2
# EC2 Instance: i-0069540f657963c71
# S3 Bucket: clinical-audio-bucket
# SQS Queue: clinical-processing-queue
# DynamoDB Tables: clinical-results, websocket-connections
```

## Backup & Recovery

### Data Backup
```bash
# Export DynamoDB table
aws dynamodb scan --table-name clinical-results --region ap-southeast-2 > clinical-results-backup.json

# S3 bucket backup (if needed)
aws s3 sync s3://clinical-audio-bucket ./s3-backup --region ap-southeast-2
```

### Disaster Recovery
1. Redeploy Lambda functions from source code
2. Recreate SQS queue with same configuration
3. Restore DynamoDB from backup
4. Launch new EC2 instance with same configuration
5. Update DNS/API Gateway endpoints if needed

## Security Checklist

- [ ] IAM roles follow least privilege principle
- [ ] No hardcoded credentials in source code
- [ ] S3 bucket has proper access controls
- [ ] EC2 security groups restrict unnecessary access
- [ ] API Gateway has CORS properly configured
- [ ] All communications use HTTPS/WSS
- [ ] Regular security updates for EC2 instance
- [ ] Monitor AWS CloudTrail for suspicious activity
