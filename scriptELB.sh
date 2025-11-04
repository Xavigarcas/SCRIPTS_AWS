# Variables
REGION="us-east-1"
VPC_ID="vpc-03b449a57aac9c174"
SUBNET_ID="subnet-0d0d3093c5ec3d476"
INSTANCIA_1="i-0f13b05c8ecb6d72f"
INSTANCIA_2="i-0d35cd5f0de153e8c"

echo "Creando grupo de seguridad..."
SG_ID=$(aws ec2 create-security-group \
  --group-name servidorweb \
  --description "Acceso HTTP, HTTPS y SSH" \
  --vpc-id $VPC_ID \
  --region  $REGION \
  --query 'GroupId' \
  --output text)

echo "Grupo de seguridad creado: $SG_ID"

# Permitimos el HTTP 
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region $REGION

# Permitimos el HTTPS
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0 \
  --region $REGION

# Permitimos el SSH
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0 \
  --region $REGION

echo "Reglas aplicadas correctamente."
echo "SG_ID: $SG_ID"





echo "Creando Network Load Balancer (NLB)..."

# Creamos el Balanceador
NLB_PRUEBA=$(aws elbv2 create-load-balancer \
  --name nlb-xavi \
  --type network \
  --scheme internet-facing \
  --subnets $SUBNET_ID \
  --region $REGION \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

echo "NLB creado: $NLB_ARN"

# Creamos el target group
TG_PRUEBA=$(aws elbv2 create-target-group \
  --name tg-xavi \
  --protocol TCP \
  --port 80 \
  --vpc-id $VPC_ID \
  --target-type instance \
  --region $REGION \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

echo "Target Group creado: $TG_PRUEBA"

# Registramos las instancias en el target group
aws elbv2 register-targets \
  --target-group-arn $TG_PRUEBA \
  --targets Id=$INSTANCIA_1 Id=$INSTANCIA_2 \
  --region $REGION

echo "Instancias registradas en el Target Group."

# Creamos el listener
aws elbv2 create-listener \
  --load-balancer-arn $NLB_PRUEBA \
  --protocol TCP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_PRUEBA \
  --region $REGION

echo "Listener creado. El balanceador ya está activo."

# Mostramos DNS del balanceador
DNS_NAME=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $NLB_PRUEBA \
  --region $REGION \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

echo "DNS del balanceador: $DNS_NAME"
