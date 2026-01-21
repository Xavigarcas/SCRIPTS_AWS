#!/usr/bin/env python3

import boto3

def main():
    # IDs de las VPCs existentes (reemplaza con tus IDs reales)
    VPC1 = "vpc-xxxxxxxxx"  # VPC en us-east-1
    VPC2 = "vpc-yyyyyyyyy"  # VPC en us-west-2
    
    # Clientes de boto3
    ec2_east = boto3.client('ec2', region_name='us-east-1')
    ec2_west = boto3.client('ec2', region_name='us-west-2')
    
    # Crear peering
    peer_response = ec2_east.create_vpc_peering_connection(
        VpcId=VPC1,
        PeerVpcId=VPC2,
        PeerRegion='us-west-2'
    )
    peer_id = peer_response['VpcPeeringConnection']['VpcPeeringConnectionId']
    
    # Aceptar peering
    ec2_west.accept_vpc_peering_connection(VpcPeeringConnectionId=peer_id)
    
    # Obtener route tables
    rt1_response = ec2_east.describe_route_tables(
        Filters=[{'Name': 'vpc-id', 'Values': [VPC1]}]
    )
    rt1 = rt1_response['RouteTables'][0]['RouteTableId']
    
    rt2_response = ec2_west.describe_route_tables(
        Filters=[{'Name': 'vpc-id', 'Values': [VPC2]}]
    )
    rt2 = rt2_response['RouteTables'][0]['RouteTableId']
    
    # Crear rutas (ajusta los CIDR blocks según tus VPCs)
    ec2_east.create_route(
        RouteTableId=rt1,
        DestinationCidrBlock='10.0.0.0/20',
        VpcPeeringConnectionId=peer_id
    )
    
    ec2_west.create_route(
        RouteTableId=rt2,
        DestinationCidrBlock='192.168.0.0/20',
        VpcPeeringConnectionId=peer_id
    )
    
    print(f"Peering creado: {peer_id}")

if __name__ == "__main__":
    main()