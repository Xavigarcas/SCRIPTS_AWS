# CREAMOS Y ASOCIAMOS EL IGW A LA VPC
igw_response = ec2.create_internet_gateway()
igw_id = igw_response['InternetGateway']['InternetGatewayId']

ec2.attach_internet_gateway(
    InternetGatewayId=igw_id,
    VpcId=vpc_id
)

# CREAMOS LA TABLA DE RUTAS PUBLICA PARA PODER ACCEDER A INTERNET
rt_public_response = ec2.create_route_table(VpcId=vpc_id)
rt_public_id = rt_public_response['RouteTable']['RouteTableId']

ec2.create_route(
    RouteTableId=rt_public_id,
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=igw_id
)

# ASOCIAMOS TABLAS DE RUTAS A LA SUBRED PUBLICA
ec2.associate_route_table(
    SubnetId=pub_subnet_id,
    RouteTableId=rt_public_id
)

# ACTIVAMOS LA IP PUBLICA AUTOMATICA EN LA SUBRED PUBLICA PARA SUS INSTANCIAS
ec2.modify_subnet_attribute(
    SubnetId=pub_subnet_id,
    MapPublicIpOnLaunch={'Value': True}
)


print(f"Internet Gateway ID: {igw_id}")
print(f"Public Route Table ID: {rt_public_id}")