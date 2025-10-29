#Creo la vpc y devuelvo su id
VPC_ID=$(aws ec2 create-vpc --cidr-block 192.168.1.0/24  \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=nubexavi}]' \
    --query Vpc.VpcId --output text)

echo $VPC_ID

#Habilitar el dns en el vpc
aws ec2 modify-vpc-attribute \
    --vpc-id $VPC_ID \
    --enable-dns-hostnames "{\"Value\":true}"

#Creo la subnet y devuelvo su id
SUBNET_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 192.168.1.0/28 \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=misubredXAVI2}]' \
    --query Subnet.SubnetId --output text)

echo $SUBNET_ID

#Habilito la asignacion de la ipv4publica en la subred
#Comprobar como no se habilita y tenemos que hacerlo a posteriori
aws ec2 modify-subnet-attribute \
  --subnet-id $SUBNET_ID \
  --map-public-ip-on-launch