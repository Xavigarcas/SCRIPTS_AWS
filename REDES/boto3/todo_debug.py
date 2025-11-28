#!/usr/bin/env python3
"""
Script de automatización para crear infraestructura de red AWS con NAT Gateway
Implementa una arquitectura de red híbrida con subredes públicas y privadas
Utiliza boto3 SDK para interactuar con los servicios de AWS EC2
"""

import boto3

print("Iniciando despliegue de infraestructura de red AWS...")

# Inicialización del cliente EC2 con configuración por defecto
ec2 = boto3.client('ec2')

# ========== CREACIÓN DE VPC (Virtual Private Cloud) ==========
# Establece un espacio de red aislado con CIDR /24 (256 direcciones IP)
print("Creando VPC con segmentación de red /24...")
vpc_response = ec2.create_vpc(
    CidrBlock='192.168.0.0/24',  # Rango privado RFC 1918
    TagSpecifications=[
        {
            'ResourceType': 'vpc',
            'Tags': [{'Key': 'Name', 'Value': 'nubePRACTICANATGW'}]
        }
    ]
)
vpc_id = vpc_response['Vpc']['VpcId']
print(f"VPC creada exitosamente: {vpc_id}")

# ========== CREACIÓN DE SUBREDES CON SEGMENTACIÓN CIDR ==========
# Subred pública: 192.168.0.0/25 (128 IPs: .0-.127)
print("Creando subred pública con enrutamiento directo a Internet...")
pub_subnet_response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='192.168.0.0/25',  # Primera mitad del rango VPC
    AvailabilityZone='us-east-1a',  # AZ específica para alta disponibilidad
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [{'Key': 'Name', 'Value': 'PublicaCLI'}]
        }
    ]
)
pub_subnet_id = pub_subnet_response['Subnet']['SubnetId']

# Subred privada: 192.168.0.128/25 (128 IPs: .128-.255)
print("Creando subred privada con enrutamiento a través de NAT Gateway...")
priv_subnet_response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='192.168.0.128/25',  # Segunda mitad del rango VPC
    AvailabilityZone='us-east-1a',  # Misma AZ para optimización de costos
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [{'Key': 'Name', 'Value': 'PrivadaCLI'}]
        }
    ]
)
priv_subnet_id = priv_subnet_response['Subnet']['SubnetId']
print(f"Subredes creadas - Pública: {pub_subnet_id}, Privada: {priv_subnet_id}")

# ========== CONFIGURACIÓN DE INTERNET GATEWAY ==========
# IGW proporciona conectividad bidireccional entre VPC e Internet
print("Desplegando Internet Gateway para conectividad externa...")
igw_response = ec2.create_internet_gateway()
igw_id = igw_response['InternetGateway']['InternetGatewayId']

# Asociación del IGW a la VPC para habilitar enrutamiento de Internet
ec2.attach_internet_gateway(
    InternetGatewayId=igw_id,
    VpcId=vpc_id
)
print(f"Internet Gateway {igw_id} asociado exitosamente a VPC")

# ========== CONFIGURACIÓN DE ENRUTAMIENTO PÚBLICO ==========
# Tabla de rutas personalizada para tráfico de subred pública
print("Configurando tabla de enrutamiento para subred pública...")
rt_public_response = ec2.create_route_table(VpcId=vpc_id)
rt_public_id = rt_public_response['RouteTable']['RouteTableId']

# Ruta por defecto (0.0.0.0/0) dirigiendo todo el tráfico externo al IGW
ec2.create_route(
    RouteTableId=rt_public_id,
    DestinationCidrBlock='0.0.0.0/0',  # Ruta por defecto para Internet
    GatewayId=igw_id
)

# Asociación explícita de la tabla de rutas con la subred pública
ec2.associate_route_table(
    SubnetId=pub_subnet_id,
    RouteTableId=rt_public_id
)

# Habilitación automática de IPs públicas para instancias en subred pública
ec2.modify_subnet_attribute(
    SubnetId=pub_subnet_id,
    MapPublicIpOnLaunch={'Value': True}  # Auto-asignación de IP pública
)
print(f"Enrutamiento público configurado - Tabla: {rt_public_id}")

# ========== CONFIGURACIÓN DE SECURITY GROUPS ==========
# Firewall a nivel de instancia con reglas de entrada específicas
print("Creando Security Group con políticas de acceso SSH e ICMP...")
sg_response = ec2.create_security_group(
    GroupName='SG-SSH-ICMP',
    Description='Permite SSH (puerto 22) y ping (ICMP) desde cualquier origen',
    VpcId=vpc_id
)
sg_id = sg_response['GroupId']

# Configuración de reglas de entrada (ingress) para el Security Group
ec2.authorize_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # SSH desde cualquier IP
        },
        {
            'IpProtocol': 'icmp',
            'FromPort': -1,  # Todos los tipos ICMP
            'ToPort': -1,    # Todos los códigos ICMP
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Ping desde cualquier IP
        }
    ]
)
print(f"Security Group {sg_id} configurado con reglas SSH e ICMP")

