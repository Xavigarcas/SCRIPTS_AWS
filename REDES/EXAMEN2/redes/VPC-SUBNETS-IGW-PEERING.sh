#!/bin/bash

# Crear VPCs
VPC1=$(aws ec2 create-vpc --cidr-block 192.168.0.0/20 --region us-east-1 --query 'Vpc.VpcId' --output text)
VPC2=$(aws ec2 create-vpc --cidr-block 10.0.0.0/20 --region us-west-2 --query 'Vpc.VpcId' --output text)

# Crear subredes para VPC1 (us-east-1)
SUBNET_PUB_VPC1=$(aws ec2 create-subnet --vpc-id $VPC1 --cidr-block 192.168.1.0/24 --availability-zone us-east-1a --region us-east-1 --query 'Subnet.SubnetId' --output text)
SUBNET_PRIV_VPC1=$(aws ec2 create-subnet --vpc-id $VPC1 --cidr-block 192.168.2.0/24 --availability-zone us-east-1b --region us-east-1 --query 'Subnet.SubnetId' --output text)

# Crear subredes para VPC2 (us-west-2)
SUBNET_PUB_VPC2=$(aws ec2 create-subnet --vpc-id $VPC2 --cidr-block 10.0.1.0/24 --availability-zone us-west-2a --region us-west-2 --query 'Subnet.SubnetId' --output text)
SUBNET_PRIV_VPC2=$(aws ec2 create-subnet --vpc-id $VPC2 --cidr-block 10.0.2.0/24 --availability-zone us-west-2b --region us-west-2 --query 'Subnet.SubnetId' --output text)

# Crear Internet Gateways para subredes públicas
IGW1=$(aws ec2 create-internet-gateway --region us-east-1 --query 'InternetGateway.InternetGatewayId' --output text)
IGW2=$(aws ec2 create-internet-gateway --region us-west-2 --query 'InternetGateway.InternetGatewayId' --output text)

# Asociar IGWs a VPCs
aws ec2 attach-internet-gateway --internet-gateway-id $IGW1 --vpc-id $VPC1 --region us-east-1
aws ec2 attach-internet-gateway --internet-gateway-id $IGW2 --vpc-id $VPC2 --region us-west-2

# Crear tablas de rutas para subredes públicas
RT_PUB_VPC1=$(aws ec2 create-route-table --vpc-id $VPC1 --region us-east-1 --query 'RouteTable.RouteTableId' --output text)
RT_PUB_VPC2=$(aws ec2 create-route-table --vpc-id $VPC2 --region us-west-2 --query 'RouteTable.RouteTableId' --output text)

# Asociar subredes públicas a sus tablas de rutas
aws ec2 associate-route-table --subnet-id $SUBNET_PUB_VPC1 --route-table-id $RT_PUB_VPC1 --region us-east-1
aws ec2 associate-route-table --subnet-id $SUBNET_PUB_VPC2 --route-table-id $RT_PUB_VPC2 --region us-west-2

# Crear rutas hacia Internet para subredes públicas
aws ec2 create-route --route-table-id $RT_PUB_VPC1 --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW1 --region us-east-1
aws ec2 create-route --route-table-id $RT_PUB_VPC2 --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW2 --region us-west-2

# Crear peering
PEER=$(aws ec2 create-vpc-peering-connection --vpc-id $VPC1 --peer-vpc-id $VPC2 --peer-region us-west-2 --region us-east-1 --query 'VpcPeeringConnection.VpcPeeringConnectionId' --output text)

# Aceptar peering
aws ec2 accept-vpc-peering-connection --vpc-peering-connection-id $PEER --region us-west-2

# Configurar rutas para peering
RT1=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC1" --region us-east-1 --query 'RouteTables[0].RouteTableId' --output text)
RT2=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC2" --region us-west-2 --query 'RouteTables[0].RouteTableId' --output text)

aws ec2 create-route --route-table-id $RT1 --destination-cidr-block 10.0.0.0/20 --vpc-peering-connection-id $PEER --region us-east-1
aws ec2 create-route --route-table-id $RT2 --destination-cidr-block 192.168.0.0/20 --vpc-peering-connection-id $PEER --region us-west-2

# Agregar rutas de peering a tablas públicas
aws ec2 create-route --route-table-id $RT_PUB_VPC1 --destination-cidr-block 10.0.0.0/20 --vpc-peering-connection-id $PEER --region us-east-1
aws ec2 create-route --route-table-id $RT_PUB_VPC2 --destination-cidr-block 192.168.0.0/20 --vpc-peering-connection-id $PEER --region us-west-2

echo "Peering creado: $PEER"
echo "VPC1: $VPC1 - Subnet Pública: $SUBNET_PUB_VPC1 - Subnet Privada: $SUBNET_PRIV_VPC1"
echo "VPC2: $VPC2 - Subnet Pública: $SUBNET_PUB_VPC2 - Subnet Privada: $SUBNET_PRIV_VPC2"
