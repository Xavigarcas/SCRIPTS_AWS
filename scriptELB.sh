#!/bin/bash
# =====================================================
# Script: crear_todo_balanceador.sh
# Autor: ChatGPT
# Descripción: Crea toda la infraestructura para un
#              Network Load Balancer con 2 instancias EC2
# =====================================================

set -e  # Detiene el script si algo falla

# ----------- CONFIGURACIÓN -------------
REGION="us-east-1"
AZ="us-east-1b"
CIDR_VPC="10.0.0.0/16"
CIDR_SUBNET="10.0.1.0/24"
AMI_ID="ami-0c02fb55956c7d316"  # Amazon Linux 2 (us-east-1)
INSTANCE_TYPE="t2.micro"
KEY_NAME="mi-clave-ec2"  # Debes tener una clave creada con este nombre
PORT=80
PROTOCOL="TCP"
TARGET_GROUP_NAME="tg-cli"
LOAD_BALANCER_NAME="balanceador-por-cli"
# ======================================

echo "✅ Creando VPC..."
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block $CIDR_VPC \
  --region $REGION \
  --query 'Vpc.VpcId' \
  --output text)

aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support "{\"Value\":true}" --region $REGION
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames "{\"Value\":true}" --region $REGION
echo "➡️ VPC creada: $VPC_ID"

echo "✅ Creando Subred pública..."
SUBNET_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block $CIDR_SUBNET \
  --availability-zone $AZ \
  --region $REGION \
  --query 'Subnet.SubnetId' \
  --output text)
echo "➡️ Subred creada: $SUBNET_ID"

echo "✅ Creando Internet Gateway..."
IGW_ID=$(aws ec2 create-internet-gateway \
  --region $REGION \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID --region $REGION
echo "➡️ IGW creado y asociado: $IGW_ID"

echo "✅ Creando tabla de rutas..."
RT_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --region $REGION \
  --query 'RouteTable.RouteTableId' \
  --output text)
aws ec2 create-route \
  --route-table-id $RT_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID \
  --region $REGION
aws ec2 associate-route-table --subnet-id $SUBNET_ID --route-table-id $RT_ID --region $REGION
echo "➡️ Tabla de rutas creada: $RT_ID"

echo "✅ Creando grupo de seguridad..."
SG_ID=$(aws ec2 create-security-group \
  --group-name sg-http-80 \
  --description "Permitir tráfico HTTP" \
  --vpc-id $VPC_ID \
  --region $REGION \
  --query 'GroupId' \
  --output text)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region $REGION
echo "➡️ Grupo de seguridad creado: $SG_ID"

echo "✅ Lanzando instancias EC2..."
USER_DATA="#!/bin/bash
yum install -y httpd
echo '<h1>Servidor \$(hostname)</h1>' > /var/www/html/index.html
systemctl enable httpd
systemctl start httpd"

INSTANCE_1=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --count 1 \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --security-group-ids $SG_ID \
  --subnet-id $SUBNET_ID \
  --user-data "$USER_DATA" \
  --region $REGION \
  --query 'Instances[0].InstanceId' \
  --output text)

INSTANCE_2=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --count 1 \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --security-group-ids $SG_ID \
  --subnet-id $SUBNET_ID \
  --user-data "$USER_DATA" \
  --region $REGION \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "➡️ Instancias lanzadas: $INSTANCE_1 , $INSTANCE_2"

echo "🕐 Esperando a que las instancias estén disponibles..."
aws ec2 wait instance-running --instance-ids $INSTANCE_1 $INSTANCE_2 --region $REGION
echo "✅ Instancias activas."

echo "✅ Creando Target Group..."
TG_ARN=$(aws elbv2 create-target-group \
  --name $TARGET_GROUP_NAME \
  --protocol $PROTOCOL \
  --port $PORT \
  --vpc-id $VPC_ID \
  --target-type instance \
  --region $REGION \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)
echo "➡️ Target Group creado: $TG_ARN"

echo "✅ Registrando instancias..."
aws elbv2 register-targets \
  --target-group-arn $TG_ARN \
  --targets Id=$INSTANCE_1 Id=$INSTANCE_2 \
  --region $REGION

echo "✅ Creando Network Load Balancer..."
LB_ARN=$(aws elbv2 create-load-balancer \
  --name "$LOAD_BALANCER_NAME" \
  --type network \
  --subnets $SUBNET_ID \
  --region $REGION \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)
echo "➡️ Load Balancer creado: $LB_ARN"

echo "✅ Creando Listener..."
aws elbv2 create-listener \
  --load-balancer-arn $LB_ARN \
  --protocol $PROTOCOL \
  --port $PORT \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN \
  --region $REGION
echo "✅ Listener creado correctamente."

LB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $LB_ARN \
  --query 'LoadBalancers[0].DNSName' \
  --output text \
  --region $REGION)

echo "--------------------------------------------------"
echo "✅ TODO CREADO CORRECTAMENTE"
echo "VPC ID:           $VPC_ID"
echo "Subred ID:        $SUBNET_ID"
echo "Security Group:   $SG_ID"
echo "Instancias:       $INSTANCE_1 , $INSTANCE_2"
echo "Target Group ARN: $TG_ARN"
echo "Load Balancer:    $LB_ARN"
echo "URL:              http://$LB_DNS"
echo "--------------------------------------------------"
