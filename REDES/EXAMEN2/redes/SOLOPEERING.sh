#!/bin/bash

# IDs de las VPCs existentes (reemplaza con tus IDs reales)
VPC1="vpc-xxxxxxxxx"  # VPC en us-east-1
VPC2="vpc-yyyyyyyyy"  # VPC en us-west-2

# Crear peering
PEER=$(aws ec2 create-vpc-peering-connection --vpc-id $VPC1 --peer-vpc-id $VPC2 --peer-region us-west-2 --region us-east-1 --query 'VpcPeeringConnection.VpcPeeringConnectionId' --output text)

# Aceptar peering
aws ec2 accept-vpc-peering-connection --vpc-peering-connection-id $PEER --region us-west-2

# Obtener route tables
RT1=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC1" --region us-east-1 --query 'RouteTables[0].RouteTableId' --output text)
RT2=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC2" --region us-west-2 --query 'RouteTables[0].RouteTableId' --output text)

# Crear rutas (ajusta los CIDR blocks según tus VPCs)
aws ec2 create-route --route-table-id $RT1 --destination-cidr-block 10.0.0.0/20 --vpc-peering-connection-id $PEER --region us-east-1
aws ec2 create-route --route-table-id $RT2 --destination-cidr-block 192.168.0.0/20 --vpc-peering-connection-id $PEER --region us-west-2

echo "Peering creado: $PEER"
