#!/bin/bash

# Comprobar número de parámetros
if [ $# -ne 3 ]; then
    echo "❌ Número de parámetros incorrecto."
    echo "Uso:"
    echo "$0 <REGION_ORIGEN> <ID_INSTANCIA_ORIGEN> <REGION_DESTINO>"
    echo "Ejemplo:"
    echo "$0 eu-west-1 i-0123456789abcdef0 us-west-2"
    exit 1
fi

# Parámetros
ORIGIN_REGION=$1
INSTANCE_ID=$2
DEST_REGION=$3

KEY_NAME="mi-clave-$DEST_REGION"
KEY_FILE="$KEY_NAME.pem"

echo "🔍 Verificando instancia origen..."
aws ec2 describe-instances --instance-id $INSTANCE_ID --region $ORIGIN_REGION >/dev/null || { echo "❌ Instancia no encontrada."; exit 1; }
echo "✅ Instancia encontrada."

echo "📸 Creando AMI en origen..."
IMAGE_ID=$(aws ec2 create-image \
  --instance-id $INSTANCE_ID \
  --name "copia-automatica-ami" \
  --no-reboot \
  --region $ORIGIN_REGION \
  --query "ImageId" --output text)

aws ec2 wait image-available --image-id $IMAGE_ID --region $ORIGIN_REGION
echo "✅ AMI lista en origen: $IMAGE_ID"

echo "🚚 Copiando AMI a destino ($DEST_REGION)..."
COPIED_IMAGE_ID=$(aws ec2 copy-image \
  --source-image-id $IMAGE_ID \
  --source-region $ORIGIN_REGION \
  --region $DEST_REGION \
  --name "copia-automatica-ami-destino" \
  --query "ImageId" --output text)

aws ec2 wait image-available --image-id $COPIED_IMAGE_ID --region $DEST_REGION
echo "✅ AMI copiada: $COPIED_IMAGE_ID"

echo "🔎 Detectando VPC por defecto..."
DEFAULT_VPC_ID=$(aws ec2 describe-vpcs \
  --region $DEST_REGION \
  --filters "Name=isDefault,Values=true" \
  --query "Vpcs[0].VpcId" --output text)

echo "✅ VPC por defecto: $DEFAULT_VPC_ID"

echo "🔎 Detectando Subnet por defecto..."
SUBNET_ID=$(aws ec2 describe-subnets \
  --region $DEST_REGION \
  --filters "Name=vpc-id,Values=$DEFAULT_VPC_ID" "Name=default-for-az,Values=true" \
  --query "Subnets[0].SubnetId" --output text)

echo "✅ Subnet por defecto: $SUBNET_ID"

echo "🔎 Detectando Security Group por defecto..."
SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
  --region $DEST_REGION \
  --filters "Name=vpc-id,Values=$DEFAULT_VPC_ID" "Name=group-name,Values=default" \
  --query "SecurityGroups[0].GroupId" --output text)

echo "✅ Security Group por defecto: $SECURITY_GROUP_ID"

echo "🔐 Configurando Security Group para permitir SSH (22) desde cualquier lugar..."
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0 \
  --region $DEST_REGION >/dev/null 2>&1 || true

echo "✅ SSH abierto a 0.0.0.0/0"

echo "🔑 Creando clave SSH..."
aws ec2 create-key-pair \
  --key-name $KEY_NAME \
  --region $DEST_REGION \
  --query "KeyMaterial" --output text > $KEY_FILE

chmod 400 $KEY_FILE
echo "✅ Clave guardada en: $KEY_FILE"

echo "🚀 Lanzando instancia en destino..."
DEST_INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $COPIED_IMAGE_ID \
  --instance-type t2.micro \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SECURITY_GROUP_ID \
  --region $DEST_REGION \
  --query "Instances[0].InstanceId" --output text)

aws ec2 wait instance-running --instance-ids $DEST_INSTANCE_ID --region $DEST_REGION
echo "✅ Instancia destino activa: $DEST_INSTANCE_ID"

# 🟢 Obtener IP pública
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $DEST_INSTANCE_ID \
  --region $DEST_REGION \
  --query "Reservations[0].Instances[0].PublicIpAddress" --output text)

echo "🌍 IP pública de la instancia destino: $PUBLIC_IP"
echo "🔗 Conexión SSH:"
echo "ssh -i $KEY_FILE ec2-user@$PUBLIC_IP"

echo "🧹 Eliminando AMIs (manteniendo instancia destino funcionando)..."
aws ec2 deregister-image --image-id $COPIED_IMAGE_ID --region $DEST_REGION
aws ec2 deregister-image --image-id $IMAGE_ID --region $ORIGIN_REGION

echo "🎉 Proceso completado con éxito."
echo "✔ Instancia destino funcionando → $DEST_INSTANCE_ID"
echo "✔ Clave SSH guardada → $KEY_FILE"
echo "✔ IP pública: $PUBLIC_IP"
