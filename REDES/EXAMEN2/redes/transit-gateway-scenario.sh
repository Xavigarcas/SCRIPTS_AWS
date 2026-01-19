#!/bin/bash

echo "=== Creando infraestructura con Transit Gateways y Peering ==="

# REGIÓN US-EAST-1 (Virginia)
echo "Creando VPCs en us-east-1..."
VPC1_EAST=$(aws ec2 create-vpc --cidr-block 10.1.0.0/16 --region us-east-1 --query 'Vpc.VpcId' --output text)
VPC2_EAST=$(aws ec2 create-vpc --cidr-block 10.2.0.0/16 --region us-east-1 --query 'Vpc.VpcId' --output text)

# Subredes públicas en us-east-1
SUBNET1_EAST=$(aws ec2 create-subnet --vpc-id $VPC1_EAST --cidr-block 10.1.1.0/24 --availability-zone us-east-1a --region us-east-1 --query 'Subnet.SubnetId' --output text)
SUBNET2_EAST=$(aws ec2 create-subnet --vpc-id $VPC2_EAST --cidr-block 10.2.1.0/24 --availability-zone us-east-1b --region us-east-1 --query 'Subnet.SubnetId' --output text)

# Internet Gateways us-east-1
IGW1_EAST=$(aws ec2 create-internet-gateway --region us-east-1 --query 'InternetGateway.InternetGatewayId' --output text)
IGW2_EAST=$(aws ec2 create-internet-gateway --region us-east-1 --query 'InternetGateway.InternetGatewayId' --output text)

aws ec2 attach-internet-gateway --internet-gateway-id $IGW1_EAST --vpc-id $VPC1_EAST --region us-east-1
aws ec2 attach-internet-gateway --internet-gateway-id $IGW2_EAST --vpc-id $VPC2_EAST --region us-east-1

# Tablas de rutas us-east-1
RT1_EAST=$(aws ec2 create-route-table --vpc-id $VPC1_EAST --region us-east-1 --query 'RouteTable.RouteTableId' --output text)
RT2_EAST=$(aws ec2 create-route-table --vpc-id $VPC2_EAST --region us-east-1 --query 'RouteTable.RouteTableId' --output text)

aws ec2 associate-route-table --subnet-id $SUBNET1_EAST --route-table-id $RT1_EAST --region us-east-1
aws ec2 associate-route-table --subnet-id $SUBNET2_EAST --route-table-id $RT2_EAST --region us-east-1

aws ec2 create-route --route-table-id $RT1_EAST --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW1_EAST --region us-east-1
aws ec2 create-route --route-table-id $RT2_EAST --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW2_EAST --region us-east-1

# REGIÓN US-WEST-2 (Oregon)
echo "Creando VPCs en us-west-2..."
VPC1_WEST=$(aws ec2 create-vpc --cidr-block 192.168.0.0/16 --region us-west-2 --query 'Vpc.VpcId' --output text)
VPC2_WEST=$(aws ec2 create-vpc --cidr-block 192.224.0.0/16 --region us-west-2 --query 'Vpc.VpcId' --output text)

# Subredes públicas en us-west-2
SUBNET1_WEST=$(aws ec2 create-subnet --vpc-id $VPC1_WEST --cidr-block 192.168.1.0/24 --availability-zone us-west-2a --region us-west-2 --query 'Subnet.SubnetId' --output text)
SUBNET2_WEST=$(aws ec2 create-subnet --vpc-id $VPC2_WEST --cidr-block 192.224.1.0/24 --availability-zone us-west-2b --region us-west-2 --query 'Subnet.SubnetId' --output text)

# Internet Gateways us-west-2
IGW1_WEST=$(aws ec2 create-internet-gateway --region us-west-2 --query 'InternetGateway.InternetGatewayId' --output text)
IGW2_WEST=$(aws ec2 create-internet-gateway --region us-west-2 --query 'InternetGateway.InternetGatewayId' --output text)

aws ec2 attach-internet-gateway --internet-gateway-id $IGW1_WEST --vpc-id $VPC1_WEST --region us-west-2
aws ec2 attach-internet-gateway --internet-gateway-id $IGW2_WEST --vpc-id $VPC2_WEST --region us-west-2

# Tablas de rutas us-west-2
RT1_WEST=$(aws ec2 create-route-table --vpc-id $VPC1_WEST --region us-west-2 --query 'RouteTable.RouteTableId' --output text)
RT2_WEST=$(aws ec2 create-route-table --vpc-id $VPC2_WEST --region us-west-2 --query 'RouteTable.RouteTableId' --output text)

aws ec2 associate-route-table --subnet-id $SUBNET1_WEST --route-table-id $RT1_WEST --region us-west-2
aws ec2 associate-route-table --subnet-id $SUBNET2_WEST --route-table-id $RT2_WEST --region us-west-2

