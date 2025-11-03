#VER GRUPOS DE SEGURIDAD
aws ec2 describe-security-groups

#CREAR GRUPO DE SEGURIDAD
aws ec2 create-security-group --group-name CLISERVER-SG --description "ssh+http"
aws ec2 authorize-security-group-ingress --group-id sg-0801a29d47c10e288 --protocol tcp --port 22 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress --group-id id-del-grupo \
aws ec2 authorize-security-group-ingress --group-id sg-0801a29d47c10e288 --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 describe-security-groups --group-ids sg-0801a29d47c10e288
aws ec2 describe-subnets --query Subnets[*].SubnetId --filters "Name=availability-zone,Values=us-east-1a"

aws ec2 run-instances   --image-id ami-0360c520857e3138f   --instance-type t3.micro   --key-name vockey   --security-group-ids sg-0801a29d47c10e288   --subnet-id subnet-0a1cd13e621dd4344   --iam-instance-profile Name=LabInstanceProfile

aws ec2 run-instances   --image-id ami-0360c520857e3138f   --instance-type t3.micro   --key-name vockey   --security-group-ids sg-0801a29d47c10e288   --subnet-id subnet-0a1cd13e621dd4344   --iam-instance-profile Name=LabInstanceProfile --user-data file://servidorweb.sh

aws ec2 describe-instances

aws ec2 describe-instances

aws ec2 describe-instances i-04315e0756a433bf2

aws ec2 describe-instances --instance-ids i-04315e0756a433bf2 --query Reservations[*].Instances[*].[InstanceType,VpcId,PrivateIpAddress,PublicIpAddress,SubnetId,SecurityGroups] --output table

aws ec2 describe-instances --instance-ids i-04315e0756a433bf2 --query Reservations[*].Instances[*].[InstanceType,VpcId,PrivateIpAddress,PublicIpAddress,SubnetId,SecurityGroups] --output text

aws ec2 create-tags --resources i-04315e0756a433bf2 --tags Key=Name,Value=MyWebServer

 aws ec2 create-volume --volume-type gp3 --size 1 --availability-zone us-east-1a

 aws ec2 attach-volume --volume-id vol-018a8d99304c56af0 --instance-id i-0508b9aac8be08dc3 --device /dev/sdf

 aws ec2 delete-volume --volume-id vol-018a8d99304c56af0


 
 
 
 
 
 
#METADATOS

 TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" \
-H "X-aws-ec2-metadata-token-ttl-seconds: 14400"`

curl -s "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-type
curl -s "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id
curl -s "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/local-ipv4
curl -s "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4
curl -s "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/mac
curl -s "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/security-groups
curl -s "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/region
curl -s "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone
curl -s "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone-id

curl -s "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/user-data

curl -s "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/tags/instance









#CREACION DE AMI y su posterior copia en otra region

aws ec2 create-image --instance-id i-0fe17ed1c3441466b --name "WebServerAMI" --no-reboot 

#esperamos a que este creada la ami en el este
aws ec2 wait image-available --image-ids ami-019ec7414b056b935

#COPIAMOS LA ID AL OESTE
aws ec2 copy-image --region us-west-2 --name AmiEste --source-region us-east-1 --source-image-id ami-019ec7414b056b935 

#esperamos a que se copie la ami en el oeste
aws ec2 wait image-available  --region us-west-2 --image-ids ami-085c1d8322641416b

#Creamos las claves en la region destino
aws ec2 create-key-pair --key-name ParOeste --region us-west-2
#Tenemos que redireccionar la salida para ello añadimos el campo --query 'KeyMaterial' --output text > ParOeste2.pem

#Lanzaremos la instancia a partir de la ami que hemos copiado en oregon --> us-west-2

#1erPaso SACAR Vpc por defecto
aws ec2 describe-vpcs --region us-west-2 --filters "Name=isDefault,Values=true" --query Vpcs[0].VpcId

#2ndPaso Sacar id de la subred
aws ec2 describe-subnets  --region us-west-2 --filters "Name=vpc-id,Values=vpc-033f89d89a3957de2" --query 'Subnets[0].SubnetId' --output text

#3erPaso Sacar el grupo de seguridad
aws ec2 describe-security-groups --region us-west-2 --filters "Name=vpc-id,Values=vpc-033f89d89a3957de2" "Name=group-name,Values=default" --query 'SecurityGroups[0].GroupId' --output text

#4toPaso Lanzar la instancia

aws ec2 run-instances --image-id ami-085c1d8322641416b --instance-type t3.micro --key-name "ParOeste2" --subnet-id "subnet-0405495357b0093a3" --security-group-ids "sg-0968d1afce013a0aa" --region "us-west-2"
