#!/bin/bash

# Script para crear infraestructura multi-región AWS con Transit Gateway
# Regiones: us-east-1 y us-west-2
# Autor: AWS Infrastructure Automation

set -e

echo "=========================================="
echo "AWS Multi-Region Infrastructure Setup"
echo "Transit Gateway + VPC Peering"
echo "=========================================="

# Variables de configuración
REGION_EAST="us-east-1"
REGION_WEST="us-west-2"

# ==========================================
# PARTE 1: CONFIGURACIÓN US-EAST-1
# ==========================================

echo ""
echo "=== CONFIGURANDO REGIÓN US-EAST-1 ==="
echo ""

# Crear VPC 1 en US-EAST-1
echo "Creando VPC 1 en us-east-1 (10.1.0.0/16)..."
VPC1_EAST=$(aws ec2 create-vpc \
    --cidr-block 10.1.0.0/16 \
    --region $REGION_EAST \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=VPC-US-EAST-1-A}]' \
    --query 'Vpc.VpcId' \
    --output text)
echo "VPC 1 US-EAST-1 creada: $VPC1_EAST"

# Habilitar DNS en VPC 1
aws ec2 modify-vpc-attribute --vpc-id $VPC1_EAST --enable-dns-hostnames --region $REGION_EAST
aws ec2 modify-vpc-attribute --vpc-id $VPC1_EAST --enable-dns-support --region $REGION_EAST

# Crear VPC 2 en US-EAST-1
echo "Creando VPC 2 en us-east-1 (10.2.0.0/16)..."
VPC2_EAST=$(aws ec2 create-vpc \
    --cidr-block 10.2.0.0/16 \
    --region $REGION_EAST \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=VPC-US-EAST-1-B}]' \
    --query 'Vpc.VpcId' \
    --output text)
echo "VPC 2 US-EAST-1 creada: $VPC2_EAST"

aws ec2 modify-vpc-attribute --vpc-id $VPC2_EAST --enable-dns-hostnames --region $REGION_EAST
aws ec2 modify-vpc-attribute --vpc-id $VPC2_EAST --enable-dns-support --region $REGION_EAST

# Crear Subnets en US-EAST-1
echo "Creando subnets en us-east-1..."
SUBNET1_EAST=$(aws ec2 create-subnet \
    --vpc-id $VPC1_EAST \
    --cidr-block 10.1.0.0/24 \
    --availability-zone ${REGION_EAST}a \
    --region $REGION_EAST \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Subnet-Public-US-EAST-1-A}]' \
    --query 'Subnet.SubnetId' \
    --output text)
echo "Subnet 1 US-EAST-1: $SUBNET1_EAST"

SUBNET2_EAST=$(aws ec2 create-subnet \
    --vpc-id $VPC2_EAST \
    --cidr-block 10.2.0.0/24 \
    --availability-zone ${REGION_EAST}b \
    --region $REGION_EAST \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Subnet-Public-US-EAST-1-B}]' \
    --query 'Subnet.SubnetId' \
    --output text)
echo "Subnet 2 US-EAST-1: $SUBNET2_EAST"

# Auto-asignar IPs públicas
aws ec2 modify-subnet-attribute --subnet-id $SUBNET1_EAST --map-public-ip-on-launch --region $REGION_EAST
aws ec2 modify-subnet-attribute --subnet-id $SUBNET2_EAST --map-public-ip-on-launch --region $REGION_EAST

# Crear Internet Gateways en US-EAST-1
echo "Creando Internet Gateways en us-east-1..."
IGW1_EAST=$(aws ec2 create-internet-gateway \
    --region $REGION_EAST \
    --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=IGW-US-EAST-1-A}]' \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)
aws ec2 attach-internet-gateway --vpc-id $VPC1_EAST --internet-gateway-id $IGW1_EAST --region $REGION_EAST
echo "IGW 1: $IGW1_EAST"

IGW2_EAST=$(aws ec2 create-internet-gateway \
    --region $REGION_EAST \
    --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=IGW-US-EAST-1-B}]' \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)
aws ec2 attach-internet-gateway --vpc-id $VPC2_EAST --internet-gateway-id $IGW2_EAST --region $REGION_EAST
echo "IGW 2: $IGW2_EAST"

