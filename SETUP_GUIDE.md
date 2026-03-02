# Clinical Recorder - Enhanced System Setup Guide

## Overview

You now have a **fully functional workflow system** with **dormant integrations** ready to activate when you get API credentials.

**Current Mode:** Manual workflow (INTEGRATIONS_ENABLED=false)
**Future Mode:** Full automation (INTEGRATIONS_ENABLED=true + API keys)

---

## What's Been Built

### 1. **Configuration System** (`config/settings.py`)
- Feature flags for all integrations
- Environment variable configuration
- Easy toggle between manual and automatic modes

### 2. **Enhanced Database** (`storage/dynamodb/enhanced_storage.py`)
- Approval workflow tracking
- Patient history queries
- Task management
- Consent tracking
- Audit logging

### 3. **Integration Framework** (`integrations/`)
- Base adapter interface
- Medtech PMS adapter (ready for API key)
- AWS Notifications adapter (works immediately)
- Pharmacy, Radiology, Lab adapters (templates ready)

### 4. **Task Router** (`automation/task_router.py`)
- Automatic task routing when integrations enabled
- Email/SMS notifications in manual mode
- Intelligent fallback system

### 5. **Enhanced API** (`backend/api_lambda_enhanced.py`)
- Approval workflow endpoints
- Patient history endpoints
- Task management endpoints
- Handover generation
- Consent management

### 6. **Frontend API Service** (`frontend/api-service.js`)
- Complete API client
- Ready for UI integration

---

## AWS Infrastructure Setup

### Step 1: Update Lambda Function

```bash
# Package dependencies
cd /Users/thireshannaidoo/Documents/Transcriber
pip install -t lambda_layer/python boto3 requests

# Create layer
cd lambda_layer
zip -r ../lambda_layer.zip .
cd ..

# Upload layer to AWS
aws lambda publish-layer-version \
    --layer-name clinical-recorder-deps \
    --zip-file fileb://lambda_layer.zip \
    --compatible-runtimes python3.11 \
    --region ap-southeast-2

# Update Lambda function code
zip -r lambda_function.zip backend/ config/ storage/ integrations/ automation/ shared/ analysis/ pdf/

aws lambda update-function-code \
    --function-name clinical-recorder-api \
    --zip-file fileb://lambda_function.zip \
    --region ap-southeast-2

# Attach layer to function
aws lambda update-function-configuration \
    --function-name clinical-recorder-api \
    --layers arn:aws:lambda:ap-southeast-2:YOUR_ACCOUNT:layer:clinical-recorder-deps:1 \
    --region ap-southeast-2
```

### Step 2: Set Environment Variables

```bash
aws lambda update-function-configuration \
    --function-name clinical-recorder-api \
    --environment Variables="{
        INTEGRATIONS_ENABLED=false,
        ENABLE_EMAIL_NOTIFICATIONS=true,
        ENABLE_SMS_NOTIFICATIONS=false,
        AWS_REGION=ap-southeast-2,
        BUCKET_NAME=clinical-audio-bucket,
        TABLE_NAME=clinical-results,
        QUEUE_URL=https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue,
        SES_FROM_EMAIL=noreply@yourdomain.com
    }" \
    --region ap-southeast-2
```

### Step 3: Setup SES for Email Notifications

```bash
# Verify your email address
aws ses verify-email-identity \
    --email-address noreply@yourdomain.com \
    --region ap-southeast-2

# Check verification status
aws ses get-identity-verification-attributes \
    --identities noreply@yourdomain.com \
    --region ap-southeast-2

# Move out of sandbox (for production)
# Go to AWS Console > SES > Account Dashboard > Request Production Access
```

### Step 4: Setup SNS for SMS (Optional)

```bash
# Create SNS topic
aws sns create-topic \
    --name clinical-notifications \
    --region ap-southeast-2

# Note the TopicArn and add to Lambda environment variables
```

### Step 5: Update DynamoDB Indexes (for better queries)

```bash
# Create GSI for patient_id
aws dynamodb update-table \
    --table-name clinical-results \
    --attribute-definitions \
        AttributeName=patient_id,AttributeType=S \
    --global-secondary-index-updates \
        "[{\"Create\":{\"IndexName\":\"patient-index\",\"KeySchema\":[{\"AttributeName\":\"patient_id\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}}]" \
    --region ap-southeast-2

# Create GSI for approval_status
aws dynamodb update-table \
    --table-name clinical-results \
    --attribute-definitions \
        AttributeName=approval_status,AttributeType=S \
    --global-secondary-index-updates \
        "[{\"Create\":{\"IndexName\":\"approval-index\",\"KeySchema\":[{\"AttributeName\":\"approval_status\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}}]" \
    --region ap-southeast-2
```

---

## Testing the System

### Test 1: Check Integration Status

```bash
curl https://your-api-gateway-url.execute-api.ap-southeast-2.amazonaws.com/integration/status
```

Expected response:
```json
{
  "integrations_enabled": false,
  "active_integrations": {
    "medtech": false,
    "pharmacy": false,
    "radiology": false,
    "lab": false,
    "healthlink": false,
    "email": true,
    "sms": false
  },
  "mode": "manual"
}
```

### Test 2: Record Consent

```bash
curl -X POST https://your-api-gateway-url/consent/record \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "TEST001",
    "consent_type": "recording",
    "granted": true,
    "recorded_by": "Dr. Smith"
  }'
```

### Test 3: Get Pending Approvals

```bash
curl https://your-api-gateway-url/approvals/pending
```

### Test 4: Approve Consultation

