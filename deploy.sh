#!/bin/bash

# Clinical Recorder v2.0 - Deployment Script
# Deploys enhanced Lambda function with all new features

set -e

echo "========================================="
echo "Clinical Recorder v2.0 - Deployment"
echo "========================================="
echo ""

# Configuration
FUNCTION_NAME="clinical-recorder-api"
REGION="ap-southeast-2"
LAYER_NAME="clinical-recorder-deps"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Creating Lambda layer with dependencies...${NC}"
mkdir -p lambda_layer/python
pip install -t lambda_layer/python boto3 requests -q
cd lambda_layer
zip -r ../lambda_layer.zip . -q
cd ..
echo -e "${GREEN}✓ Layer created${NC}"

echo ""
echo -e "${YELLOW}Step 2: Publishing Lambda layer...${NC}"
LAYER_VERSION=$(aws lambda publish-layer-version \
    --layer-name $LAYER_NAME \
    --zip-file fileb://lambda_layer.zip \
    --compatible-runtimes python3.11 python3.12 \
    --region $REGION \
    --query 'Version' \
    --output text)
echo -e "${GREEN}✓ Layer published (version $LAYER_VERSION)${NC}"

echo ""
echo -e "${YELLOW}Step 3: Packaging Lambda function...${NC}"
zip -r lambda_function.zip \
    backend/ \
    config/ \
    storage/ \
    integrations/ \
    automation/ \
    shared/ \
    analysis/ \
    pdf/ \
    -x "*.pyc" -x "__pycache__/*" -q
echo -e "${GREEN}✓ Function packaged${NC}"

echo ""
echo -e "${YELLOW}Step 4: Updating Lambda function code...${NC}"
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://lambda_function.zip \
    --region $REGION \
    --no-cli-pager > /dev/null
echo -e "${GREEN}✓ Function code updated${NC}"

echo ""
echo -e "${YELLOW}Step 5: Attaching layer to function...${NC}"
LAYER_ARN=$(aws lambda list-layer-versions \
    --layer-name $LAYER_NAME \
    --region $REGION \
    --query "LayerVersions[0].LayerVersionArn" \
    --output text)

aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --layers $LAYER_ARN \
    --region $REGION \
    --no-cli-pager > /dev/null
echo -e "${GREEN}✓ Layer attached${NC}"

echo ""
echo -e "${YELLOW}Step 6: Setting environment variables...${NC}"
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment Variables="{
        INTEGRATIONS_ENABLED=false,
        ENABLE_EMAIL_NOTIFICATIONS=true,
        ENABLE_SMS_NOTIFICATIONS=false,
        AWS_REGION=$REGION,
        BUCKET_NAME=clinical-audio-bucket,
        TABLE_NAME=clinical-results,
        QUEUE_URL=https://sqs.$REGION.amazonaws.com/958175315966/clinical-processing-queue,
        SES_FROM_EMAIL=noreply@clinicalrecorder.com
    }" \
    --region $REGION \
    --no-cli-pager > /dev/null
echo -e "${GREEN}✓ Environment variables set${NC}"

echo ""
echo -e "${YELLOW}Step 7: Updating Lambda handler...${NC}"
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --handler backend.api_lambda_enhanced.handler \
    --region $REGION \
    --no-cli-pager > /dev/null
echo -e "${GREEN}✓ Handler updated${NC}"

echo ""
echo -e "${YELLOW}Step 8: Cleaning up...${NC}"
rm -rf lambda_layer lambda_layer.zip lambda_function.zip
echo -e "${GREEN}✓ Cleanup complete${NC}"

echo ""
echo "========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Verify SES email: aws ses verify-email-identity --email-address your@email.com"
echo "2. Test API: curl https://your-api-url/integration/status"
echo "3. Open frontend/dashboard.html in browser"
echo "4. See SETUP_GUIDE.md for full configuration"
echo ""
