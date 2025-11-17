#Creo la vpc y devuelvo su id
VPC_ID=$(aws ec2 create-vpc --cidr-block 172.16.0.0/16  \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=nubePRACTICA}]' \
    --query Vpc.VpcId --output text)

echo $VPC_ID

#Habilitar el dns en el vpc
aws ec2 modify-vpc-attribute \
    --vpc-id $VPC_ID \
    --enable-dns-hostnames "{\"Value\":true}"

#Creo la subnet y devuelvo su id
SUBNET_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 172.16.0.0/20 \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=subredPRACTICA}]' \
    --query Subnet.SubnetId --output text)

echo $SUBNET_ID

IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=igwPRACTICA}]' \
  --query InternetGateway.InternetGatewayId --output text)


aws ec2 attach-internet-gateway \
  --internet-gateway-id $IGW_ID \
  --vpc-id $VPC_ID

#Obtenemos la tabla de rutas de la vpc
RT_ID=$(aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query "RouteTables[0].RouteTableId" \
  --output text)
#Añadimos la ruta hacia intenet
aws ec2 create-route \
  --route-table-id $RT_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID
  
aws ec2 associate-route-table \
  --route-table-id $RT_ID \
  --subnet-id $SUBNET_ID

aws ec2 create-tags \
  --resources $RT_ID \
  --tags Key=Name,Value=tabla_practica

#Creando grupo de seguridad
SG_ID=$(aws ec2 create-security-group \
  --group-name SGVPC \
  --description "Mi grupo de seguridad para abrir el puerto 80" \
  --vpc-id $VPC_ID \
  --query GroupId --output text)

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --ip-permissions '[{"IpProtocol":"tcp","FromPort":22,"ToPort":22,"IpRanges":[{"CidrIp":"0.0.0.0/0", "Description": "Allow ssh"}]}]' 
#    --protocol tcp \
#    --port 80 \
#    --cidr 0.0.0.0/0 > /dev/null

#Creando instancia ec2
EC2_ID=$(aws ec2 run-instances \
    --image-id ami-0360c520857e3138f \
    --instance-type t2.micro \
    --subnet-id $SUBNET_ID \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=miec2}]' \
    --key-name vockey \
    --associate-public-ip-address \
    --security-group-ids $SG_ID \
    --private-ip-address 172.16.0.100 \
    --query Instances.InstanceId --output text)

#Añadiendo el grupo de seguridad a posteriori
#aws ec2 modify-instance-attribute \
#    --instance-id $EC2_ID \
#    --groups $SG_ID

sleep 15
echo $EC2_ID




NEW_SUBNET_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 172.16.16.0/20 \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=subred2PRACTICA}]' \
  --query Subnet.SubnetId --output text)

# Asociarla a la tabla de enrutamiento (RT_ID previamente obtenida)
aws ec2 associate-route-table \
  --route-table-id $RT_ID \
  --subnet-id $NEW_SUBNET_ID



aws ec2 run-instances     --image-id ami-0360c520857e3138f     --instance-type t2.micro     --subnet-id subnet-05bb9508f27e6fa1a \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=miec2-2}]' \
  --key-name vockey     --associate-public-ip-address   --security-group-ids sg-0cfc9eead20bd8833 \
  --private-ip-address 172.16.16.100     --query Instances.InstanceId --output text

xavgarcas@client64:~/Descargas$ aws ec2 describe-route-tables \
  --filters "Name=association.subnet-id,Values=subnet-05bb9508f27e6fa1a" \
  --query "RouteTables[0].Associations[0].RouteTableAssociationId" \                                          
  --output text
rtbassoc-068572db2a55fa294
xavgarcas@client64:~/Descargas$ aws ec2 disassociate-route-table \
  --association-id rtbassoc-068572db2a55fa294

  	
subnet-05bb9508f27e6fa1a
