#!/usr/bin/env python3
"""
Script de automatización para crear infraestructura de red AWS con NAT Gateway
Implementa una arquitectura de red híbrida con subredes públicas y privadas
Utiliza boto3 SDK para interactuar con los servicios de AWS EC2
"""
import boto3

# Inicialización del cliente EC2 con configuración por defecto
ec2 = boto3.client('ec2')

# ========== CREACIÓN DE SUBREDES CON SEGMENTACIÓN CIDR ==========
# NOTA: vpc_id debe ser definido previamente ejecutando vpc.py
# vpc_id = 'vpc-xxxxxxxxx'  # Descomenta y asigna el VPC ID

# Subred pública: 192.168.0.0/25 (128 IPs: .0-.127)
print("Creando subred pública con enrutamiento directo a Internet...")
pub_subnet_response = ec2.create_subnet(
    VpcId=vpc_id,  # Variable debe existir del script vpc.py
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
    VpcId=vpc_id,  # Variable debe existir del script vpc.py
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
