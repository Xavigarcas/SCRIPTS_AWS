#!/usr/bin/env python3

import boto3
import time

def create_blackhole_scenario():
    """
    Crea un escenario de blackhole eliminando attachments pero manteniendo rutas
    """
    
    region1 = 'us-east-1'
    region2 = 'us-west-2'
    
    ec2_r1 = boto3.client('ec2', region_name=region1)
    ec2_r2 = boto3.client('ec2', region_name=region2)
    
    print("=== CREANDO ESCENARIO BLACKHOLE ===")
    print("Un blackhole ocurre cuando hay rutas que apuntan a destinos inexistentes")
    
    # Obtener IDs de la infraestructura existente
    tgw_id = input("Introduce Transit Gateway ID (región 1): ")
    peering_id = input("Introduce Peering Attachment ID: ")
    vpc_id = input("Introduce VPC ID para crear blackhole: ")
    
    print(f"\n=== MÉTODO 1: ELIMINAR ATTACHMENT PERO MANTENER RUTAS ===")
    
    # Obtener route table del TGW
    tgw_rt = ec2_r1.describe_transit_gateway_route_tables(
        Filters=[{'Name': 'transit-gateway-id', 'Values': [tgw_id]}]
    )['TransitGatewayRouteTables'][0]['TransitGatewayRouteTableId']
    
    # Crear ruta hacia destino que será eliminado
    print("Creando ruta hacia attachment que será eliminado...")
    try:
        ec2_r1.create_transit_gateway_route(
            DestinationCidrBlock='192.168.100.0/24',  # CIDR ficticio
            TransitGatewayRouteTableId=tgw_rt,
            TransitGatewayAttachmentId=peering_id
        )
        print("✅ Ruta creada hacia peering attachment")
    except Exception as e:
        print(f"Ruta ya existe: {e}")
    
    # Simular eliminación del peering (ESTO CREA EL BLACKHOLE)
    print("\n🚨 CREANDO BLACKHOLE: Eliminando peering pero manteniendo ruta...")
    try:
        ec2_r1.delete_transit_gateway_peering_attachment(TransitGatewayAttachmentId=peering_id)
        print("❌ Peering eliminado - BLACKHOLE CREADO")
        print("   El tráfico hacia 192.168.100.0/24 ahora va a un destino inexistente")
    except Exception as e:
        print(f"Error eliminando peering: {e}")
    
    print(f"\n=== MÉTODO 2: RUTA HACIA ATTACHMENT INEXISTENTE ===")
    
    # Crear ruta hacia attachment ID falso
    fake_attachment = "tgw-attach-xxxxxxxxx"  # ID falso
    try:
        ec2_r1.create_transit_gateway_route(
            DestinationCidrBlock='172.16.0.0/16',
            TransitGatewayRouteTableId=tgw_rt,
            TransitGatewayAttachmentId=fake_attachment
        )
        print("❌ BLACKHOLE CREADO: Ruta hacia attachment inexistente")
    except Exception as e:
        print(f"No se pudo crear ruta falsa: {e}")
    
    print(f"\n=== MÉTODO 3: BLACKHOLE EN VPC ROUTE TABLE ===")
    
    # Obtener route table de VPC
    vpc_rt = ec2_r1.describe_route_tables(
        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
    )['RouteTables'][0]['RouteTableId']
    
    # Crear ruta hacia NAT Gateway inexistente
    try:
        ec2_r1.create_route(
            RouteTableId=vpc_rt,
            DestinationCidrBlock='10.99.0.0/16',
            NatGatewayId='nat-xxxxxxxxx'  # NAT Gateway falso
        )
        print("❌ BLACKHOLE CREADO: Ruta VPC hacia NAT inexistente")
    except Exception as e:
        print(f"No se pudo crear ruta VPC falsa: {e}")
    
    print(f"\n=== VERIFICAR BLACKHOLES ===")
    
    # Mostrar rutas del TGW
    routes = ec2_r1.describe_transit_gateway_route_tables(
        TransitGatewayRouteTableIds=[tgw_rt]
    )
    
    print(f"Route Table TGW: {tgw_rt}")
    
    # Buscar rutas en estado blackhole
    tgw_routes = ec2_r1.search_transit_gateway_routes(
        TransitGatewayRouteTableId=tgw_rt,
        Filters=[{'Name': 'state', 'Values': ['blackhole']}]
    )
    
    if tgw_routes['Routes']:
        print("🕳️  BLACKHOLES ENCONTRADOS:")
        for route in tgw_routes['Routes']:
            print(f"   - {route['DestinationCidrBlock']} → {route['State']}")
    else:
        print("No se encontraron blackholes activos")
    
    print(f"\n=== CÓMO DETECTAR BLACKHOLES ===")
    print("1. AWS CLI:")
    print(f"   aws ec2 search-transit-gateway-routes --transit-gateway-route-table-id {tgw_rt} --filters Name=state,Values=blackhole")
    print("2. Consola AWS: VPC → Transit Gateways → Route Tables → Routes")
    print("3. CloudWatch: Métricas de TGW con PacketDropCount")
    
    print(f"\n=== CÓMO SOLUCIONAR BLACKHOLES ===")
    print("1. Eliminar rutas hacia destinos inexistentes")
    print("2. Recrear attachments eliminados")
    print("3. Corregir IDs de destino en rutas")
    print("4. Verificar estado de attachments")

def fix_blackholes():
    """
    Script para solucionar blackholes
    """
    region = input("Región (us-east-1): ") or 'us-east-1'
    ec2 = boto3.client('ec2', region_name=region)
    
    tgw_rt_id = input("Transit Gateway Route Table ID: ")
    
    # Buscar blackholes
    blackhole_routes = ec2.search_transit_gateway_routes(
        TransitGatewayRouteTableId=tgw_rt_id,
        Filters=[{'Name': 'state', 'Values': ['blackhole']}]
    )
    
    if not blackhole_routes['Routes']:
        print("✅ No se encontraron blackholes")
        return
    
    print(f"🕳️  Encontrados {len(blackhole_routes['Routes'])} blackholes:")
    
    for i, route in enumerate(blackhole_routes['Routes']):
        print(f"{i+1}. {route['DestinationCidrBlock']} → {route.get('TransitGatewayAttachments', [{}])[0].get('TransitGatewayAttachmentId', 'N/A')}")
    
    # Eliminar blackholes
    if input("¿Eliminar todas las rutas blackhole? (y/N): ").lower() == 'y':
        for route in blackhole_routes['Routes']:
            try:
                ec2.delete_transit_gateway_route(
                    TransitGatewayRouteTableId=tgw_rt_id,
                    DestinationCidrBlock=route['DestinationCidrBlock']
                )
                print(f"✅ Eliminada ruta blackhole: {route['DestinationCidrBlock']}")
            except Exception as e:
                print(f"❌ Error eliminando {route['DestinationCidrBlock']}: {e}")

if __name__ == "__main__":
    print("1. Crear blackhole")
    print("2. Solucionar blackholes")
    choice = input("Selecciona opción (1/2): ")
    
    if choice == "1":
        create_blackhole_scenario()
    elif choice == "2":
        fix_blackholes()
    else:
        print("Opción inválida")