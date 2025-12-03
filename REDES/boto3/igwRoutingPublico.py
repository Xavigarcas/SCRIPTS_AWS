#!/usr/bin/env python3
"""
Script de automatización para crear infraestructura de red AWS con NAT Gateway
Implementa una arquitectura de red híbrida con subredes públicas y privadas
Utiliza boto3 SDK para interactuar con los servicios de AWS EC2
"""
import boto3

# Inicialización del cliente EC2 con configuración por defecto
ec2 = boto3.client('ec2')

print("Desplegando Internet Gateway para conectividad externa...")
igw_response = ec2.create_internet_gateway()
igw_id = igw_response['InternetGateway']['InternetGatewayId']

ec2.attach_internet_gateway(
    InternetGatewayId=igw_id,
    VpcId=vpc_id
)
print(f"Internet Gateway {igw_id} asociado exitosamente a VPC")

print("Configurando tabla de enrutamiento para subred pública...")
rt_public_response = ec2.create_route_table(VpcId=vpc_id)
rt_public_id = rt_public_response['RouteTable']['RouteTableId']

ec2.create_route(
    RouteTableId=rt_public_id,
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=igw_id
)

ec2.associate_route_table(
    SubnetId=pub_subnet_id,
    RouteTableId=rt_public_id
)

ec2.modify_subnet_attribute(
    SubnetId=pub_subnet_id,
    MapPublicIpOnLaunch={'Value': True}
)
print(f"Enrutamiento público configurado - Tabla: {rt_public_id}")
