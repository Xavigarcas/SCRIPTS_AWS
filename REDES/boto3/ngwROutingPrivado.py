#!/usr/bin/env python3
"""
Script de automatización para crear infraestructura de red AWS con NAT Gateway
Implementa una arquitectura de red híbrida con subredes públicas y privadas
Utiliza boto3 SDK para interactuar con los servicios de AWS EC2
"""
import boto3

# Inicialización del cliente EC2 con configuración por defecto
ec2 = boto3.client('ec2')

print("Configurando NAT Gateway para conectividad de salida desde subred privada...")

# Elastic IP
eip_response = ec2.allocate_address(Domain='vpc')
eip_alloc_id = eip_response['AllocationId']
print(f"Elastic IP asignada: {eip_alloc_id}")

# NAT Gateway en subred pública
nat_gw_response = ec2.create_nat_gateway(
    SubnetId=pub_subnet_id,
    AllocationId=eip_alloc_id,
    TagSpecifications=[ ... ]
)
nat_gw_id = nat_gw_response['NatGateway']['NatGatewayId']
print(f"NAT Gateway {nat_gw_id} creado, esperando disponibilidad...")

waiter = ec2.get_waiter('nat_gateway_available')
waiter.wait(NatGatewayIds=[nat_gw_id])
print("NAT Gateway operativo y disponible para enrutamiento")

print("Configurando enrutamiento privado a través de NAT Gateway...")
rt_private_response = ec2.create_route_table(VpcId=vpc_id)
rt_private_id = rt_private_response['RouteTable']['RouteTableId']

ec2.associate_route_table(
    SubnetId=priv_subnet_id,
    RouteTableId=rt_private_id
)

ec2.create_route(
    RouteTableId=rt_private_id,
    DestinationCidrBlock='0.0.0.0/0',
    NatGatewayId=nat_gw_id
)
print(f"Enrutamiento privado configurado - Tabla: {rt_private_id}")
