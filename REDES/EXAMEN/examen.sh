#!/bin/bash

# ========== CREACIÓN DE VPC ==========
echo "Creando VPC con CIDR 10.10.0.0/16..."
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.10.0.0/16 \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=VPC-Examen}]' \
    --query Vpc.VpcId --output text)
echo "VPC creada: $VPC_ID"

# ========== CREACIÓN DE SUBREDES ==========
echo "Creando subredes públicas y privadas en 2 AZs..."

# Subred pública 1 (AZ us-east-1a)
PUB_SUBNET_1_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.10.1.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Publica-1-AZ-a}]' \
    --query 'Subnet.SubnetId' \
    --output text)

# Subred pública 2 (AZ us-east-1b)
PUB_SUBNET_2_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.10.2.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Publica-2-AZ-b}]' \
    --query 'Subnet.SubnetId' \
    --output text)

# Subred privada 1 (AZ us-east-1a)
PRIV_SUBNET_1_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.10.3.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Privada-1-AZ-a}]' \
    --query 'Subnet.SubnetId' \
    --output text)

# Subred privada 2 (AZ us-east-1b)
PRIV_SUBNET_2_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.10.4.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Privada-2-AZ-b}]' \
    --query 'Subnet.SubnetId' \
    --output text)

echo "Subredes creadas:"
echo "  Públicas: $PUB_SUBNET_1_ID, $PUB_SUBNET_2_ID"
echo "  Privadas: $PRIV_SUBNET_1_ID, $PRIV_SUBNET_2_ID"

# ========== INTERNET GATEWAY ==========
echo "Creando y asociando Internet Gateway..."
IGW_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=IGW-Examen}]' \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)

aws ec2 attach-internet-gateway \
    --internet-gateway-id $IGW_ID \
    --vpc-id $VPC_ID
echo "Internet Gateway creado: $IGW_ID"

# ========== NAT GATEWAY ==========
echo "Creando NAT Gateway en subred pública 1..."
EIP_ALLOC_ID=$(aws ec2 allocate-address \
    --domain vpc \
    --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=EIP-NAT}]' \
    --query 'AllocationId' \
    --output text)

NAT_GW_ID=$(aws ec2 create-nat-gateway \
    --subnet-id $PUB_SUBNET_1_ID \
    --allocation-id $EIP_ALLOC_ID \
    --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=NAT-Gateway}]' \
    --query 'NatGateway.NatGatewayId' \
    --output text)

echo "NAT Gateway creado: $NAT_GW_ID (esperando disponibilidad...)"
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_ID
echo "NAT Gateway disponible"

# ========== TABLAS DE RUTAS ==========
echo "Creando tablas de rutas..."

# Tabla de rutas pública 1
RT_PUB_1_ID=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=RT-Publica-1}]' \
    --query 'RouteTable.RouteTableId' \
    --output text)

# Tabla de rutas pública 2
RT_PUB_2_ID=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=RT-Publica-2}]' \
    --query 'RouteTable.RouteTableId' \
    --output text)

# Tabla de rutas privada 1
RT_PRIV_1_ID=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=RT-Privada-1}]' \
    --query 'RouteTable.RouteTableId' \
    --output text)

# Tabla de rutas privada 2
RT_PRIV_2_ID=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=RT-Privada-2}]' \
    --query 'RouteTable.RouteTableId' \
    --output text)

echo "Tablas de rutas creadas"

# ========== CONFIGURACIÓN DE RUTAS ==========
echo "Configurando rutas..."

# Rutas públicas (hacia Internet Gateway)
aws ec2 create-route --route-table-id $RT_PUB_1_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
aws ec2 create-route --route-table-id $RT_PUB_2_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID

# Rutas privadas (hacia NAT Gateway)
aws ec2 create-route --route-table-id $RT_PRIV_1_ID --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_ID
aws ec2 create-route --route-table-id $RT_PRIV_2_ID --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_ID

# ========== ASOCIACIÓN DE TABLAS DE RUTAS ==========
echo "Asociando tablas de rutas con subredes..."
aws ec2 associate-route-table --subnet-id $PUB_SUBNET_1_ID --route-table-id $RT_PUB_1_ID
aws ec2 associate-route-table --subnet-id $PUB_SUBNET_2_ID --route-table-id $RT_PUB_2_ID
aws ec2 associate-route-table --subnet-id $PRIV_SUBNET_1_ID --route-table-id $RT_PRIV_1_ID
aws ec2 associate-route-table --subnet-id $PRIV_SUBNET_2_ID --route-table-id $RT_PRIV_2_ID

# Habilitar IP pública automática en subredes públicas
aws ec2 modify-subnet-attribute --subnet-id $PUB_SUBNET_1_ID --map-public-ip-on-launch
aws ec2 modify-subnet-attribute --subnet-id $PUB_SUBNET_2_ID --map-public-ip-on-launch

# ========== GRUPOS DE SEGURIDAD ENCADENADOS ==========
echo "Creando grupos de seguridad encadenados..."

# Security Group para instancias públicas (Bastion)
SG_PUBLIC_ID=$(aws ec2 create-security-group \
    --group-name SG-Public-Bastion \
    --description "Permite SSH desde Internet" \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=SG-Public}]' \
    --query 'GroupId' \
    --output text)

# Regla SSH desde Internet para bastion
aws ec2 authorize-security-group-ingress \
    --group-id $SG_PUBLIC_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

# Security Group para instancias privadas
SG_PRIVATE_ID=$(aws ec2 create-security-group \
    --group-name SG-Private-Backend \
    --description "Permite acceso solo desde subredes publicas" \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=SG-Private}]' \
    --query 'GroupId' \
    --output text)

# Regla SSH solo desde Security Group público (encadenamiento)
aws ec2 authorize-security-group-ingress \
    --group-id $SG_PRIVATE_ID \
    --protocol tcp \
    --port 22 \
    --source-group $SG_PUBLIC_ID

# Regla ICMP solo desde Security Group público
aws ec2 authorize-security-group-ingress \
    --group-id $SG_PRIVATE_ID \
    --protocol icmp \
    --port -1 \
    --source-group $SG_PUBLIC_ID

echo "Security Groups creados con encadenamiento:"
echo "  Público: $SG_PUBLIC_ID (SSH desde Internet)"
echo "  Privado: $SG_PRIVATE_ID (SSH/ICMP solo desde SG público)"

# ========== RESUMEN ==========
echo "VPC ID:                $VPC_ID"
echo "Internet Gateway:      $IGW_ID"
echo "NAT Gateway:           $NAT_GW_ID"
echo ""
echo "SUBREDES:"
echo "  Pública 1 (AZ-a):    $PUB_SUBNET_1_ID"
echo "  Pública 2 (AZ-b):    $PUB_SUBNET_2_ID"
echo "  Privada 1 (AZ-a):    $PRIV_SUBNET_1_ID"
echo "  Privada 2 (AZ-b):    $PRIV_SUBNET_2_ID"
echo ""
echo "TABLAS DE RUTAS:"
echo "  RT Pública 1:         $RT_PUB_1_ID"
echo "  RT Pública 2:         $RT_PUB_2_ID"
echo "  RT Privada 1:         $RT_PRIV_1_ID"
echo "  RT Privada 2:         $RT_PRIV_2_ID"
echo ""
echo "SECURITY GROUPS:"
echo "  SG Público:           $SG_PUBLIC_ID"
echo "  SG Privado:           $SG_PRIVATE_ID"
echo "=========================================="
echo "Arquitectura multi-AZ con encadenamiento de SG completada"