aws ec2 create-route --route-table-id $RT1_WEST --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW1_WEST --region us-west-2
aws ec2 create-route --route-table-id $RT2_WEST --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW2_WEST --region us-west-2

# TRANSIT GATEWAYS
echo "Creando Transit Gateways..."
TGW_EAST=$(aws ec2 create-transit-gateway --region us-east-1 --query 'TransitGateway.TransitGatewayId' --output text)
TGW_WEST=$(aws ec2 create-transit-gateway --region us-west-2 --query 'TransitGateway.TransitGatewayId' --output text)

# Esperar a que los TGW estén disponibles
echo "Esperando a que los Transit Gateways estén disponibles..."
aws ec2 wait transit-gateway-available --transit-gateway-ids $TGW_EAST --region us-east-1
aws ec2 wait transit-gateway-available --transit-gateway-ids $TGW_WEST --region us-west-2

# Attachments de VPCs a Transit Gateways
echo "Conectando VPCs a Transit Gateways..."
ATTACH1_EAST=$(aws ec2 create-transit-gateway-vpc-attachment --transit-gateway-id $TGW_EAST --vpc-id $VPC1_EAST --subnet-ids $SUBNET1_EAST --region us-east-1 --query 'TransitGatewayVpcAttachment.TransitGatewayAttachmentId' --output text)
ATTACH2_EAST=$(aws ec2 create-transit-gateway-vpc-attachment --transit-gateway-id $TGW_EAST --vpc-id $VPC2_EAST --subnet-ids $SUBNET2_EAST --region us-east-1 --query 'TransitGatewayVpcAttachment.TransitGatewayAttachmentId' --output text)

ATTACH1_WEST=$(aws ec2 create-transit-gateway-vpc-attachment --transit-gateway-id $TGW_WEST --vpc-id $VPC1_WEST --subnet-ids $SUBNET1_WEST --region us-west-2 --query 'TransitGatewayVpcAttachment.TransitGatewayAttachmentId' --output text)
ATTACH2_WEST=$(aws ec2 create-transit-gateway-vpc-attachment --transit-gateway-id $TGW_WEST --vpc-id $VPC2_WEST --subnet-ids $SUBNET2_WEST --region us-west-2 --query 'TransitGatewayVpcAttachment.TransitGatewayAttachmentId' --output text)

# Esperar attachments
echo "Esperando attachments..."
sleep 60

# PEERING entre Transit Gateways
echo "Creando peering entre Transit Gateways..."
TGW_PEER=$(aws ec2 create-transit-gateway-peering-attachment --transit-gateway-id $TGW_EAST --peer-transit-gateway-id $TGW_WEST --peer-region us-west-2 --region us-east-1 --query 'TransitGatewayPeeringAttachment.TransitGatewayAttachmentId' --output text)

# Aceptar peering
aws ec2 accept-transit-gateway-peering-attachment --transit-gateway-attachment-id $TGW_PEER --region us-west-2

# Esperar peering
echo "Esperando peering..."
sleep 60

# RUTAS en Transit Gateways
echo "Configurando rutas..."

# Rutas en TGW East hacia West
aws ec2 create-route --route-table-id $(aws ec2 describe-transit-gateways --transit-gateway-ids $TGW_EAST --region us-east-1 --query 'TransitGateways[0].Options.DefaultRouteTableId' --output text) --destination-cidr-block 192.168.0.0/16 --transit-gateway-attachment-id $TGW_PEER --region us-east-1
aws ec2 create-route --route-table-id $(aws ec2 describe-transit-gateways --transit-gateway-ids $TGW_EAST --region us-east-1 --query 'TransitGateways[0].Options.DefaultRouteTableId' --output text) --destination-cidr-block 192.224.0.0/16 --transit-gateway-attachment-id $TGW_PEER --region us-east-1

# Rutas en TGW West hacia East
aws ec2 create-route --route-table-id $(aws ec2 describe-transit-gateways --transit-gateway-ids $TGW_WEST --region us-west-2 --query 'TransitGateways[0].Options.DefaultRouteTableId' --output text) --destination-cidr-block 10.1.0.0/16 --transit-gateway-attachment-id $TGW_PEER --region us-west-2
aws ec2 create-route --route-table-id $(aws ec2 describe-transit-gateways --transit-gateway-ids $TGW_WEST --region us-west-2 --query 'TransitGateways[0].Options.DefaultRouteTableId' --output text) --destination-cidr-block 10.2.0.0/16 --transit-gateway-attachment-id $TGW_PEER --region us-west-2

# Rutas en VPCs hacia Transit Gateways
aws ec2 create-route --route-table-id $RT1_EAST --destination-cidr-block 10.2.0.0/16 --transit-gateway-id $TGW_EAST --region us-east-1
aws ec2 create-route --route-table-id $RT1_EAST --destination-cidr-block 192.168.0.0/16 --transit-gateway-id $TGW_EAST --region us-east-1
aws ec2 create-route --route-table-id $RT1_EAST --destination-cidr-block 192.224.0.0/16 --transit-gateway-id $TGW_EAST --region us-east-1

