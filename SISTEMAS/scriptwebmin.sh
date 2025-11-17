#!/bin/bash
INSTANCE_TYPE="t3.micro"
KEY_NAME="vockey"
REGION="us-east-1"
IAM_INSTANCE_PROFILE="LabInstanceProfile"
USERDATA_FILE="instalarwebmin.txt"
SECURITY_GROUP_NAME="grupowebmin"

SG_ID=$(aws ec2 create-security-group \
    --group-name "$SECURITY_GROUP_NAME" \
    --description "Webmin SSH y puerto 10000" \
    --region "$REGION" \
    --query 'GroupId' \
    --output text)

echo "Security Group creado: $SG_ID"

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp --port 22 --cidr 0.0.0.0/0 \
    --region $REGION

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp --port 10000 --cidr 0.0.0.0/0 \
    --region $REGION

aws ec2 run-instances \
    --image-id ami-0ecb62995f68bb549 \
    --count 1 \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ec2webminsh2}]' \
    --iam-instance-profile Name=$IAM_INSTANCE_PROFILE \
    --user-data file://$USERDATA_FILE \
    --region $REGION

echo "Instancia lanzada. Comprueba la IP pública en la consola de AWS y accede a Webmin en https://<IP>:10000"
