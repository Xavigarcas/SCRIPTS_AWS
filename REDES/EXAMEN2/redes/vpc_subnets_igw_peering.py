#!/usr/bin/env python3
import boto3

# Crear clientes para ambas regiones
ec2_east = boto3.client('ec2', region_name='us-east-1')
ec2_west = boto3.client('ec2', region_name='us-west-2')

# Crear VPCs
vpc1 = ec2_east.create_vpc(CidrBlock='192.168.0.0/20')['Vpc']['VpcId']
vpc2 = ec2_west.create_vpc(CidrBlock='10.0.0.0/20')['Vpc']['VpcId']

# Crear subredes para VPC1 (us-east-1)
subnet_pub_vpc1 = ec2_east.create_subnet(VpcId=vpc1, CidrBlock='192.168.1.0/24', AvailabilityZone='us-east-1a')['Subnet']['SubnetId']
subnet_priv_vpc1 = ec2_east.create_subnet(VpcId=vpc1, CidrBlock='192.168.2.0/24', AvailabilityZone='us-east-1b')['Subnet']['SubnetId']

# Crear subredes para VPC2 (us-west-2)
subnet_pub_vpc2 = ec2_west.create_subnet(VpcId=vpc2, CidrBlock='10.0.1.0/24', AvailabilityZone='us-west-2a')['Subnet']['SubnetId']
subnet_priv_vpc2 = ec2_west.create_subnet(VpcId=vpc2, CidrBlock='10.0.2.0/24', AvailabilityZone='us-west-2b')['Subnet']['SubnetId']

# Crear Internet Gateways
igw1 = ec2_east.create_internet_gateway()['InternetGateway']['InternetGatewayId']
igw2 = ec2_west.create_internet_gateway()['InternetGateway']['InternetGatewayId']

# Asociar IGWs a VPCs
ec2_east.attach_internet_gateway(InternetGatewayId=igw1, VpcId=vpc1)
ec2_west.attach_internet_gateway(InternetGatewayId=igw2, VpcId=vpc2)

# Crear tablas de rutas públicas
rt_pub_vpc1 = ec2_east.create_route_table(VpcId=vpc1)['RouteTable']['RouteTableId']
rt_pub_vpc2 = ec2_west.create_route_table(VpcId=vpc2)['RouteTable']['RouteTableId']

# Asociar subredes públicas a tablas de rutas
ec2_east.associate_route_table(SubnetId=subnet_pub_vpc1, RouteTableId=rt_pub_vpc1)
ec2_west.associate_route_table(SubnetId=subnet_pub_vpc2, RouteTableId=rt_pub_vpc2)

# Crear rutas hacia Internet
ec2_east.create_route(RouteTableId=rt_pub_vpc1, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw1)
ec2_west.create_route(RouteTableId=rt_pub_vpc2, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw2)

# Crear peering connection
peer = ec2_east.create_vpc_peering_connection(VpcId=vpc1, PeerVpcId=vpc2, PeerRegion='us-west-2')['VpcPeeringConnection']['VpcPeeringConnectionId']

# Aceptar peering
ec2_west.accept_vpc_peering_connection(VpcPeeringConnectionId=peer)

# Obtener tablas de rutas por defecto
rt1 = ec2_east.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc1]}])['RouteTables'][0]['RouteTableId']
rt2 = ec2_west.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc2]}])['RouteTables'][0]['RouteTableId']

# Crear rutas de peering en tablas por defecto
ec2_east.create_route(RouteTableId=rt1, DestinationCidrBlock='10.0.0.0/20', VpcPeeringConnectionId=peer)
ec2_west.create_route(RouteTableId=rt2, DestinationCidrBlock='192.168.0.0/20', VpcPeeringConnectionId=peer)

# Crear rutas de peering en tablas públicas
ec2_east.create_route(RouteTableId=rt_pub_vpc1, DestinationCidrBlock='10.0.0.0/20', VpcPeeringConnectionId=peer)
ec2_west.create_route(RouteTableId=rt_pub_vpc2, DestinationCidrBlock='192.168.0.0/20', VpcPeeringConnectionId=peer)

print(f"Peering creado: {peer}")
print(f"VPC1: {vpc1} - Subnet Pública: {subnet_pub_vpc1} - Subnet Privada: {subnet_priv_vpc1}")
print(f"VPC2: {vpc2} - Subnet Pública: {subnet_pub_vpc2} - Subnet Privada: {subnet_priv_vpc2}")