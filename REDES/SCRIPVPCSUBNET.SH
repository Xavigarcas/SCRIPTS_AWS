
# Crear VPC con etiquetas Name y entorno
VPC_ID=$(aws ec2 create-vpc --cidr-block 192.168.0.0/24 \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=vpcdelete},{Key=entorno,Value=prueba}]' \
    --query Vpc.VpcId --output text)

echo "VPC creada: $VPC_ID"

# Habilitar el DNS en la VPC
aws ec2 modify-vpc-attribute \
    --vpc-id $VPC_ID \
    --enable-dns-hostnames "{\"Value\":true}"

# Crear primera subnet con etiquetas Name y entorno
SUBNET_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 192.168.0.0/28 \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=sr1},{Key=entorno,Value=prueba}]' \
    --query Subnet.SubnetId --output text)
echo "Subnet 1 creada: $SUBNET_ID"

# Crear segunda subnet con etiquetas Name y entorno
SUBNET_ID2=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 192.168.0.16/28 \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=sr2},{Key=entorno,Value=prueba}]' \
    --query Subnet.SubnetId --output text)
echo "Subnet 2 creada: $SUBNET_ID2"


EC2_ID=$(aws ec2 run-instances \
    --image-id ami-0360c520857e3138f \
    --instance-type t2.micro \
    --subnet-id $SUBNET_ID \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=instancia1borrar},{Key=entorno,Value=prueba}]'  \
    --key-name vockey \
    --associate-public-ip-address \
    --query Instances.InstanceId --output text)


# Comprobar si la instancia se creó correctamente
if [ -z "$EC2_ID" ] || [ "$EC2_ID" == "None" ]; then
  echo "Se ha podido crear correctamente la instancia"
  exit 1
fi

echo "Instancia EC2 creada: $EC2_ID"

# Esperar a que la instancia esté en estado 'running'
echo "Esperando a que la instancia $EC2_ID esté en estado 'running'..."
aws ec2 wait instance-running --instance-ids "$EC2_ID"

echo "✅ La instancia $EC2_ID ya está en ejecución."
