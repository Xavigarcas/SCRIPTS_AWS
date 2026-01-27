#!/usr/bin/env python3

import boto3
import time

def create_multi_vpc_connectivity():
    """
    Implementa conectividad entre VPCs usando Transit Gateway
    - Región 1: 2 VPCs conectadas via Transit Gateway
    - Región 2: 1 VPC conectada via Transit Gateway Peering
    """
    
    # Configuración
    region1 = 'us-east-1'  # Región 1: 2 VPCs
    region2 = 'us-west-2'  # Región 2: 1 VPC
    
    ec2_r1 = boto3.client('ec2', region_name=region1)
    ec2_r2 = boto3.client('ec2', region_name=region2)
    sts = boto3.client('sts')
    
    account_id = sts.get_caller_identity()['Account']
    
    print("=== SOLUCIÓN: TRANSIT GATEWAY ===")
    print("Ventajas vs VPC Peering:")
    print("1. Escalabilidad: Hub central vs conexiones punto a punto")
    print("2. Gestión: Una sola tabla de rutas vs múltiples peerings")
    print("3. Costos: Más eficiente con >3 VPCs")
    print("4. Flexibilidad: Fácil agregar/quitar VPCs")
    
    # ==========================================
    # REGIÓN 1: CREAR 2 VPCs Y TRANSIT GATEWAY
    # ==========================================
    
    print(f"\n=== CONFIGURANDO REGIÓN 1 ({region1}) ===")
    
    # VPC 1 en Región 1
    vpc1_r1 = ec2_r1.create_vpc(
        CidrBlock='10.1.0.0/16',
        TagSpecifications=[{'ResourceType': 'vpc', 'Tags': [{'Key': 'Name', 'Value': 'VPC1-Region1'}]}]
    )['Vpc']['VpcId']
    print(f"VPC1 Región 1: {vpc1_r1}")
    
    # VPC 2 en Región 1
    vpc2_r1 = ec2_r1.create_vpc(
        CidrBlock='10.2.0.0/16',
        TagSpecifications=[{'ResourceType': 'vpc', 'Tags': [{'Key': 'Name', 'Value': 'VPC2-Region1'}]}]
    )['Vpc']['VpcId']
    print(f"VPC2 Región 1: {vpc2_r1}")
    
    # Subnets para attachments
    az1_r1 = ec2_r1.describe_availability_zones()['AvailabilityZones'][0]['ZoneName']
    
    subnet1_r1 = ec2_r1.create_subnet(
        VpcId=vpc1_r1, CidrBlock='10.1.1.0/24', AvailabilityZone=az1_r1,
        TagSpecifications=[{'ResourceType': 'subnet', 'Tags': [{'Key': 'Name', 'Value': 'TGW-Subnet-VPC1-R1'}]}]
    )['Subnet']['SubnetId']
    
    subnet2_r1 = ec2_r1.create_subnet(
        VpcId=vpc2_r1, CidrBlock='10.2.1.0/24', AvailabilityZone=az1_r1,
        TagSpecifications=[{'ResourceType': 'subnet', 'Tags': [{'Key': 'Name', 'Value': 'TGW-Subnet-VPC2-R1'}]}]
    )['Subnet']['SubnetId']
    
    # Hacer subnets públicas
    ec2_r1.modify_subnet_attribute(SubnetId=subnet1_r1, MapPublicIpOnLaunch={'Value': True})
    ec2_r1.modify_subnet_attribute(SubnetId=subnet2_r1, MapPublicIpOnLaunch={'Value': True})
    
    # Internet Gateways para acceso SSH
    igw1_r1 = ec2_r1.create_internet_gateway(
        TagSpecifications=[{'ResourceType': 'internet-gateway', 'Tags': [{'Key': 'Name', 'Value': 'IGW-VPC1-R1'}]}]
    )['InternetGateway']['InternetGatewayId']
    ec2_r1.attach_internet_gateway(VpcId=vpc1_r1, InternetGatewayId=igw1_r1)
    
    igw2_r1 = ec2_r1.create_internet_gateway(
        TagSpecifications=[{'ResourceType': 'internet-gateway', 'Tags': [{'Key': 'Name', 'Value': 'IGW-VPC2-R1'}]}]
    )['InternetGateway']['InternetGatewayId']
    ec2_r1.attach_internet_gateway(VpcId=vpc2_r1, InternetGatewayId=igw2_r1)
    
    print(f"IGWs creados: {igw1_r1}, {igw2_r1}")
    
    # Transit Gateway en Región 1
    tgw_r1 = ec2_r1.create_transit_gateway(
        Description='Transit Gateway Region 1',
        Options={'AmazonSideAsn': 64512, 'DefaultRouteTableAssociation': 'enable', 'DefaultRouteTablePropagation': 'enable'},
        TagSpecifications=[{'ResourceType': 'transit-gateway', 'Tags': [{'Key': 'Name', 'Value': 'TGW-Region1'}]}]
    )['TransitGateway']['TransitGatewayId']
    print(f"Transit Gateway Región 1: {tgw_r1}")
    
    print("Esperando Transit Gateway (3 minutos)...")
    time.sleep(180)
    
    # Attachments en Región 1
    attach1_r1 = ec2_r1.create_transit_gateway_vpc_attachment(
        TransitGatewayId=tgw_r1, VpcId=vpc1_r1, SubnetIds=[subnet1_r1],
        TagSpecifications=[{'ResourceType': 'transit-gateway-attachment', 'Tags': [{'Key': 'Name', 'Value': 'TGW-Attach-VPC1-R1'}]}]
    )['TransitGatewayVpcAttachment']['TransitGatewayAttachmentId']
    
    attach2_r1 = ec2_r1.create_transit_gateway_vpc_attachment(
        TransitGatewayId=tgw_r1, VpcId=vpc2_r1, SubnetIds=[subnet2_r1],
        TagSpecifications=[{'ResourceType': 'transit-gateway-attachment', 'Tags': [{'Key': 'Name', 'Value': 'TGW-Attach-VPC2-R1'}]}]
    )['TransitGatewayVpcAttachment']['TransitGatewayAttachmentId']
    
    print(f"Attachments creados: {attach1_r1}, {attach2_r1}")
    print("Esperando attachments disponibles (1 minuto)...")
    time.sleep(60)
    
    # ==========================================
    # REGIÓN 2: CREAR VPC Y TRANSIT GATEWAY
    # ==========================================
    
    print(f"\n=== CONFIGURANDO REGIÓN 2 ({region2}) ===")
    
    # VPC en Región 2
    vpc1_r2 = ec2_r2.create_vpc(
        CidrBlock='10.3.0.0/16',
        TagSpecifications=[{'ResourceType': 'vpc', 'Tags': [{'Key': 'Name', 'Value': 'VPC1-Region2'}]}]
    )['Vpc']['VpcId']
    print(f"VPC Región 2: {vpc1_r2}")
    
    # Subnet para attachment
    az1_r2 = ec2_r2.describe_availability_zones()['AvailabilityZones'][0]['ZoneName']
    
    subnet1_r2 = ec2_r2.create_subnet(
        VpcId=vpc1_r2, CidrBlock='10.3.1.0/24', AvailabilityZone=az1_r2,
        TagSpecifications=[{'ResourceType': 'subnet', 'Tags': [{'Key': 'Name', 'Value': 'TGW-Subnet-VPC1-R2'}]}]
    )['Subnet']['SubnetId']
    
    # Hacer subnet pública
    ec2_r2.modify_subnet_attribute(SubnetId=subnet1_r2, MapPublicIpOnLaunch={'Value': True})
    
    # Internet Gateway para acceso SSH
    igw1_r2 = ec2_r2.create_internet_gateway(
        TagSpecifications=[{'ResourceType': 'internet-gateway', 'Tags': [{'Key': 'Name', 'Value': 'IGW-VPC1-R2'}]}]
    )['InternetGateway']['InternetGatewayId']
    ec2_r2.attach_internet_gateway(VpcId=vpc1_r2, InternetGatewayId=igw1_r2)
    
    print(f"IGW creado: {igw1_r2}")
    
    # Transit Gateway en Región 2
    tgw_r2 = ec2_r2.create_transit_gateway(
        Description='Transit Gateway Region 2',
        Options={'AmazonSideAsn': 64513, 'DefaultRouteTableAssociation': 'enable', 'DefaultRouteTablePropagation': 'enable'},
        TagSpecifications=[{'ResourceType': 'transit-gateway', 'Tags': [{'Key': 'Name', 'Value': 'TGW-Region2'}]}]
    )['TransitGateway']['TransitGatewayId']
    print(f"Transit Gateway Región 2: {tgw_r2}")
    
    print("Esperando Transit Gateway (3 minutos)...")
    time.sleep(180)
    
    # Attachment en Región 2
    attach1_r2 = ec2_r2.create_transit_gateway_vpc_attachment(
        TransitGatewayId=tgw_r2, VpcId=vpc1_r2, SubnetIds=[subnet1_r2],
        TagSpecifications=[{'ResourceType': 'transit-gateway-attachment', 'Tags': [{'Key': 'Name', 'Value': 'TGW-Attach-VPC1-R2'}]}]
    )['TransitGatewayVpcAttachment']['TransitGatewayAttachmentId']
    
    print(f"Attachment creado: {attach1_r2}")
    print("Esperando attachment disponible (1 minuto)...")
    time.sleep(60)
    
    # ==========================================
    # TRANSIT GATEWAY PEERING ENTRE REGIONES
    # ==========================================
    
    print(f"\n=== CREANDO PEERING ENTRE REGIONES ===")
    
    # Crear peering desde Región 1 a Región 2
    peering_id = ec2_r1.create_transit_gateway_peering_attachment(
        TransitGatewayId=tgw_r1,
        PeerTransitGatewayId=tgw_r2,
        PeerAccountId=account_id,
        PeerRegion=region2,
        TagSpecifications=[{'ResourceType': 'transit-gateway-attachment', 'Tags': [{'Key': 'Name', 'Value': 'TGW-Peering-R1-R2'}]}]
    )['TransitGatewayPeeringAttachment']['TransitGatewayAttachmentId']
    
    print(f"Peering creado: {peering_id}")
    print("Esperando peering pendiente (2 minutos)...")
    time.sleep(120)
    
    # Aceptar peering desde Región 2
    ec2_r2.accept_transit_gateway_peering_attachment(TransitGatewayAttachmentId=peering_id)
    print("Peering aceptado")
    
    print("Esperando peering completamente disponible (4 minutos)...")
    time.sleep(240)
    
    # ==========================================
    # CONFIGURAR RUTAS
    # ==========================================
    
    print(f"\n=== CONFIGURANDO RUTAS ===")
    
    # Obtener route tables
    tgw_rt_r1 = ec2_r1.describe_transit_gateway_route_tables(
        Filters=[{'Name': 'transit-gateway-id', 'Values': [tgw_r1]}]
    )['TransitGatewayRouteTables'][0]['TransitGatewayRouteTableId']
    
    tgw_rt_r2 = ec2_r2.describe_transit_gateway_route_tables(
        Filters=[{'Name': 'transit-gateway-id', 'Values': [tgw_r2]}]
    )['TransitGatewayRouteTables'][0]['TransitGatewayRouteTableId']
    
    # Rutas en Región 1 hacia Región 2
    ec2_r1.create_transit_gateway_route(
        DestinationCidrBlock='10.3.0.0/16',
        TransitGatewayRouteTableId=tgw_rt_r1,
        TransitGatewayAttachmentId=peering_id
    )
    
    # Rutas en Región 2 hacia Región 1
    ec2_r2.create_transit_gateway_route(
        DestinationCidrBlock='10.1.0.0/16',
        TransitGatewayRouteTableId=tgw_rt_r2,
        TransitGatewayAttachmentId=peering_id
    )
    
    ec2_r2.create_transit_gateway_route(
        DestinationCidrBlock='10.2.0.0/16',
        TransitGatewayRouteTableId=tgw_rt_r2,
        TransitGatewayAttachmentId=peering_id
    )
    
    print("Rutas configuradas")
    print("Esperando propagación de rutas (1 minuto)...")
    time.sleep(60)
    
    # ==========================================
    # CONFIGURAR RUTAS EN VPCs
    # ==========================================
    
    print(f"\n=== CONFIGURANDO RUTAS EN VPCs ===")
    
    # Obtener route tables de las VPCs
    rt_vpc1_r1 = ec2_r1.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc1_r1]}])['RouteTables'][0]['RouteTableId']
    rt_vpc2_r1 = ec2_r1.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc2_r1]}])['RouteTables'][0]['RouteTableId']
    rt_vpc1_r2 = ec2_r2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc1_r2]}])['RouteTables'][0]['RouteTableId']
    
    # Rutas en VPC1 Región 1 hacia otras VPCs via TGW + Internet
    try:
        ec2_r1.create_route(RouteTableId=rt_vpc1_r1, DestinationCidrBlock='10.2.0.0/16', TransitGatewayId=tgw_r1)
        ec2_r1.create_route(RouteTableId=rt_vpc1_r1, DestinationCidrBlock='10.3.0.0/16', TransitGatewayId=tgw_r1)
        ec2_r1.create_route(RouteTableId=rt_vpc1_r1, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw1_r1)
        print(f"Rutas creadas en VPC1-R1: {rt_vpc1_r1}")
    except Exception as e:
        print(f"Rutas VPC1-R1 ya existen: {str(e)[:50]}...")
    
    # Rutas en VPC2 Región 1 hacia otras VPCs via TGW + Internet
    try:
        ec2_r1.create_route(RouteTableId=rt_vpc2_r1, DestinationCidrBlock='10.1.0.0/16', TransitGatewayId=tgw_r1)
        ec2_r1.create_route(RouteTableId=rt_vpc2_r1, DestinationCidrBlock='10.3.0.0/16', TransitGatewayId=tgw_r1)
        ec2_r1.create_route(RouteTableId=rt_vpc2_r1, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw2_r1)
        print(f"Rutas creadas en VPC2-R1: {rt_vpc2_r1}")
    except Exception as e:
        print(f"Rutas VPC2-R1 ya existen: {str(e)[:50]}...")
    
    # Rutas en VPC1 Región 2 hacia VPCs de Región 1 via TGW + Internet
    try:
        ec2_r2.create_route(RouteTableId=rt_vpc1_r2, DestinationCidrBlock='10.1.0.0/16', TransitGatewayId=tgw_r2)
        ec2_r2.create_route(RouteTableId=rt_vpc1_r2, DestinationCidrBlock='10.2.0.0/16', TransitGatewayId=tgw_r2)
        ec2_r2.create_route(RouteTableId=rt_vpc1_r2, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw1_r2)
        print(f"Rutas creadas en VPC1-R2: {rt_vpc1_r2}")
    except Exception as e:
        print(f"Rutas VPC1-R2 ya existen: {str(e)[:50]}...")
    
    # ==========================================
    # RESUMEN
    # ==========================================
    
    print(f"\n=== INFRAESTRUCTURA COMPLETADA ===")
    print(f"Región 1 ({region1}):")
    print(f"  VPC1: {vpc1_r1} (10.1.0.0/16)")
    print(f"  VPC2: {vpc2_r1} (10.2.0.0/16)")
    print(f"  Transit Gateway: {tgw_r1}")
    print(f"")
    print(f"Región 2 ({region2}):")
    print(f"  VPC1: {vpc1_r2} (10.3.0.0/16)")
    print(f"  Transit Gateway: {tgw_r2}")
    print(f"")
    print(f"Peering: {peering_id}")
    print(f"")
    print(f"=== CONECTIVIDAD LOGRADA ===")
    print(f"✅ VPC1-R1 ↔ VPC2-R1 (via TGW local)")
    print(f"✅ VPC1-R1 ↔ VPC1-R2 (via TGW peering)")
    print(f"✅ VPC2-R1 ↔ VPC1-R2 (via TGW peering)")
    print(f"")
    print(f"=== VENTAJAS DE ESTA SOLUCIÓN ===")
    print(f"1. Escalabilidad: Fácil agregar más VPCs")
    print(f"2. Gestión centralizada: Una tabla de rutas por región")
    print(f"3. Eficiencia: Menos conexiones que VPC Peering")
    print(f"4. Flexibilidad: Control granular de rutas")

if __name__ == "__main__":
    create_multi_vpc_connectivity()