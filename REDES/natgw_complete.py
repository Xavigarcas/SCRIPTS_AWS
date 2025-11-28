import boto3

ec2 = boto3.client('ec2')

# CREACION VPC
vpc_response = ec2.create_vpc(
    CidrBlock='192.168.0.0/24',
    TagSpecifications=[
        {
            'ResourceType': 'vpc',
            'Tags': [{'Key': 'Name', 'Value': 'nubePRACTICANATGW'}]
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
            'Tags': [{'Key': 'Name', 'Value': 'PublicaCLI'}]
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
            'Tags': [{'Key': 'Name', 'Value': 'PrivadaCLI'}]
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

# CREAMOS GRUPOS DE SEGURIDAD
sg_response = ec2.create_security_group(
    GroupName='SG-SSH-ICMP',
    Description='Permite SSH y ping desde cualquier lugar',
    VpcId=vpc_id
)
sg_id = sg_response['GroupId']

ec2.authorize_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        },
        {
            'IpProtocol': 'icmp',
            'FromPort': -1,
            'ToPort': -1,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
    ]
)

# LANZAMOS INSTANCIAS
ec2_publica_response = ec2.run_instances(
    ImageId='ami-0360c520857e3138f',
    InstanceType='t2.micro',
    SubnetId=pub_subnet_id,
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'ec2publica'}]
        }
    ],
    KeyName='vockey',
    SecurityGroupIds=[sg_id],
    PrivateIpAddress='192.168.0.100',
    MinCount=1,
    MaxCount=1
)
ec2_publica_id = ec2_publica_response['Instances'][0]['InstanceId']

ec2_privada_response = ec2.run_instances(
    ImageId='ami-0360c520857e3138f',
    InstanceType='t2.micro',
    SubnetId=priv_subnet_id,
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'ec2privada'}]
        }
    ],
    KeyName='vockey',
    SecurityGroupIds=[sg_id],
    PrivateIpAddress='192.168.0.200',
    MinCount=1,
    MaxCount=1
)
ec2_privada_id = ec2_privada_response['Instances'][0]['InstanceId']

# CREACION DE LA IP ELASTICA PARA EL NAT GATEWAY
eip_response = ec2.allocate_address(Domain='vpc')
eip_alloc_id = eip_response['AllocationId']

# CREAMOS LA NAT GATEWAY EN LA SUBRED PUBLICA
nat_gw_response = ec2.create_nat_gateway(
    SubnetId=pub_subnet_id,
    AllocationId=eip_alloc_id,
    TagSpecifications=[
        {
            'ResourceType': 'natgateway',
            'Tags': [{'Key': 'Name', 'Value': 'NAT-Publica'}]
        }
    ]
)
nat_gw_id = nat_gw_response['NatGateway']['NatGatewayId']

# Esperar a que el NAT esté disponible
waiter = ec2.get_waiter('nat_gateway_available')
waiter.wait(NatGatewayIds=[nat_gw_id])

# CREAMOS LA TABLA DE RUTAS PARA LA SUBRED PRIVADA
rt_private_response = ec2.create_route_table(VpcId=vpc_id)
rt_private_id = rt_private_response['RouteTable']['RouteTableId']

# ASOCIAMOS LA TABLAS DE RUTAS PRIVADA A LA SUBRED PRIVADA
ec2.associate_route_table(
    SubnetId=priv_subnet_id,
    RouteTableId=rt_private_id
)

# CREAMOS LA RUTA EN LA TABLA DE RUTAS APUNTANDO HACIA LA NATGW
ec2.create_route(
    RouteTableId=rt_private_id,
    DestinationCidrBlock='0.0.0.0/0',
    NatGatewayId=nat_gw_id
)

print(f"VPC ID: {vpc_id}")
print(f"Public Subnet ID: {pub_subnet_id}")
print(f"Private Subnet ID: {priv_subnet_id}")
print(f"Internet Gateway ID: {igw_id}")
print(f"Security Group ID: {sg_id}")
print(f"Public EC2 ID: {ec2_publica_id}")
print(f"Private EC2 ID: {ec2_privada_id}")
print(f"NAT Gateway ID: {nat_gw_id}")