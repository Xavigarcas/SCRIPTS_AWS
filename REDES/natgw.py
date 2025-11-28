import boto3

ec2 = boto3.client('ec2')

# CREACION VPC
vpc_response = ec2.create_vpc(
    CidrBlock='192.168.0.0/24',
    TagSpecifications=[
        {
            'ResourceType': 'vpc',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'nubePRACTICANATGW'
                }
            ]
        }
    ]
)
vpc_id = vpc_response['Vpc']['VpcId']

# CREACIÓN SUBRED PUBLICA
pub_subnet_response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='192.168.0.0/25',
    AvailabilityZone='us-east-1a',
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'PublicaCLI'
                }
            ]
        }
    ]
)
pub_subnet_id = pub_subnet_response['Subnet']['SubnetId']

# CREACION SUBRED PRIVADA
priv_subnet_response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='192.168.0.128/25',
    AvailabilityZone='us-east-1a',
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'PrivadaCLI'
                }
            ]
        }
    ]
)
priv_subnet_id = priv_subnet_response['Subnet']['SubnetId']

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

print(f"VPC ID: {vpc_id}")
print(f"Public Subnet ID: {pub_subnet_id}")
print(f"Private Subnet ID: {priv_subnet_id}")
print(f"Internet Gateway ID: {igw_id}")
print(f"Public Route Table ID: {rt_public_id}")