# Crear Transit Gateway en US-EAST-1
echo "Creando Transit Gateway en us-east-1..."
TGW_EAST=$(aws ec2 create-transit-gateway \
    --description "Transit Gateway US-EAST-1" \
    --options "AmazonSideAsn=64512,DefaultRouteTableAssociation=enable,DefaultRouteTablePropagation=enable,DnsSupport=enable,VpnEcmpSupport=enable" \
    --region $REGION_EAST \
    --tag-specifications 'ResourceType=transit-gateway,Tags=[{Key=Name,Value=TGW-US-EAST-1}]' \
    --query 'TransitGateway.TransitGatewayId' \
    --output text)
echo "Transit Gateway US-EAST-1: $TGW_EAST"

echo "Esperando a que el Transit Gateway esté disponible (2 minutos)..."
sleep 120
echo "Transit Gateway disponible!"

# Crear Transit Gateway Attachments en US-EAST-1
echo "Creando Transit Gateway Attachments en us-east-1..."
TGW_ATTACH1_EAST=$(aws ec2 create-transit-gateway-vpc-attachment \
    --transit-gateway-id $TGW_EAST \
    --vpc-id $VPC1_EAST \
    --subnet-ids $SUBNET1_EAST \
    --region $REGION_EAST \
    --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=TGW-Attach-VPC-US-EAST-1-A}]' \
    --query 'TransitGatewayVpcAttachment.TransitGatewayAttachmentId' \
    --output text)
echo "TGW Attachment 1: $TGW_ATTACH1_EAST"

TGW_ATTACH2_EAST=$(aws ec2 create-transit-gateway-vpc-attachment \
    --transit-gateway-id $TGW_EAST \
    --vpc-id $VPC2_EAST \
    --subnet-ids $SUBNET2_EAST \
    --region $REGION_EAST \
    --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=TGW-Attach-VPC-US-EAST-1-B}]' \
    --query 'TransitGatewayVpcAttachment.TransitGatewayAttachmentId' \
    --output text)
echo "TGW Attachment 2: $TGW_ATTACH2_EAST"

sleep 30

# ==========================================
# PARTE 2: CONFIGURACIÓN US-WEST-2
# ==========================================

echo ""
echo "=== CONFIGURANDO REGIÓN US-WEST-2 ==="
echo ""

# Crear VPC 1 en US-WEST-2
echo "Creando VPC 1 en us-west-2 (192.168.0.0/16)..."
VPC1_WEST=$(aws ec2 create-vpc \
    --cidr-block 192.168.0.0/16 \
    --region $REGION_WEST \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=VPC-US-WEST-2-A}]' \
    --query 'Vpc.VpcId' \
    --output text)
echo "VPC 1 US-WEST-2 creada: $VPC1_WEST"

aws ec2 modify-vpc-attribute --vpc-id $VPC1_WEST --enable-dns-hostnames --region $REGION_WEST
aws ec2 modify-vpc-attribute --vpc-id $VPC1_WEST --enable-dns-support --region $REGION_WEST

# Crear VPC 2 en US-WEST-2
echo "Creando VPC 2 en us-west-2 (192.224.0.0/16)..."
VPC2_WEST=$(aws ec2 create-vpc \
    --cidr-block 192.224.0.0/16 \
    --region $REGION_WEST \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=VPC-US-WEST-2-B}]' \
    --query 'Vpc.VpcId' \
    --output text)
echo "VPC 2 US-WEST-2 creada: $VPC2_WEST"

aws ec2 modify-vpc-attribute --vpc-id $VPC2_WEST --enable-dns-hostnames --region $REGION_WEST
aws ec2 modify-vpc-attribute --vpc-id $VPC2_WEST --enable-dns-support --region $REGION_WEST

# Crear Subnets en US-WEST-2
echo "Creando subnets en us-west-2..."
SUBNET1_WEST=$(aws ec2 create-subnet \
    --vpc-id $VPC1_WEST \
    --cidr-block 192.168.1.0/24 \
    --availability-zone ${REGION_WEST}a \
    --region $REGION_WEST \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Subnet-Public-US-WEST-2-A}]' \
    --query 'Subnet.SubnetId' \
    --output text)
echo "Subnet 1 US-WEST-2: $SUBNET1_WEST"

SUBNET2_WEST=$(aws ec2 create-subnet \
    --vpc-id $VPC2_WEST \
    --cidr-block 192.224.1.0/24 \
    --availability-zone ${REGION_WEST}b \
    --region $REGION_WEST \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Subnet-Public-US-WEST-2-B}]' \
    --query 'Subnet.SubnetId' \
    --output text)
