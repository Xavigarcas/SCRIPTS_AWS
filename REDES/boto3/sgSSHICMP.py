#!/usr/bin/env python3
"""
Script de automatización para crear infraestructura de red AWS con NAT Gateway
Implementa una arquitectura de red híbrida con subredes públicas y privadas
Utiliza boto3 SDK para interactuar con los servicios de AWS EC2
"""
import boto3

# Inicialización del cliente EC2 con configuración por defecto
ec2 = boto3.client('ec2')

# ========== CONFIGURACIÓN DE SECURITY GROUPS ==========
# Firewall a nivel de instancia con reglas de entrada específicas
print("Creando Security Group con políticas de acceso SSH e ICMP...")

# NOTA: vpc_id debe ser definido previamente ejecutando vpc.py
# vpc_id = 'vpc-xxxxxxxxx'  # Descomenta y asigna el VPC ID

sg_response = ec2.create_security_group(
    GroupName='SG-SSH-ICMP',
    Description='Permite SSH (puerto 22) y ping (ICMP) desde cualquier origen',
    VpcId=vpc_id  # Variable debe existir del script vpc.py
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