```bash
curl -X POST https://your-api-gateway-url/approvals/approve \
  -H "Content-Type: application/json" \
  -d '{
    "audio_key": "uploads/test_xxx.webm",
    "approved_by": "Dr. Smith",
    "notes": "Reviewed and approved"
  }'
```

### Test 5: Get Pending Tasks

```bash
curl https://your-api-gateway-url/tasks/pending
```

---

## Enabling Integrations (When Ready)

### Medtech Integration

1. **Get API Access:**
   - Contact Medtech: support@medtechglobal.com
   - Request API documentation and credentials
   - Obtain: API_URL, API_KEY, CLIENT_ID

2. **Configure:**
```bash
aws lambda update-function-configuration \
    --function-name clinical-recorder-api \
    --environment Variables="{
        INTEGRATIONS_ENABLED=true,
        ENABLE_MEDTECH=true,
        MEDTECH_API_URL=https://api.medtech.co.nz,
        MEDTECH_API_KEY=your_api_key,
        MEDTECH_CLIENT_ID=your_client_id,
        ...other vars...
    }"
```

3. **Test:**
```bash
curl https://your-api-gateway-url/integration/status
# Should show medtech: true
```

### Pharmacy Integration

Similar process - contact your pharmacy system vendor for API access.

### HealthLink Integration

1. **Apply for HealthLink Access:**
   - Visit: https://www.healthlink.net/
   - Apply for provider access
   - Complete certification process

2. **Configure once approved**

---

## Frontend Development

### Option 1: Use Existing HTML (Quick Start)

Update your current `index.html` to use the new API service:

```html
<script src="frontend/api-service.js"></script>
<script>
const api = new APIService('https://your-api-gateway-url');

// Example: Get pending approvals
async function loadApprovals() {
    const data = await api.getPendingApprovals();
    console.log('Pending approvals:', data);
    // Render in UI
}
</script>
```

### Option 2: Build React Frontend (Advanced)

```bash
cd frontend
npm install
npm start
```

Then build components for:
- Dashboard (patient list, pending approvals)
- Approval interface
- Task management
- Patient history timeline
- Handover report

---

## Current Capabilities (Manual Mode)

✅ **Record consultations** - Works as before
✅ **AI extraction** - Works as before
✅ **Approval workflow** - NEW: Doctor reviews before finalizing
✅ **Patient history** - NEW: View all past consultations
✅ **Task management** - NEW: Track and complete tasks
✅ **Email notifications** - NEW: Automatic emails for tasks
✅ **Handover reports** - NEW: End-of-shift summaries
✅ **Consent tracking** - NEW: GDPR/Privacy Act compliance
✅ **Audit logging** - NEW: Track all actions

---

## Future Capabilities (When Integrations Enabled)

🔄 **Auto-save to Medtech** - Consultation notes automatically appear in PMS
🔄 **Auto-send prescriptions** - Pharmacy receives orders automatically
🔄 **Auto-book imaging** - Radiology appointments created automatically
🔄 **Auto-order labs** - Lab tests ordered automatically
🔄 **Auto-send referrals** - HealthLink delivers referrals automatically
🔄 **Pre-consultation context** - Patient history loaded before consultation

---

## Monitoring & Maintenance

### Check Lambda Logs

```bash
aws logs tail /aws/lambda/clinical-recorder-api --follow --region ap-southeast-2
```

### Check DynamoDB Items

```bash
aws dynamodb scan \
    --table-name clinical-results \
    --filter-expression "approval_status = :status" \
    --expression-attribute-values '{":status":{"S":"pending_approval"}}' \
    --region ap-southeast-2
```

### Monitor Costs

```bash
aws ce get-cost-and-usage \
    --time-period Start=2026-03-01,End=2026-03-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --region us-east-1
```

---

## Troubleshooting

### Issue: "Medtech not configured"

**Solution:** This is expected. Medtech integration is dormant until you add API credentials.

### Issue: Email notifications not working

**Solution:** 
1. Verify email in SES: `aws ses verify-email-identity --email-address your@email.com`
2. Check SES is out of sandbox mode
3. Check Lambda has SES permissions

### Issue: Tasks not routing

**Solution:**
1. Check `INTEGRATIONS_ENABLED` is set correctly
2. Verify consultation is approved (tasks only route after approval)
3. Check Lambda logs for errors

---

## Next Steps

1. **Test the approval workflow** - Upload a consultation, approve it, see tasks
2. **Setup email notifications** - Verify SES email, test task notifications
3. **Build/update frontend** - Create approval interface and task dashboard
4. **Apply for Medtech API** - Start the process (takes 2-4 weeks)
5. **Apply for HealthLink** - Start certification process (takes 1-3 months)
6. **Demo to clinics** - Show the manual workflow system
7. **Iterate based on feedback** - Improve before adding integrations

---

## Support & Documentation

- **AWS Lambda Docs:** https://docs.aws.amazon.com/lambda/
- **AWS SES Docs:** https://docs.aws.amazon.com/ses/
- **Medtech API:** Contact Medtech support
- **HealthLink:** https://www.healthlink.net/

---

## Summary

You now have:
- ✅ Fully functional workflow system (works today)
- ✅ Integration framework (ready for API keys)
- ✅ Approval workflow (human-in-the-loop)
- ✅ Task management (track everything)
- ✅ Patient history (complete timeline)
- ✅ Compliance features (consent, audit)
- ✅ Email notifications (works immediately)

**The system is production-ready in manual mode and will seamlessly upgrade to full automation when you add integration credentials.**
