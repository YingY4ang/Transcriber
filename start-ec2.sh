#!/bin/bash
INSTANCE_ID="i-0069540f657963c71"
REGION="ap-southeast-2"

echo "Starting EC2 instance..."
aws ec2 start-instances --instance-ids $INSTANCE_ID --region $REGION

echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

echo "Waiting for instance to be ready..."
sleep 30

PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $REGION --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "Instance IP: $PUBLIC_IP"

echo "Starting Docker containers..."
ssh -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "docker start clinical-api clinical-recorder"

echo "Done! API available at http://$PUBLIC_IP:5000"