echo "Subnet 2 US-WEST-2: $SUBNET2_WEST"

aws ec2 modify-subnet-attribute --subnet-id $SUBNET1_WEST --map-public-ip-on-launch --region $REGION_WEST
aws ec2 modify-subnet-attribute --subnet-id $SUBNET2_WEST --map-public-ip-on-launch --region $REGION_WEST

# Crear Internet Gateways en US-WEST-2
echo "Creando Internet Gateways en us-west-2..."
IGW1_WEST=$(aws ec2 create-internet-gateway \
    --region $REGION_WEST \
    --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=IGW-US-WEST-2-A}]' \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)
aws ec2 attach-internet-gateway --vpc-id $VPC1_WEST --internet-gateway-id $IGW1_WEST --region $REGION_WEST
echo "IGW 1: $IGW1_WEST"

IGW2_WEST=$(aws ec2 create-internet-gateway \
    --region $REGION_WEST \
    --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=IGW-US-WEST-2-B}]' \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)
aws ec2 attach-internet-gateway --vpc-id $VPC2_WEST --internet-gateway-id $IGW2_WEST --region $REGION_WEST
echo "IGW 2: $IGW2_WEST"

# Crear Transit Gateway en US-WEST-2
echo "Creando Transit Gateway en us-west-2..."
TGW_WEST=$(aws ec2 create-transit-gateway \
    --description "Transit Gateway US-WEST-2" \
    --options "AmazonSideAsn=64513,DefaultRouteTableAssociation=enable,DefaultRouteTablePropagation=enable,DnsSupport=enable,VpnEcmpSupport=enable" \
    --region $REGION_WEST \
    --tag-specifications 'ResourceType=transit-gateway,Tags=[{Key=Name,Value=TGW-US-WEST-2}]' \
    --query 'TransitGateway.TransitGatewayId' \
    --output text)
echo "Transit Gateway US-WEST-2: $TGW_WEST"

echo "Esperando a que el Transit Gateway esté disponible (2 minutos)..."
sleep 120
echo "Transit Gateway disponible!"

# Crear Transit Gateway Attachments en US-WEST-2
echo "Creando Transit Gateway Attachments en us-west-2..."
TGW_ATTACH1_WEST=$(aws ec2 create-transit-gateway-vpc-attachment \
    --transit-gateway-id $TGW_WEST \
    --vpc-id $VPC1_WEST \
    --subnet-ids $SUBNET1_WEST \
    --region $REGION_WEST \
    --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=TGW-Attach-VPC-US-WEST-2-A}]' \
    --query 'TransitGatewayVpcAttachment.TransitGatewayAttachmentId' \
    --output text)
echo "TGW Attachment 1: $TGW_ATTACH1_WEST"

TGW_ATTACH2_WEST=$(aws ec2 create-transit-gateway-vpc-attachment \
    --transit-gateway-id $TGW_WEST \
    --vpc-id $VPC2_WEST \
    --subnet-ids $SUBNET2_WEST \
    --region $REGION_WEST \
    --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=TGW-Attach-VPC-US-WEST-2-B}]' \
    --query 'TransitGatewayVpcAttachment.TransitGatewayAttachmentId' \
    --output text)
echo "TGW Attachment 2: $TGW_ATTACH2_WEST"

sleep 30

# ==========================================
# PARTE 3: TRANSIT GATEWAY PEERING
# ==========================================

echo ""
echo "=== CREANDO TRANSIT GATEWAY PEERING ==="
echo ""

# Obtener Account ID automáticamente
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"

# Crear Peering Request desde US-EAST-1 hacia US-WEST-2
echo "Creando Transit Gateway Peering Request..."
PEERING_ID=$(aws ec2 create-transit-gateway-peering-attachment \
    --transit-gateway-id $TGW_EAST \
    --peer-transit-gateway-id $TGW_WEST \
    --peer-account-id $ACCOUNT_ID \
    --peer-region $REGION_WEST \
    --region $REGION_EAST \
    --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=TGW-Peering-EAST-WEST}]' \
    --query 'TransitGatewayPeeringAttachment.TransitGatewayAttachmentId' \
    --output text)
echo "Peering ID: $PEERING_ID"

echo "Esperando a que el peering esté pendiente de aceptación..."
sleep 120