aws ec2 create-route --route-table-id $RT2_EAST --destination-cidr-block 10.1.0.0/16 --transit-gateway-id $TGW_EAST --region us-east-1
aws ec2 create-route --route-table-id $RT2_EAST --destination-cidr-block 192.168.0.0/16 --transit-gateway-id $TGW_EAST --region us-east-1
aws ec2 create-route --route-table-id $RT2_EAST --destination-cidr-block 192.224.0.0/16 --transit-gateway-id $TGW_EAST --region us-east-1

aws ec2 create-route --route-table-id $RT1_WEST --destination-cidr-block 192.224.0.0/16 --transit-gateway-id $TGW_WEST --region us-west-2
aws ec2 create-route --route-table-id $RT1_WEST --destination-cidr-block 10.1.0.0/16 --transit-gateway-id $TGW_WEST --region us-west-2
aws ec2 create-route --route-table-id $RT1_WEST --destination-cidr-block 10.2.0.0/16 --transit-gateway-id $TGW_WEST --region us-west-2

aws ec2 create-route --route-table-id $RT2_WEST --destination-cidr-block 192.168.0.0/16 --transit-gateway-id $TGW_WEST --region us-west-2
aws ec2 create-route --route-table-id $RT2_WEST --destination-cidr-block 10.1.0.0/16 --transit-gateway-id $TGW_WEST --region us-west-2
aws ec2 create-route --route-table-id $RT2_WEST --destination-cidr-block 10.2.0.0/16 --transit-gateway-id $TGW_WEST --region us-west-2

# Security Groups
echo "Creando Security Groups..."
SG1_EAST=$(aws ec2 create-security-group --group-name sg-east-1 --description "SG East 1" --vpc-id $VPC1_EAST --region us-east-1 --query 'GroupId' --output text)
SG2_EAST=$(aws ec2 create-security-group --group-name sg-east-2 --description "SG East 2" --vpc-id $VPC2_EAST --region us-east-1 --query 'GroupId' --output text)
SG1_WEST=$(aws ec2 create-security-group --group-name sg-west-1 --description "SG West 1" --vpc-id $VPC1_WEST --region us-west-2 --query 'GroupId' --output text)
SG2_WEST=$(aws ec2 create-security-group --group-name sg-west-2 --description "SG West 2" --vpc-id $VPC2_WEST --region us-west-2 --query 'GroupId' --output text)

# Reglas de Security Groups
aws ec2 authorize-security-group-ingress --group-id $SG1_EAST --protocol icmp --port -1 --cidr 0.0.0.0/0 --region us-east-1
aws ec2 authorize-security-group-ingress --group-id $SG1_EAST --protocol tcp --port 22 --cidr 0.0.0.0/0 --region us-east-1
aws ec2 authorize-security-group-ingress --group-id $SG2_EAST --protocol icmp --port -1 --cidr 0.0.0.0/0 --region us-east-1
aws ec2 authorize-security-group-ingress --group-id $SG2_EAST --protocol tcp --port 22 --cidr 0.0.0.0/0 --region us-east-1
aws ec2 authorize-security-group-ingress --group-id $SG1_WEST --protocol icmp --port -1 --cidr 0.0.0.0/0 --region us-west-2
aws ec2 authorize-security-group-ingress --group-id $SG1_WEST --protocol tcp --port 22 --cidr 0.0.0.0/0 --region us-west-2
aws ec2 authorize-security-group-ingress --group-id $SG2_WEST --protocol icmp --port -1 --cidr 0.0.0.0/0 --region us-west-2
aws ec2 authorize-security-group-ingress --group-id $SG2_WEST --protocol tcp --port 22 --cidr 0.0.0.0/0 --region us-west-2

echo "=== RESUMEN DE LA INFRAESTRUCTURA ==="
echo "US-EAST-1:"
echo "  VPC1: $VPC1_EAST (10.1.0.0/16) - Subnet: $SUBNET1_EAST"
echo "  VPC2: $VPC2_EAST (10.2.0.0/16) - Subnet: $SUBNET2_EAST"
echo "  Transit Gateway: $TGW_EAST"
echo ""
echo "US-WEST-2:"
echo "  VPC1: $VPC1_WEST (192.168.0.0/16) - Subnet: $SUBNET1_WEST"
echo "  VPC2: $VPC2_WEST (192.224.0.0/16) - Subnet: $SUBNET2_WEST"
echo "  Transit Gateway: $TGW_WEST"
echo ""
echo "Transit Gateway Peering: $TGW_PEER"
echo ""
echo "Security Groups creados con reglas ICMP y SSH"
echo "Infraestructura lista para crear instancias EC2"