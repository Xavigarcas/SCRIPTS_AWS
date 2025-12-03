#!/usr/bin/env python3
"""
Script de automatización para crear infraestructura de red AWS con NAT Gateway
Implementa una arquitectura de red híbrida con subredes públicas y privadas
Utiliza boto3 SDK para interactuar con los servicios de AWS EC2
"""
import boto3

# Inicialización del cliente EC2 con configuración por defecto
ec2 = boto3.client('ec2')

print("Creando VPC con segmentación de red /24...")
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
print(f"VPC creada exitosamente: {vpc_id}")