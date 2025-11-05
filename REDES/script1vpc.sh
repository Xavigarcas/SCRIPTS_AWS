#Creo la vpc y devuelvo su id
VPC_ID=$(aws ec2 create-vpc --cidr-block 192.168.2.0/24  \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=nubexavi2}]' \
    --query Vpc.VpcId --output text)

echo $VPC_ID

#Habilitar el dns en el vpc
aws ec2 modify-vpc-attribute \
    --vpc-id $VPC_ID \
    --enable-dns-hostnames "{\"Value\":true}"

#Creo la subnet y devuelvo su id
SUBNET_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 192.168.2.0/28 \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=misubredXAVI3}]' \
    --query Subnet.SubnetId --output text)

echo $SUBNET_ID

#Habilito la asignacion de la ipv4publica en la subred
#Comprobar como no se habilita y tenemos que hacerlo a posteriori
aws ec2 modify-subnet-attribute \
  --subnet-id $SUBNET_ID \
  --map-public-ip-on-launch

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
    --query Instances.InstanceId --output text)

sleep 15
echo $EC2_ID

