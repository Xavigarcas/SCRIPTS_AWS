aws ec2 create-vpc --cidr-block 192.168.0.0/24  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=xaviVPC}]' --query Vpc.VpcId --output text

ws ec2 create-subnet --vpc-id nombrevpc --cidr-block 192.168.0.0/28 --availability-zone us-east-1a --query Subnet.SubnetId --output text