#creamos una IGW y la conectamos a la vpc
IGW_ID=$(aws ec2 create-internet-gateway \
  --query InternetGateway.InternetGatewayId --output text)

aws ec2 attach-internet-gateway \
  --internet-gateway-id $IGW_ID \
  --vpc-id vpc-0d73347512377adab

#Obtenemos la tabla de rutas de la vpc
RT_ID=$(aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=vpc-0d73347512377adab" \
  --query "RouteTables[0].RouteTableId" \
  --output text)
#Añadimos la ruta hacia intenet
aws ec2 create-route \
  --route-table-id $RT_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID