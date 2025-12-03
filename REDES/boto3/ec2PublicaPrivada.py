#!/usr/bin/env python3
"""
Script de automatización para crear infraestructura de red AWS con NAT Gateway
Implementa una arquitectura de red híbrida con subredes públicas y privadas
Utiliza boto3 SDK para interactuar con los servicios de AWS EC2
"""
import boto3

# Inicialización del cliente EC2 con configuración por defecto
ec2 = boto3.client('ec2')

print("Desplegando instancias EC2 en arquitectura multi-tier...")

# Instancia pública
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

# Instancia privada
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
print(f"Instancias desplegadas - Pública: {ec2_publica_id}, Privada: {ec2_privada_id}")
