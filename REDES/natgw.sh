#CREACION VPC
VPC_ID=$(aws ec2 create-vpc --cidr-block 192.168.0.0/24  \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=nubePRACTICANATGW}]' \
    --query Vpc.VpcId --output text)

#CREACIÓN SUBRED PUBLICA
PUB_SUBNET_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 192.168.0.0/25 \
  --availability-zone us-east-1 \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=PublicaCLI}]' \
  --query 'Subnet.SubnetId' \
  --output text)

#CREACION SUBRED PRIVADA
PRIV_SUBNET_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 192.168.0.128/25 \
  --availability-zone us-east-1 \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=PrivadaCLI}]' \
  --query 'Subnet.SubnetId' \
  --output text)

#CREAMOS Y ASOCIAMOS EL IGW A LA VPC
IGW_ID=$(aws ec2 create-internet-gateway \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

aws ec2 attach-internet-gateway \
  --internet-gateway-id $IGW_ID \
  --vpc-id $VPC_ID

#CREAMOS LA TABLA DE RUTAS PUBLICA PARA PODER ACCEDER A INTERNET
RT_PUBLIC_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --query 'RouteTable.RouteTableId' \
  --output text)

aws ec2 create-route \
  --route-table-id $RT_PUBLIC_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID

#ASOCIAMOS TABLAS DE RUTAS A LA SUBRED PUBLICA
aws ec2 associate-route-table \
  --subnet-id $PUB_SUBNET_ID \
  --route-table-id $RT_PUBLIC_ID

#ACTIVAMOS LA IP PUBLICA AUTOMATICA EN LA SUBRED PUBLICA PARA SUS INSTANCIAS
aws ec2 modify-subnet-attribute \
  --subnet-id $PUB_SUBNET_ID \
  --map-public-ip-on-launch

#CREAMOS GRUPOS DE SEGURIDAD

SG_ID=$(aws ec2 create-security-group \
  --group-name SG-SSH-ICMP \
  --description "Permite SSH y ping desde cualquier lugar" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

  aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0


aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol icmp \
  --port -1 \
  --cidr 0.0.0.0/0


#LANZAMOS INSTANCIAS

EC2PUBLICA_ID=$(aws ec2 run-instances \
    --image-id ami-0360c520857e3138f \
    --instance-type t2.micro \
    --subnet-id $PUB_SUBNET_ID \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ec2publica}]' \
    --key-name vockey \
    --associate-public-ip-address \
    --security-group-ids $SG_ID \
    --private-ip-address 192.168.0.100 \
    --query Instances.InstanceId --output text)

EC2PRIVADA_ID=$(aws ec2 run-instances \
    --image-id ami-0360c520857e3138f \
    --instance-type t2.micro \
    --subnet-id $PRIV_SUBNET_ID \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ec2privada}]' \
    --key-name vockey \
    --associate-public-ip-address \
    --security-group-ids $SG_ID \
    --private-ip-address 192.168.0.200 \
    --query Instances.InstanceId --output text)


#CREACION DE LA IP ELASTICA PARA EL NAT GATEWAY
EIP_ALLOC_ID=$(aws ec2 allocate-address \
  --domain vpc \
  --query 'AllocationId' \
  --output text)

#CREAMOS LA NAT GATEWAY EN LA SUBRED PUBLICA
NAT_GW_ID=$(aws ec2 create-nat-gateway \
  --subnet-id $PUB_SUBNET_ID \
  --allocation-id $EIP_ALLOC_ID \
  --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=NAT-Publica}]' \
  --query 'NatGateway.NatGatewayId' \
  --output text)

# Esperar a que el NAT esté disponible
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_ID


#CREAMOS LA TABLA DE RUTAS PARA LA SUBRED PRIVADA
RT_PRIVATE_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --query 'RouteTable.RouteTableId' \
  --output text)

#ASOCIAMOS LA TABLAS DE RUTAS PRIVADA A LA SUBRED PRIVADA
aws ec2 associate-route-table \
  --subnet-id $PRIV_SUBNET_ID \
  --route-table-id $RT_PRIVATE_ID

#CREAMOS LA RUTA EN LA TABLA DE RUTAS APUNTANDO HACIA LA NATGW
aws ec2 create-route \
  --route-table-id $RT_PRIVATE_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW_ID
