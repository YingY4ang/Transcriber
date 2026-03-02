# Clinical Recorder v2.0 - Deployment Checklist

## Pre-Deployment

### ✅ Code Review
- [ ] All new files created
- [ ] Configuration file (`config/settings.py`) reviewed
- [ ] API endpoints tested locally
- [ ] Integration adapters reviewed
- [ ] Frontend UI tested in browser

### ✅ AWS Prerequisites
- [ ] AWS CLI installed and configured
- [ ] Correct AWS region set (ap-southeast-2)
- [ ] IAM permissions for Lambda, S3, DynamoDB, SES, SNS
- [ ] Existing resources identified (S3 bucket, DynamoDB table, SQS queue)

---

## Deployment Steps

### Step 1: Deploy Lambda Function
```bash
cd /Users/thireshannaidoo/Documents/Transcriber
./deploy.sh
```

**Expected output:**
- ✓ Layer created
- ✓ Layer published
- ✓ Function packaged
- ✓ Function code updated
- ✓ Layer attached
- ✓ Environment variables set
- ✓ Handler updated

**Checklist:**
- [ ] Deployment script completed without errors
- [ ] Lambda function updated successfully
- [ ] Layer attached to function

### Step 2: Configure SES (Email Notifications)
```bash
# Verify sender email
aws ses verify-email-identity \
    --email-address noreply@yourdomain.com \
    --region ap-southeast-2

# Check verification status (wait for email, click link)
aws ses get-identity-verification-attributes \
    --identities noreply@yourdomain.com \
    --region ap-southeast-2
```

**Checklist:**
- [ ] Verification email received
- [ ] Email link clicked
- [ ] Status shows "Success"
- [ ] Test email sent successfully

### Step 3: Update DynamoDB Indexes (Optional but Recommended)
```bash
# Create patient_id index
aws dynamodb update-table \
    --table-name clinical-results \
    --attribute-definitions AttributeName=patient_id,AttributeType=S \
    --global-secondary-index-updates \
        '[{"Create":{"IndexName":"patient-index","KeySchema":[{"AttributeName":"patient_id","KeyType":"HASH"}],"Projection":{"ProjectionType":"ALL"},"ProvisionedThroughput":{"ReadCapacityUnits":5,"WriteCapacityUnits":5}}}]' \
    --region ap-southeast-2
```

**Checklist:**
- [ ] patient-index created
- [ ] Index status: ACTIVE
- [ ] approval-index created (optional)

### Step 4: Update Frontend Configuration
```bash
# Edit frontend/dashboard.html
# Update API_URL constant with your API Gateway URL
```

**Checklist:**
- [ ] API_URL updated in dashboard.html
- [ ] API_URL updated in api-service.js (if needed)
- [ ] Clinician ID configured

### Step 5: Test Deployment
```bash
# Test integration status
curl https://your-api-gateway-url/integration/status

# Expected response:
# {
#   "integrations_enabled": false,
#   "active_integrations": {
#     "medtech": false,
#     "pharmacy": false,
#     "email": true
#   },
#   "mode": "manual"
# }
```

**Checklist:**
- [ ] `/integration/status` returns 200
- [ ] `/config` returns configuration
- [ ] `/approvals/pending` returns empty list (or existing approvals)
- [ ] `/tasks/pending` returns empty list (or existing tasks)

---

## Post-Deployment Testing

### Test 1: Record Consent
```bash
curl -X POST https://your-api-url/consent/record \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "TEST001",
    "consent_type": "recording",
    "granted": true,
    "recorded_by": "Dr. Test"
  }'
```

**Expected:** `{"consent_id": "consent_...", "status": "recorded"}`

**Checklist:**
- [ ] Consent recorded successfully
- [ ] Consent retrievable via `/consent/check`

### Test 2: Upload and Process (End-to-End)
1. Open `frontend/dashboard.html` in browser
2. Go to "Record" tab
3. Enter patient ID: TEST001
4. Check both consent boxes
5. Click "Start Recording"
6. Speak for 10-15 seconds
7. Click "Stop Recording"
8. Wait for upload confirmation

**Checklist:**
- [ ] Recording started successfully
- [ ] Recording stopped successfully
- [ ] Upload completed
- [ ] Processing triggered

### Test 3: Check Approval Queue (After Processing)
Wait 2-3 minutes for processing, then:
```bash
curl https://your-api-url/approvals/pending
```

**Expected:** List with one consultation

**Checklist:**
- [ ] Consultation appears in pending approvals
- [ ] Patient ID correct
- [ ] Timestamp present
- [ ] Task count shown

