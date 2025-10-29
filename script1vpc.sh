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
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=misubredXAVI1}]' \
    --query Subnet.SubnetId --output text)

echo $SUBNET_ID