#!/usr/bin/env python3

import boto3
import time
import sys

def main():
    print("==========================================")
    print("AWS Multi-Region Infrastructure Setup")
    print("Transit Gateway + VPC Peering")
    print("==========================================")
    
    # Variables de configuración
    REGION_EAST = "us-east-1"
    REGION_WEST = "us-west-2"
    
    # Clientes de boto3
    ec2_east = boto3.client('ec2', region_name=REGION_EAST)
    ec2_west = boto3.client('ec2', region_name=REGION_WEST)
    sts = boto3.client('sts')
    
    try:
        # ==========================================
        # PARTE 1: CONFIGURACIÓN US-EAST-1
        # ==========================================
        
        print("\n=== CONFIGURANDO REGIÓN US-EAST-1 ===\n")
        
        # Crear VPC 1 en US-EAST-1
        print("Creando VPC 1 en us-east-1 (10.1.0.0/16)...")
        vpc1_east_response = ec2_east.create_vpc(
            CidrBlock='10.1.0.0/16',
            TagSpecifications=[{
                'ResourceType': 'vpc',
                'Tags': [{'Key': 'Name', 'Value': 'VPC-US-EAST-1-A'}]
            }]
        )
        vpc1_east = vpc1_east_response['Vpc']['VpcId']
        print(f"VPC 1 US-EAST-1 creada: {vpc1_east}")
        
        # Habilitar DNS en VPC 1
        ec2_east.modify_vpc_attribute(VpcId=vpc1_east, EnableDnsHostnames={'Value': True})
        ec2_east.modify_vpc_attribute(VpcId=vpc1_east, EnableDnsSupport={'Value': True})
        
        # Crear VPC 2 en US-EAST-1
        print("Creando VPC 2 en us-east-1 (10.2.0.0/16)...")
        vpc2_east_response = ec2_east.create_vpc(
            CidrBlock='10.2.0.0/16',
            TagSpecifications=[{
                'ResourceType': 'vpc',
                'Tags': [{'Key': 'Name', 'Value': 'VPC-US-EAST-1-B'}]
            }]
        )
        vpc2_east = vpc2_east_response['Vpc']['VpcId']
        print(f"VPC 2 US-EAST-1 creada: {vpc2_east}")
        
        ec2_east.modify_vpc_attribute(VpcId=vpc2_east, EnableDnsHostnames={'Value': True})
        ec2_east.modify_vpc_attribute(VpcId=vpc2_east, EnableDnsSupport={'Value': True})
        
        # Crear Subnets en US-EAST-1
        print("Creando subnets en us-east-1...")
        subnet1_east_response = ec2_east.create_subnet(
            VpcId=vpc1_east,
            CidrBlock='10.1.0.0/24',
            AvailabilityZone=f'{REGION_EAST}a',
            TagSpecifications=[{
                'ResourceType': 'subnet',
                'Tags': [{'Key': 'Name', 'Value': 'Subnet-Public-US-EAST-1-A'}]
            }]
        )
        subnet1_east = subnet1_east_response['Subnet']['SubnetId']
        print(f"Subnet 1 US-EAST-1: {subnet1_east}")
        
        subnet2_east_response = ec2_east.create_subnet(
            VpcId=vpc2_east,
            CidrBlock='10.2.0.0/24',
            AvailabilityZone=f'{REGION_EAST}b',
            TagSpecifications=[{
                'ResourceType': 'subnet',
                'Tags': [{'Key': 'Name', 'Value': 'Subnet-Public-US-EAST-1-B'}]
            }]
        )
        subnet2_east = subnet2_east_response['Subnet']['SubnetId']
        print(f"Subnet 2 US-EAST-1: {subnet2_east}")
        
        # Auto-asignar IPs públicas
        ec2_east.modify_subnet_attribute(SubnetId=subnet1_east, MapPublicIpOnLaunch={'Value': True})
        ec2_east.modify_subnet_attribute(SubnetId=subnet2_east, MapPublicIpOnLaunch={'Value': True})
        
        # Crear Internet Gateways en US-EAST-1
        print("Creando Internet Gateways en us-east-1...")
        igw1_east_response = ec2_east.create_internet_gateway(
            TagSpecifications=[{
                'ResourceType': 'internet-gateway',
                'Tags': [{'Key': 'Name', 'Value': 'IGW-US-EAST-1-A'}]
            }]
        )
        igw1_east = igw1_east_response['InternetGateway']['InternetGatewayId']
        ec2_east.attach_internet_gateway(VpcId=vpc1_east, InternetGatewayId=igw1_east)
        print(f"IGW 1: {igw1_east}")
        
        igw2_east_response = ec2_east.create_internet_gateway(
            TagSpecifications=[{
                'ResourceType': 'internet-gateway',
                'Tags': [{'Key': 'Name', 'Value': 'IGW-US-EAST-1-B'}]
            }]
        )
        igw2_east = igw2_east_response['InternetGateway']['InternetGatewayId']
        ec2_east.attach_internet_gateway(VpcId=vpc2_east, InternetGatewayId=igw2_east)
        print(f"IGW 2: {igw2_east}")
        
        # Crear Transit Gateway en US-EAST-1
        print("Creando Transit Gateway en us-east-1...")
        tgw_east_response = ec2_east.create_transit_gateway(
            Description='Transit Gateway US-EAST-1',
            Options={
                'AmazonSideAsn': 64512,
                'DefaultRouteTableAssociation': 'enable',
                'DefaultRouteTablePropagation': 'enable',
                'DnsSupport': 'enable',
                'VpnEcmpSupport': 'enable'
            },
            TagSpecifications=[{
                'ResourceType': 'transit-gateway',
                'Tags': [{'Key': 'Name', 'Value': 'TGW-US-EAST-1'}]
            }]
        )
        tgw_east = tgw_east_response['TransitGateway']['TransitGatewayId']
        print(f"Transit Gateway US-EAST-1: {tgw_east}")
        
        print("Esperando a que el Transit Gateway esté disponible (2 minutos)...")
        time.sleep(120)
        print("Transit Gateway disponible!")
        
        # Crear Transit Gateway Attachments en US-EAST-1
        print("Creando Transit Gateway Attachments en us-east-1...")
        tgw_attach1_east_response = ec2_east.create_transit_gateway_vpc_attachment(
            TransitGatewayId=tgw_east,
            VpcId=vpc1_east,
            SubnetIds=[subnet1_east],
            TagSpecifications=[{
                'ResourceType': 'transit-gateway-attachment',
                'Tags': [{'Key': 'Name', 'Value': 'TGW-Attach-VPC-US-EAST-1-A'}]
            }]
        )
        tgw_attach1_east = tgw_attach1_east_response['TransitGatewayVpcAttachment']['TransitGatewayAttachmentId']
        print(f"TGW Attachment 1: {tgw_attach1_east}")
        
        tgw_attach2_east_response = ec2_east.create_transit_gateway_vpc_attachment(
            TransitGatewayId=tgw_east,
            VpcId=vpc2_east,
            SubnetIds=[subnet2_east],
            TagSpecifications=[{
                'ResourceType': 'transit-gateway-attachment',
                'Tags': [{'Key': 'Name', 'Value': 'TGW-Attach-VPC-US-EAST-1-B'}]
            }]
        )
        tgw_attach2_east = tgw_attach2_east_response['TransitGatewayVpcAttachment']['TransitGatewayAttachmentId']
        print(f"TGW Attachment 2: {tgw_attach2_east}")
        
        time.sleep(30)
        
        # ==========================================
        # PARTE 2: CONFIGURACIÓN US-WEST-2
        # ==========================================
        
        print("\n=== CONFIGURANDO REGIÓN US-WEST-2 ===\n")
        
        # Crear VPC 1 en US-WEST-2
        print("Creando VPC 1 en us-west-2 (192.168.0.0/16)...")
        vpc1_west_response = ec2_west.create_vpc(
            CidrBlock='192.168.0.0/16',
            TagSpecifications=[{
                'ResourceType': 'vpc',
                'Tags': [{'Key': 'Name', 'Value': 'VPC-US-WEST-2-A'}]
            }]
        )
        vpc1_west = vpc1_west_response['Vpc']['VpcId']
        print(f"VPC 1 US-WEST-2 creada: {vpc1_west}")
        
        ec2_west.modify_vpc_attribute(VpcId=vpc1_west, EnableDnsHostnames={'Value': True})
        ec2_west.modify_vpc_attribute(VpcId=vpc1_west, EnableDnsSupport={'Value': True})
        
        # Crear VPC 2 en US-WEST-2
        print("Creando VPC 2 en us-west-2 (192.224.0.0/16)...")
        vpc2_west_response = ec2_west.create_vpc(
            CidrBlock='192.224.0.0/16',
            TagSpecifications=[{
                'ResourceType': 'vpc',
                'Tags': [{'Key': 'Name', 'Value': 'VPC-US-WEST-2-B'}]
            }]
        )
        vpc2_west = vpc2_west_response['Vpc']['VpcId']
        print(f"VPC 2 US-WEST-2 creada: {vpc2_west}")
        
        ec2_west.modify_vpc_attribute(VpcId=vpc2_west, EnableDnsHostnames={'Value': True})
        ec2_west.modify_vpc_attribute(VpcId=vpc2_west, EnableDnsSupport={'Value': True})
        
        # Crear Subnets en US-WEST-2
        print("Creando subnets en us-west-2...")
        subnet1_west_response = ec2_west.create_subnet(
            VpcId=vpc1_west,
            CidrBlock='192.168.1.0/24',
            AvailabilityZone=f'{REGION_WEST}a',
            TagSpecifications=[{
                'ResourceType': 'subnet',
                'Tags': [{'Key': 'Name', 'Value': 'Subnet-Public-US-WEST-2-A'}]
            }]
        )
        subnet1_west = subnet1_west_response['Subnet']['SubnetId']
        print(f"Subnet 1 US-WEST-2: {subnet1_west}")
        
        subnet2_west_response = ec2_west.create_subnet(
            VpcId=vpc2_west,
            CidrBlock='192.224.1.0/24',
            AvailabilityZone=f'{REGION_WEST}b',
            TagSpecifications=[{
                'ResourceType': 'subnet',
                'Tags': [{'Key': 'Name', 'Value': 'Subnet-Public-US-WEST-2-B'}]
            }]
        )
        subnet2_west = subnet2_west_response['Subnet']['SubnetId']
        print(f"Subnet 2 US-WEST-2: {subnet2_west}")
        
        ec2_west.modify_subnet_attribute(SubnetId=subnet1_west, MapPublicIpOnLaunch={'Value': True})
        ec2_west.modify_subnet_attribute(SubnetId=subnet2_west, MapPublicIpOnLaunch={'Value': True})
        
        # Crear Internet Gateways en US-WEST-2
        print("Creando Internet Gateways en us-west-2...")
        igw1_west_response = ec2_west.create_internet_gateway(
            TagSpecifications=[{
                'ResourceType': 'internet-gateway',
                'Tags': [{'Key': 'Name', 'Value': 'IGW-US-WEST-2-A'}]
            }]
        )
        igw1_west = igw1_west_response['InternetGateway']['InternetGatewayId']
        ec2_west.attach_internet_gateway(VpcId=vpc1_west, InternetGatewayId=igw1_west)
        print(f"IGW 1: {igw1_west}")
        
        igw2_west_response = ec2_west.create_internet_gateway(
            TagSpecifications=[{
                'ResourceType': 'internet-gateway',
                'Tags': [{'Key': 'Name', 'Value': 'IGW-US-WEST-2-B'}]
            }]
        )
        igw2_west = igw2_west_response['InternetGateway']['InternetGatewayId']
        ec2_west.attach_internet_gateway(VpcId=vpc2_west, InternetGatewayId=igw2_west)
        print(f"IGW 2: {igw2_west}")
        
        # Crear Transit Gateway en US-WEST-2
        print("Creando Transit Gateway en us-west-2...")
        tgw_west_response = ec2_west.create_transit_gateway(
            Description='Transit Gateway US-WEST-2',
            Options={
                'AmazonSideAsn': 64513,
                'DefaultRouteTableAssociation': 'enable',
                'DefaultRouteTablePropagation': 'enable',
                'DnsSupport': 'enable',
                'VpnEcmpSupport': 'enable'
            },
            TagSpecifications=[{
                'ResourceType': 'transit-gateway',
                'Tags': [{'Key': 'Name', 'Value': 'TGW-US-WEST-2'}]
            }]
        )
        tgw_west = tgw_west_response['TransitGateway']['TransitGatewayId']
        print(f"Transit Gateway US-WEST-2: {tgw_west}")
        
        print("Esperando a que el Transit Gateway esté disponible (2 minutos)...")
        time.sleep(120)
        print("Transit Gateway disponible!")
        
        # Crear Transit Gateway Attachments en US-WEST-2
        print("Creando Transit Gateway Attachments en us-west-2...")
        tgw_attach1_west_response = ec2_west.create_transit_gateway_vpc_attachment(
            TransitGatewayId=tgw_west,
            VpcId=vpc1_west,
            SubnetIds=[subnet1_west],
            TagSpecifications=[{
                'ResourceType': 'transit-gateway-attachment',
                'Tags': [{'Key': 'Name', 'Value': 'TGW-Attach-VPC-US-WEST-2-A'}]
            }]
        )
        tgw_attach1_west = tgw_attach1_west_response['TransitGatewayVpcAttachment']['TransitGatewayAttachmentId']
        print(f"TGW Attachment 1: {tgw_attach1_west}")
        
        tgw_attach2_west_response = ec2_west.create_transit_gateway_vpc_attachment(
            TransitGatewayId=tgw_west,
            VpcId=vpc2_west,
            SubnetIds=[subnet2_west],
            TagSpecifications=[{
                'ResourceType': 'transit-gateway-attachment',
                'Tags': [{'Key': 'Name', 'Value': 'TGW-Attach-VPC-US-WEST-2-B'}]
            }]
        )
        tgw_attach2_west = tgw_attach2_west_response['TransitGatewayVpcAttachment']['TransitGatewayAttachmentId']
        print(f"TGW Attachment 2: {tgw_attach2_west}")
        
        time.sleep(30)
        
        # ==========================================
        # PARTE 3: TRANSIT GATEWAY PEERING
        # ==========================================
        
        print("\n=== CREANDO TRANSIT GATEWAY PEERING ===\n")
        
        # Obtener Account ID automáticamente
        account_id = sts.get_caller_identity()['Account']
        print(f"Account ID: {account_id}")
        
        # Crear Peering Request desde US-EAST-1 hacia US-WEST-2
        print("Creando Transit Gateway Peering Request...")
        peering_response = ec2_east.create_transit_gateway_peering_attachment(
            TransitGatewayId=tgw_east,
            PeerTransitGatewayId=tgw_west,
            PeerAccountId=account_id,
            PeerRegion=REGION_WEST,
            TagSpecifications=[{
                'ResourceType': 'transit-gateway-attachment',
                'Tags': [{'Key': 'Name', 'Value': 'TGW-Peering-EAST-WEST'}]
            }]
        )
        peering_id = peering_response['TransitGatewayPeeringAttachment']['TransitGatewayAttachmentId']
        print(f"Peering ID: {peering_id}")
        
        print("Esperando a que el peering esté pendiente de aceptación...")
        time.sleep(120)
        
        # Aceptar Peering desde US-WEST-2
        print("Aceptando Transit Gateway Peering desde us-west-2...")
        ec2_west.accept_transit_gateway_peering_attachment(TransitGatewayAttachmentId=peering_id)
        
        print("Esperando a que el peering esté disponible (3 minutos)...")
        time.sleep(200)
        
        # ==========================================
        # PARTE 4: CONFIGURAR ROUTE TABLES
        # ==========================================
        
        print("\n=== CONFIGURANDO ROUTE TABLES ===\n")
        
        # Obtener Route Tables
        rt1_east = ec2_east.describe_route_tables(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc1_east]}]
        )['RouteTables'][0]['RouteTableId']
        
        rt2_east = ec2_east.describe_route_tables(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc2_east]}]
        )['RouteTables'][0]['RouteTableId']
        
        rt1_west = ec2_west.describe_route_tables(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc1_west]}]
        )['RouteTables'][0]['RouteTableId']
        
        rt2_west = ec2_west.describe_route_tables(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc2_west]}]
        )['RouteTables'][0]['RouteTableId']
        
        # Routes para US-EAST-1 VPC 1
        print("Configurando rutas para VPC1 US-EAST-1...")
        ec2_east.create_route(RouteTableId=rt1_east, DestinationCidrBlock='10.2.0.0/16', TransitGatewayId=tgw_east)
        ec2_east.create_route(RouteTableId=rt1_east, DestinationCidrBlock='192.168.0.0/16', TransitGatewayId=tgw_east)
        ec2_east.create_route(RouteTableId=rt1_east, DestinationCidrBlock='192.224.0.0/16', TransitGatewayId=tgw_east)
        ec2_east.create_route(RouteTableId=rt1_east, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw1_east)
        
        # Routes para US-EAST-1 VPC 2
        print("Configurando rutas para VPC2 US-EAST-1...")
        ec2_east.create_route(RouteTableId=rt2_east, DestinationCidrBlock='10.1.0.0/16', TransitGatewayId=tgw_east)
        ec2_east.create_route(RouteTableId=rt2_east, DestinationCidrBlock='192.168.0.0/16', TransitGatewayId=tgw_east)
        ec2_east.create_route(RouteTableId=rt2_east, DestinationCidrBlock='192.224.0.0/16', TransitGatewayId=tgw_east)
        ec2_east.create_route(RouteTableId=rt2_east, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw2_east)
        
        # Routes para US-WEST-2 VPC 1
        print("Configurando rutas para VPC1 US-WEST-2...")
        ec2_west.create_route(RouteTableId=rt1_west, DestinationCidrBlock='192.224.0.0/16', TransitGatewayId=tgw_west)
        ec2_west.create_route(RouteTableId=rt1_west, DestinationCidrBlock='10.0.0.0/8', TransitGatewayId=tgw_west)
        ec2_west.create_route(RouteTableId=rt1_west, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw1_west)
        
        # Routes para US-WEST-2 VPC 2
        print("Configurando rutas para VPC2 US-WEST-2...")
        ec2_west.create_route(RouteTableId=rt2_west, DestinationCidrBlock='192.168.0.0/16', TransitGatewayId=tgw_west)
        ec2_west.create_route(RouteTableId=rt2_west, DestinationCidrBlock='10.0.0.0/8', TransitGatewayId=tgw_west)
        ec2_west.create_route(RouteTableId=rt2_west, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw2_west)
        
        # Obtener Transit Gateway Route Tables
        tgw_rt_east = ec2_east.describe_transit_gateway_route_tables(
            Filters=[{'Name': 'transit-gateway-id', 'Values': [tgw_east]}]
        )['TransitGatewayRouteTables'][0]['TransitGatewayRouteTableId']
        
        tgw_rt_west = ec2_west.describe_transit_gateway_route_tables(
            Filters=[{'Name': 'transit-gateway-id', 'Values': [tgw_west]}]
        )['TransitGatewayRouteTables'][0]['TransitGatewayRouteTableId']
        
        # Rutas en Transit Gateway US-EAST-1
        print("Configurando rutas en Transit Gateway US-EAST-1...")
        ec2_east.create_transit_gateway_route(
            DestinationCidrBlock='192.168.0.0/16',
            TransitGatewayRouteTableId=tgw_rt_east,
            TransitGatewayAttachmentId=peering_id
        )
        ec2_east.create_transit_gateway_route(
            DestinationCidrBlock='192.224.0.0/16',
            TransitGatewayRouteTableId=tgw_rt_east,
            TransitGatewayAttachmentId=peering_id
        )
        
        # Rutas en Transit Gateway US-WEST-2
        print("Configurando rutas en Transit Gateway US-WEST-2...")
        ec2_west.create_transit_gateway_route(
            DestinationCidrBlock='10.0.0.0/8',
            TransitGatewayRouteTableId=tgw_rt_west,
            TransitGatewayAttachmentId=peering_id
        )
        
        # Asociar y propagar peering en ambos Transit Gateways
        print("Asociando peering connection en Transit Gateways...")
        
        # Asociar peering en US-EAST-1
        ec2_east.associate_transit_gateway_route_table(
            TransitGatewayAttachmentId=peering_id,
            TransitGatewayRouteTableId=tgw_rt_east
        )
        
        # Propagar rutas del peering en US-EAST-1
        ec2_east.enable_transit_gateway_route_table_propagation(
            TransitGatewayAttachmentId=peering_id,
            TransitGatewayRouteTableId=tgw_rt_east
        )
        
        # Asociar peering en US-WEST-2
        ec2_west.associate_transit_gateway_route_table(
            TransitGatewayAttachmentId=peering_id,
            TransitGatewayRouteTableId=tgw_rt_west
        )
        
        # Propagar rutas del peering en US-WEST-2
        ec2_west.enable_transit_gateway_route_table_propagation(
            TransitGatewayAttachmentId=peering_id,
            TransitGatewayRouteTableId=tgw_rt_west
        )
        
        # ==========================================
        # RESUMEN DE LA INFRAESTRUCTURA
        # ==========================================
        
        print("\n==========================================")
        print("INFRAESTRUCTURA COMPLETADA EXITOSAMENTE")
        print("==========================================\n")
        print("US-EAST-1 (Norte de Virginia):")
        print(f"  VPC 1: {vpc1_east} (10.1.0.0/16)")
        print(f"    Subnet: {subnet1_east}")
        print(f"  VPC 2: {vpc2_east} (10.2.0.0/16)")
        print(f"    Subnet: {subnet2_east}")
        print(f"  Transit Gateway: {tgw_east}\n")
        print("US-WEST-2 (Oregón):")
        print(f"  VPC 1: {vpc1_west} (192.168.0.0/16)")
        print(f"    Subnet: {subnet1_west} (192.168.1.0/24)")
        print(f"  VPC 2: {vpc2_west} (192.224.0.0/16)")
        print(f"    Subnet: {subnet2_west} (192.224.1.0/24)")
        print(f"  Transit Gateway: {tgw_west}\n")
        print(f"Transit Gateway Peering: {peering_id}\n")
        print("==========================================")
        print("PRÓXIMOS PASOS:")
        print("==========================================")
        print("1. Infraestructura de red lista para desplegar instancias")
        print("2. Verifica las tablas de rutas en la consola de AWS")
        print("3. Verifica los Transit Gateways y el Peering Connection\n")
        print("==========================================")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()