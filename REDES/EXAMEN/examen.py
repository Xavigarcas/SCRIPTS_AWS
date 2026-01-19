#!/usr/bin/env python3
"""
Script de automatización para crear infraestructura de red AWS - EXAMEN
Implementa arquitectura multi-AZ con subredes públicas/privadas y Security Groups encadenados
Utiliza boto3 SDK para interactuar con los servicios de AWS EC2
"""

import boto3

print("Iniciando despliegue de infraestructura de examen AWS...")
ec2 = boto3.client('ec2')

# ========== CREACIÓN DE VPC ==========
print("Creando VPC con CIDR 10.10.0.0/16...")
vpc_response = ec2.create_vpc(
    CidrBlock='10.10.0.0/16',
    TagSpecifications=[
        {
            'ResourceType': 'vpc',
            'Tags': [{'Key': 'Name', 'Value': 'VPC-Examen'}]
        }
    ]
)
vpc_id = vpc_response['Vpc']['VpcId']
print(f"VPC creada: {vpc_id}")

# ========== CREACIÓN DE SUBREDES ==========
print("Creando subredes públicas y privadas en 2 AZs...")

# Subred pública 1 (AZ us-east-1a)
pub_subnet_1_response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.10.1.0/24',
    AvailabilityZone='us-east-1a',
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [{'Key': 'Name', 'Value': 'Publica-1-AZ-a'}]
        }
    ]
)
pub_subnet_1_id = pub_subnet_1_response['Subnet']['SubnetId']

# Subred pública 2 (AZ us-east-1b)
pub_subnet_2_response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.10.2.0/24',
    AvailabilityZone='us-east-1b',
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [{'Key': 'Name', 'Value': 'Publica-2-AZ-b'}]
        }
    ]
)
pub_subnet_2_id = pub_subnet_2_response['Subnet']['SubnetId']

# Subred privada 1 (AZ us-east-1a)
priv_subnet_1_response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.10.3.0/24',
    AvailabilityZone='us-east-1a',
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [{'Key': 'Name', 'Value': 'Privada-1-AZ-a'}]
        }
    ]
)
priv_subnet_1_id = priv_subnet_1_response['Subnet']['SubnetId']

# Subred privada 2 (AZ us-east-1b)
priv_subnet_2_response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.10.4.0/24',
    AvailabilityZone='us-east-1b',
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [{'Key': 'Name', 'Value': 'Privada-2-AZ-b'}]
        }
    ]
)
priv_subnet_2_id = priv_subnet_2_response['Subnet']['SubnetId']

print("Subredes creadas:")
print(f"  Públicas: {pub_subnet_1_id}, {pub_subnet_2_id}")
print(f"  Privadas: {priv_subnet_1_id}, {priv_subnet_2_id}")

# ========== INTERNET GATEWAY ==========
print("Creando y asociando Internet Gateway...")
igw_response = ec2.create_internet_gateway(
    TagSpecifications=[
        {
            'ResourceType': 'internet-gateway',
            'Tags': [{'Key': 'Name', 'Value': 'IGW-Examen'}]
        }
    ]
)
igw_id = igw_response['InternetGateway']['InternetGatewayId']

ec2.attach_internet_gateway(
    InternetGatewayId=igw_id,
    VpcId=vpc_id
)
print(f"Internet Gateway creado: {igw_id}")

# ========== NAT GATEWAY ==========
print("Creando NAT Gateway en subred pública 1...")
eip_response = ec2.allocate_address(
    Domain='vpc',
    TagSpecifications=[
        {
            'ResourceType': 'elastic-ip',
            'Tags': [{'Key': 'Name', 'Value': 'EIP-NAT'}]
        }
    ]
)
eip_alloc_id = eip_response['AllocationId']

nat_gw_response = ec2.create_nat_gateway(
    SubnetId=pub_subnet_1_id,
    AllocationId=eip_alloc_id,
    TagSpecifications=[
        {
            'ResourceType': 'natgateway',
            'Tags': [{'Key': 'Name', 'Value': 'NAT-Gateway'}]
        }
    ]
)
nat_gw_id = nat_gw_response['NatGateway']['NatGatewayId']

print(f"NAT Gateway creado: {nat_gw_id} (esperando disponibilidad...)")
waiter = ec2.get_waiter('nat_gateway_available')
waiter.wait(NatGatewayIds=[nat_gw_id])
print("NAT Gateway disponible")

# ========== TABLAS DE RUTAS ==========
print("Creando tablas de rutas...")

# Tabla de rutas pública 1
rt_pub_1_response = ec2.create_route_table(
    VpcId=vpc_id,
    TagSpecifications=[
        {
            'ResourceType': 'route-table',
            'Tags': [{'Key': 'Name', 'Value': 'RT-Publica-1'}]
        }
    ]
)
rt_pub_1_id = rt_pub_1_response['RouteTable']['RouteTableId']

# Tabla de rutas pública 2
rt_pub_2_response = ec2.create_route_table(
    VpcId=vpc_id,
    TagSpecifications=[
        {
            'ResourceType': 'route-table',
            'Tags': [{'Key': 'Name', 'Value': 'RT-Publica-2'}]
        }
    ]
)
rt_pub_2_id = rt_pub_2_response['RouteTable']['RouteTableId']

# Tabla de rutas privada 1
rt_priv_1_response = ec2.create_route_table(
    VpcId=vpc_id,
    TagSpecifications=[
        {
            'ResourceType': 'route-table',
            'Tags': [{'Key': 'Name', 'Value': 'RT-Privada-1'}]
        }
    ]
)
rt_priv_1_id = rt_priv_1_response['RouteTable']['RouteTableId']