### Test 4: Approve Consultation
```bash
curl -X POST https://your-api-url/approvals/approve \
  -H "Content-Type: application/json" \
  -d '{
    "audio_key": "uploads/TEST001_xxx.webm",
    "approved_by": "Dr. Test",
    "notes": "Reviewed and approved"
  }'
```

**Expected:** `{"status": "approved"}`

**Checklist:**
- [ ] Consultation approved
- [ ] No longer in pending approvals
- [ ] Tasks created

### Test 5: Check Tasks
```bash
curl https://your-api-url/tasks/pending
```

**Expected:** List of tasks from approved consultation

**Checklist:**
- [ ] Tasks listed
- [ ] Urgency levels correct
- [ ] Task descriptions present
- [ ] Patient ID attached to each task

### Test 6: Patient History
```bash
curl https://your-api-url/patient/TEST001
```

**Expected:** Patient history with consultation

**Checklist:**
- [ ] Consultation appears in history
- [ ] Timeline correct
- [ ] Diagnosis shown
- [ ] Medications listed

### Test 7: Email Notification (If SES Configured)
Should have received email notification for tasks.

**Checklist:**
- [ ] Email received
- [ ] Task details in email
- [ ] Urgency indicated
- [ ] Patient ID included

---

## Troubleshooting

### Issue: Lambda deployment fails
**Solution:**
- Check IAM permissions
- Verify Lambda function exists
- Check region is correct

### Issue: SES email not verified
**Solution:**
- Check spam folder for verification email
- Resend verification: `aws ses verify-email-identity --email-address your@email.com`
- Wait up to 5 minutes

### Issue: API returns 404
**Solution:**
- Verify API Gateway URL is correct
- Check Lambda function is attached to API Gateway
- Check handler is set to `backend.api_lambda_enhanced.handler`

### Issue: Consultations not appearing in approvals
**Solution:**
- Check Lambda logs: `aws logs tail /aws/lambda/clinical-recorder-api --follow`
- Verify EC2 worker is running
- Check SQS queue has messages
- Verify DynamoDB table name is correct

### Issue: Tasks not routing
**Solution:**
- Check `INTEGRATIONS_ENABLED` is set correctly
- Verify SES email is verified
- Check Lambda has SES permissions
- Review Lambda logs for errors

---

## Monitoring

### Lambda Logs
```bash
aws logs tail /aws/lambda/clinical-recorder-api --follow --region ap-southeast-2
```

### DynamoDB Items
```bash
aws dynamodb scan \
    --table-name clinical-results \
    --region ap-southeast-2 \
    --max-items 10
```

### SQS Queue
```bash
aws sqs get-queue-attributes \
    --queue-url https://sqs.ap-southeast-2.amazonaws.com/958175315966/clinical-processing-queue \
    --attribute-names ApproximateNumberOfMessages \
    --region ap-southeast-2
```

---

## Success Criteria

### ✅ Deployment Successful If:
- [ ] All API endpoints return 200 (or appropriate status)
- [ ] Can record and upload consultation
- [ ] Consultation appears in pending approvals
- [ ] Can approve consultation
- [ ] Tasks created after approval
- [ ] Patient history shows consultation
- [ ] Email notifications sent (if SES configured)
- [ ] No errors in Lambda logs

### ✅ Ready for Production If:
- [ ] All success criteria met
- [ ] SES email verified and working
- [ ] Frontend UI accessible and functional
- [ ] Tested with multiple consultations
- [ ] Tested with multiple patients
- [ ] Handover report generates correctly
- [ ] Consent tracking working
- [ ] Audit logs being created

---

## Next Steps After Successful Deployment

1. **Demo to stakeholders**
   - Show approval workflow
   - Demonstrate task management
   - Show patient history
   - Generate handover report

2. **Gather feedback**
   - UI improvements needed?
   - Additional features wanted?
   - Integration priorities?

3. **Apply for API access**
   - Medtech (2-4 weeks)
   - HealthLink (1-3 months)
   - Pharmacy systems (varies)

4. **Plan scaling**
   - Multi-clinic support
   - User authentication
   - Role-based access control
   - Analytics dashboard

---

## Support

If you encounter issues:
1. Check `SETUP_GUIDE.md` for detailed instructions
2. Review Lambda logs for errors
3. Verify all environment variables are set
4. Test each endpoint individually
5. Check AWS service quotas and limits

---

## Congratulations! 🎉

If all checkboxes are ticked, you have successfully deployed Clinical Recorder v2.0!

You now have a production-ready clinical workflow automation system.