# Aceptar Peering desde US-WEST-2
echo "Aceptando Transit Gateway Peering desde us-west-2..."
aws ec2 accept-transit-gateway-peering-attachment \
    --transit-gateway-attachment-id $PEERING_ID \
    --region $REGION_WEST

echo "Esperando a que el peering esté disponible (3 minutos)..."
sleep 200

# ==========================================
# PARTE 4: CONFIGURAR ROUTE TABLES
# ==========================================

echo ""
echo "=== CONFIGURANDO ROUTE TABLES ==="
echo ""

# Obtener Route Tables
RT1_EAST=$(aws ec2 describe-route-tables --region $REGION_EAST --filters "Name=vpc-id,Values=$VPC1_EAST" --query 'RouteTables[0].RouteTableId' --output text)
RT2_EAST=$(aws ec2 describe-route-tables --region $REGION_EAST --filters "Name=vpc-id,Values=$VPC2_EAST" --query 'RouteTables[0].RouteTableId' --output text)
RT1_WEST=$(aws ec2 describe-route-tables --region $REGION_WEST --filters "Name=vpc-id,Values=$VPC1_WEST" --query 'RouteTables[0].RouteTableId' --output text)
RT2_WEST=$(aws ec2 describe-route-tables --region $REGION_WEST --filters "Name=vpc-id,Values=$VPC2_WEST" --query 'RouteTables[0].RouteTableId' --output text)

# Routes para US-EAST-1 VPC 1
echo "Configurando rutas para VPC1 US-EAST-1..."
aws ec2 create-route --route-table-id $RT1_EAST --destination-cidr-block 10.2.0.0/16 --transit-gateway-id $TGW_EAST --region $REGION_EAST
aws ec2 create-route --route-table-id $RT1_EAST --destination-cidr-block 192.168.0.0/16 --transit-gateway-id $TGW_EAST --region $REGION_EAST
aws ec2 create-route --route-table-id $RT1_EAST --destination-cidr-block 192.224.0.0/16 --transit-gateway-id $TGW_EAST --region $REGION_EAST
aws ec2 create-route --route-table-id $RT1_EAST --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW1_EAST --region $REGION_EAST

# Routes para US-EAST-1 VPC 2
echo "Configurando rutas para VPC2 US-EAST-1..."
aws ec2 create-route --route-table-id $RT2_EAST --destination-cidr-block 10.1.0.0/16 --transit-gateway-id $TGW_EAST --region $REGION_EAST
aws ec2 create-route --route-table-id $RT2_EAST --destination-cidr-block 192.168.0.0/16 --transit-gateway-id $TGW_EAST --region $REGION_EAST
aws ec2 create-route --route-table-id $RT2_EAST --destination-cidr-block 192.224.0.0/16 --transit-gateway-id $TGW_EAST --region $REGION_EAST
aws ec2 create-route --route-table-id $RT2_EAST --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW2_EAST --region $REGION_EAST

# Routes para US-WEST-2 VPC 1
echo "Configurando rutas para VPC1 US-WEST-2..."
aws ec2 create-route --route-table-id $RT1_WEST --destination-cidr-block 192.224.0.0/16 --transit-gateway-id $TGW_WEST --region $REGION_WEST
aws ec2 create-route --route-table-id $RT1_WEST --destination-cidr-block 10.0.0.0/8 --transit-gateway-id $TGW_WEST --region $REGION_WEST
aws ec2 create-route --route-table-id $RT1_WEST --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW1_WEST --region $REGION_WEST

# Routes para US-WEST-2 VPC 2
echo "Configurando rutas para VPC2 US-WEST-2..."
aws ec2 create-route --route-table-id $RT2_WEST --destination-cidr-block 192.168.0.0/16 --transit-gateway-id $TGW_WEST --region $REGION_WEST
aws ec2 create-route --route-table-id $RT2_WEST --destination-cidr-block 10.0.0.0/8 --transit-gateway-id $TGW_WEST --region $REGION_WEST
aws ec2 create-route --route-table-id $RT2_WEST --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW2_WEST --region $REGION_WEST

# Obtener Transit Gateway Route Tables
TGW_RT_EAST=$(aws ec2 describe-transit-gateway-route-tables --region $REGION_EAST --filters "Name=transit-gateway-id,Values=$TGW_EAST" --query 'TransitGatewayRouteTables[0].TransitGatewayRouteTableId' --output text)
TGW_RT_WEST=$(aws ec2 describe-transit-gateway-route-tables --region $REGION_WEST --filters "Name=transit-gateway-id,Values=$TGW_WEST" --query 'TransitGatewayRouteTables[0].TransitGatewayRouteTableId' --output text)