# Tabla de rutas privada 2
rt_priv_2_response = ec2.create_route_table(
    VpcId=vpc_id,
    TagSpecifications=[
        {
            'ResourceType': 'route-table',
            'Tags': [{'Key': 'Name', 'Value': 'RT-Privada-2'}]
        }
    ]
)
rt_priv_2_id = rt_priv_2_response['RouteTable']['RouteTableId']

print("Tablas de rutas creadas")

# ========== CONFIGURACIÓN DE RUTAS ==========
print("Configurando rutas...")

# Rutas públicas (hacia Internet Gateway)
ec2.create_route(
    RouteTableId=rt_pub_1_id,
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=igw_id
)
ec2.create_route(
    RouteTableId=rt_pub_2_id,
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=igw_id
)

# Rutas privadas (hacia NAT Gateway)
ec2.create_route(
    RouteTableId=rt_priv_1_id,
    DestinationCidrBlock='0.0.0.0/0',
    NatGatewayId=nat_gw_id
)
ec2.create_route(
    RouteTableId=rt_priv_2_id,
    DestinationCidrBlock='0.0.0.0/0',
    NatGatewayId=nat_gw_id
)

# ========== ASOCIACIÓN DE TABLAS DE RUTAS ==========
print("Asociando tablas de rutas con subredes...")
ec2.associate_route_table(SubnetId=pub_subnet_1_id, RouteTableId=rt_pub_1_id)
ec2.associate_route_table(SubnetId=pub_subnet_2_id, RouteTableId=rt_pub_2_id)
ec2.associate_route_table(SubnetId=priv_subnet_1_id, RouteTableId=rt_priv_1_id)
ec2.associate_route_table(SubnetId=priv_subnet_2_id, RouteTableId=rt_priv_2_id)

# Habilitar IP pública automática en subredes públicas
ec2.modify_subnet_attribute(
    SubnetId=pub_subnet_1_id,
    MapPublicIpOnLaunch={'Value': True}
)
ec2.modify_subnet_attribute(
    SubnetId=pub_subnet_2_id,
    MapPublicIpOnLaunch={'Value': True}
)

# ========== GRUPOS DE SEGURIDAD ENCADENADOS ==========
print("Creando grupos de seguridad encadenados...")

# Security Group para instancias públicas (Bastion)
sg_public_response = ec2.create_security_group(
    GroupName='SG-Public-Bastion',
    Description='Permite SSH desde Internet',
    VpcId=vpc_id,
    TagSpecifications=[
        {
            'ResourceType': 'security-group',
            'Tags': [{'Key': 'Name', 'Value': 'SG-Public'}]
        }
    ]
)
sg_public_id = sg_public_response['GroupId']

# Regla SSH desde Internet para bastion
ec2.authorize_security_group_ingress(
    GroupId=sg_public_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
    ]
)

# Security Group para instancias privadas
sg_private_response = ec2.create_security_group(
    GroupName='SG-Private-Backend',
    Description='Permite acceso solo desde subredes publicas',
    VpcId=vpc_id,
    TagSpecifications=[
        {
            'ResourceType': 'security-group',
            'Tags': [{'Key': 'Name', 'Value': 'SG-Private'}]
        }
    ]
)
sg_private_id = sg_private_response['GroupId']

# Reglas SSH e ICMP solo desde Security Group público (encadenamiento)
ec2.authorize_security_group_ingress(
    GroupId=sg_private_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'UserIdGroupPairs': [{'GroupId': sg_public_id}]
        },
        {
            'IpProtocol': 'icmp',
            'FromPort': -1,
            'ToPort': -1,
            'UserIdGroupPairs': [{'GroupId': sg_public_id}]
        }
    ]
)

print("Security Groups creados con encadenamiento:")
print(f"  Público: {sg_public_id} (SSH desde Internet)")
print(f"  Privado: {sg_private_id} (SSH/ICMP solo desde SG público)")

# ========== RESUMEN ==========
print("\n" + "="*60)
print("    INFRAESTRUCTURA DE EXAMEN DESPLEGADA")
print("="*60)
print(f"VPC ID:                {vpc_id}")
print(f"Internet Gateway:      {igw_id}")
print(f"NAT Gateway:           {nat_gw_id}")
print(f"Elastic IP:            {eip_alloc_id}")
print("")
print("SUBREDES:")
print(f"  Pública 1 (AZ-a):    {pub_subnet_1_id}")
print(f"  Pública 2 (AZ-b):    {pub_subnet_2_id}")
print(f"  Privada 1 (AZ-a):    {priv_subnet_1_id}")
print(f"  Privada 2 (AZ-b):    {priv_subnet_2_id}")
print("")
print("TABLAS DE RUTAS:")
print(f"  RT Pública 1:         {rt_pub_1_id}")
print(f"  RT Pública 2:         {rt_pub_2_id}")
print(f"  RT Privada 1:         {rt_priv_1_id}")
print(f"  RT Privada 2:         {rt_priv_2_id}")
print("")
print("SECURITY GROUPS:")
print(f"  SG Público:           {sg_public_id}")
print(f"  SG Privado:           {sg_private_id}")
print("="*60)
print("Arquitectura multi-AZ con encadenamiento de SG completada")
print("Acceso privado SOLO desde subredes públicas garantizado")
print("="*60)