# ========== DESPLIEGUE DE INSTANCIAS EC2 ==========
# Lanzamiento de instancias en subredes pública y privada
print("Desplegando instancias EC2 en arquitectura multi-tier...")

# Instancia en subred pública (Bastion Host / Jump Server)
ec2_publica_response = ec2.run_instances(
    ImageId='ami-0360c520857e3138f',  # Amazon Linux 2 AMI
    InstanceType='t2.micro',          # Instancia de capa gratuita
    SubnetId=pub_subnet_id,
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'ec2publica'}]
        }
    ],
    KeyName='vockey',                 # Par de claves para acceso SSH
    SecurityGroupIds=[sg_id],
    PrivateIpAddress='192.168.0.100', # IP estática en rango público
    MinCount=1,
    MaxCount=1
)
ec2_publica_id = ec2_publica_response['Instances'][0]['InstanceId']

# Instancia en subred privada (Backend / Database Server)
ec2_privada_response = ec2.run_instances(
    ImageId='ami-0360c520857e3138f',  # Amazon Linux 2 AMI
    InstanceType='t2.micro',          # Instancia de capa gratuita
    SubnetId=priv_subnet_id,
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'ec2privada'}]
        }
    ],
    KeyName='vockey',                 # Par de claves para acceso SSH
    SecurityGroupIds=[sg_id],
    PrivateIpAddress='192.168.0.200', # IP estática en rango privado
    MinCount=1,
    MaxCount=1
)
ec2_privada_id = ec2_privada_response['Instances'][0]['InstanceId']
print(f"Instancias desplegadas - Pública: {ec2_publica_id}, Privada: {ec2_privada_id}")

# ========== CONFIGURACIÓN DE NAT GATEWAY ==========
# Permite conectividad de salida para instancias en subredes privadas
print("Configurando NAT Gateway para conectividad de salida desde subred privada...")

# Asignación de Elastic IP para el NAT Gateway (IP pública estática)
eip_response = ec2.allocate_address(Domain='vpc')
eip_alloc_id = eip_response['AllocationId']
print(f"Elastic IP asignada: {eip_alloc_id}")

# Creación del NAT Gateway en la subred pública
nat_gw_response = ec2.create_nat_gateway(
    SubnetId=pub_subnet_id,           # Debe estar en subred pública
    AllocationId=eip_alloc_id,        # EIP previamente asignada
    TagSpecifications=[
        {
            'ResourceType': 'natgateway',
            'Tags': [{'Key': 'Name', 'Value': 'NAT-Publica'}]
        }
    ]
)
nat_gw_id = nat_gw_response['NatGateway']['NatGatewayId']
print(f"NAT Gateway {nat_gw_id} creado, esperando disponibilidad...")

# Espera síncrona hasta que el NAT Gateway esté operativo (3-5 minutos)
waiter = ec2.get_waiter('nat_gateway_available')
waiter.wait(NatGatewayIds=[nat_gw_id])
print("NAT Gateway operativo y disponible para enrutamiento")

# ========== CONFIGURACIÓN DE ENRUTAMIENTO PRIVADO ==========
# Tabla de rutas para tráfico de salida desde subred privada vía NAT Gateway
print("Configurando enrutamiento privado a través de NAT Gateway...")
rt_private_response = ec2.create_route_table(VpcId=vpc_id)
rt_private_id = rt_private_response['RouteTable']['RouteTableId']

# Asociación de la tabla de rutas privada con la subred privada
ec2.associate_route_table(
    SubnetId=priv_subnet_id,
    RouteTableId=rt_private_id
)

# Ruta por defecto dirigiendo tráfico externo al NAT Gateway
ec2.create_route(
    RouteTableId=rt_private_id,
    DestinationCidrBlock='0.0.0.0/0',  # Ruta por defecto para Internet
    NatGatewayId=nat_gw_id             # Enrutamiento vía NAT Gateway
)
print(f"Enrutamiento privado configurado - Tabla: {rt_private_id}")

# ========== RESUMEN DE INFRAESTRUCTURA DESPLEGADA ==========
print("\n" + "="*60)
print("    INFRAESTRUCTURA AWS DESPLEGADA EXITOSAMENTE")
print("="*60)
print(f"VPC ID:                    {vpc_id}")
print(f"Subred Pública ID:         {pub_subnet_id}")
print(f"Subred Privada ID:         {priv_subnet_id}")
print(f"Internet Gateway ID:       {igw_id}")
print(f"Security Group ID:         {sg_id}")
print(f"Instancia Pública ID:      {ec2_publica_id}")
print(f"Instancia Privada ID:      {ec2_privada_id}")
print(f"NAT Gateway ID:            {nat_gw_id}")
print(f"Tabla Rutas Pública ID:    {rt_public_id}")
print(f"Tabla Rutas Privada ID:    {rt_private_id}")
print(f"Elastic IP Allocation ID:  {eip_alloc_id}")
print("="*60)
print("Arquitectura de red híbrida con NAT Gateway desplegada")
print("Conectividad: Pública (bidireccional) | Privada (solo salida)")
print("="*60)