# Rutas en Transit Gateway US-EAST-1
echo "Configurando rutas en Transit Gateway US-EAST-1..."
aws ec2 create-transit-gateway-route \
    --destination-cidr-block 192.168.0.0/16 \
    --transit-gateway-route-table-id $TGW_RT_EAST \
    --transit-gateway-attachment-id $PEERING_ID \
    --region $REGION_EAST

aws ec2 create-transit-gateway-route \
    --destination-cidr-block 192.224.0.0/16 \
    --transit-gateway-route-table-id $TGW_RT_EAST \
    --transit-gateway-attachment-id $PEERING_ID \
    --region $REGION_EAST

# Rutas en Transit Gateway US-WEST-2
echo "Configurando rutas en Transit Gateway US-WEST-2..."
aws ec2 create-transit-gateway-route \
    --destination-cidr-block 10.0.0.0/8 \
    --transit-gateway-route-table-id $TGW_RT_WEST \
    --transit-gateway-attachment-id $PEERING_ID \
    --region $REGION_WEST

# Asociar y propagar peering en ambos Transit Gateways
echo "Asociando peering connection en Transit Gateways..."

# Asociar peering en US-EAST-1
aws ec2 associate-transit-gateway-route-table \
    --transit-gateway-attachment-id $PEERING_ID \
    --transit-gateway-route-table-id $TGW_RT_EAST \
    --region $REGION_EAST

# Propagar rutas del peering en US-EAST-1
aws ec2 enable-transit-gateway-route-table-propagation \
    --transit-gateway-attachment-id $PEERING_ID \
    --transit-gateway-route-table-id $TGW_RT_EAST \
    --region $REGION_EAST

# Asociar peering en US-WEST-2
aws ec2 associate-transit-gateway-route-table \
    --transit-gateway-attachment-id $PEERING_ID \
    --transit-gateway-route-table-id $TGW_RT_WEST \
    --region $REGION_WEST

# Propagar rutas del peering en US-WEST-2
aws ec2 enable-transit-gateway-route-table-propagation \
    --transit-gateway-attachment-id $PEERING_ID \
    --transit-gateway-route-table-id $TGW_RT_WEST \
    --region $REGION_WEST

# ==========================================
# RESUMEN DE LA INFRAESTRUCTURA
# ==========================================

echo ""
echo "=========================================="
echo "INFRAESTRUCTURA COMPLETADA EXITOSAMENTE"
echo "=========================================="
echo ""
echo "US-EAST-1 (Norte de Virginia):"
echo "  VPC 1: $VPC1_EAST (10.1.0.0/16)"
echo "    Subnet: $SUBNET1_EAST"
echo "  VPC 2: $VPC2_EAST (10.2.0.0/16)"
echo "    Subnet: $SUBNET2_EAST"
echo "  Transit Gateway: $TGW_EAST"
echo ""
echo "US-WEST-2 (Oregón):"
echo "  VPC 1: $VPC1_WEST (192.168.0.0/16)"
echo "    Subnet: $SUBNET1_WEST (192.168.1.0/24)"
echo "  VPC 2: $VPC2_WEST (192.224.0.0/16)"
echo "    Subnet: $SUBNET2_WEST (192.224.1.0/24)"
echo "  Transit Gateway: $TGW_WEST"
echo ""
echo "Transit Gateway Peering: $PEERING_ID"
echo ""
echo "=========================================="
echo "PRÓXIMOS PASOS:"
echo "=========================================="
echo "1. Infraestructura de red lista para desplegar instancias"
echo "2. Verifica las tablas de rutas en la consola de AWS"
echo "3. Verifica los Transit Gateways y el Peering Connection"
echo ""
echo "Comandos para verificar:"
echo "  aws ec2 describe-route-tables --route-table-ids $RT1_EAST --region $REGION_EAST"
echo "  aws ec2 describe-transit-gateways --transit-gateway-ids $TGW_EAST --region $REGION_EAST"
echo "  aws ec2 describe-transit-gateway-peering-attachments --transit-gateway-attachment-ids $PEERING_ID --region $REGION_EAST"
echo ""
echo "=========================================="