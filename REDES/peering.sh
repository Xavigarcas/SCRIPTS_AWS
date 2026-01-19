aws ec2 create-vpc-peering-connection \
  --region us-east-1 \
  --vpc-id vpc-001d1df8fd6d6b54b \
  --peer-vpc-id vpc-04295cae7644ff6df \
  --tag-specifications 'ResourceType=vpc-peering-connection,Tags=[{Key=Name,Value=Peering-A-B}]'

  PCX_ID=pcx-1234567890abcdef0   # el ID que te devolvió el comando anterior

aws ec2 accept-vpc-peering-connection \
  --region us-east-1 \
  --vpc-peering-connection-id pcx-0c181138a814d85db

aws ec2 describe-vpc-peering-connections \
  --region us-east-1 \
  --vpc-peering-connection-ids pcx-0c181138a814d85db \
  --query "VpcPeeringConnections[0].Status"

  aws ec2 create-route \
  --region us-east-1 \
  --route-table-id rtb-0936606530d3cb40e \
  --destination-cidr-block 172.16.0.0/24 \
  --vpc-peering-connection-id pcx-0c181138a814d85db

  aws ec2 create-route \
  --region us-east-1 \
  --route-table-id rtb-0a794786972d828fb \
  --destination-cidr-block 192.168.0.0/20 \
  --vpc-peering-connection-id pcx-0c181138a814d85db