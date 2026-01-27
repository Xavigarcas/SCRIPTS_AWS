#!/usr/bin/env python3

import boto3
import subprocess
import sys

def diagnose_ssh_connection():
    """
    Diagnostica problemas de conexión SSH a instancias EC2
    """
    
    region = input("Región de la instancia: ") or 'us-east-1'
    instance_id = input("Instance ID (i-xxxxxxxxx): ")
    
    if not instance_id.startswith('i-'):
        print("❌ ID de instancia inválido")
        return
    
    ec2 = boto3.client('ec2', region_name=region)
    
    print(f"\n=== DIAGNÓSTICO SSH PARA {instance_id} ===")
    
    try:
        # Obtener información de la instancia
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        
        print(f"\n1. ✅ INFORMACIÓN DE LA INSTANCIA:")
        print(f"   Estado: {instance['State']['Name']}")
        print(f"   Tipo: {instance['InstanceType']}")
        print(f"   VPC: {instance.get('VpcId', 'N/A')}")
        print(f"   Subnet: {instance.get('SubnetId', 'N/A')}")
        print(f"   AZ: {instance['Placement']['AvailabilityZone']}")
        
        # Verificar estado
        if instance['State']['Name'] != 'running':
            print(f"❌ PROBLEMA: Instancia no está running")
            return
        
        # Verificar IP pública
        public_ip = instance.get('PublicIpAddress')
        private_ip = instance.get('PrivateIpAddress')
        
        print(f"\n2. 🌐 DIRECCIONES IP:")
        print(f"   IP Pública: {public_ip or '❌ NO TIENE'}")
        print(f"   IP Privada: {private_ip}")
        
        if not public_ip:
            print(f"❌ PROBLEMA: Sin IP pública - no accesible desde internet")
            
            # Verificar si subnet es pública
            subnet_id = instance['SubnetId']
            subnet = ec2.describe_subnets(SubnetIds=[subnet_id])['Subnets'][0]
            
            if not subnet.get('MapPublicIpOnLaunch', False):
                print(f"   💡 SOLUCIÓN: Subnet no asigna IPs públicas automáticamente")
                print(f"   Ejecuta: aws ec2 modify-subnet-attribute --subnet-id {subnet_id} --map-public-ip-on-launch")
            
            return
        
        # Verificar Key Pair
        key_name = instance.get('KeyName')
        print(f"\n3. 🔑 KEY PAIR:")
        print(f"   Key Name: {key_name or '❌ NO CONFIGURADO'}")
        
        if not key_name:
            print(f"❌ PROBLEMA: Instancia sin Key Pair - no se puede conectar por SSH")
            print(f"   💡 SOLUCIÓN: Usar Session Manager o recrear instancia con Key Pair")
            return
        
        # Verificar Security Groups
        print(f"\n4. 🛡️  SECURITY GROUPS:")
        sg_ids = [sg['GroupId'] for sg in instance['SecurityGroups']]
        
        ssh_allowed = False
        for sg_id in sg_ids:
            sg = ec2.describe_security_groups(GroupIds=[sg_id])['SecurityGroups'][0]
            print(f"   SG: {sg_id} ({sg['GroupName']})")
            
            for rule in sg['IpPermissions']:
                if rule.get('FromPort') == 22 and rule.get('ToPort') == 22:
                    ssh_allowed = True
                    for ip_range in rule.get('IpRanges', []):
                        print(f"      ✅ SSH permitido desde: {ip_range['CidrIp']}")
        
        if not ssh_allowed:
            print(f"❌ PROBLEMA: SSH (puerto 22) no permitido en Security Groups")
            print(f"   💡 SOLUCIÓN: Añadir regla SSH:")
            print(f"   aws ec2 authorize-security-group-ingress --group-id {sg_ids[0]} --protocol tcp --port 22 --cidr 0.0.0.0/0")
            return
        
        # Verificar conectividad de red
        print(f"\n5. 🌐 CONECTIVIDAD DE RED:")
        vpc_id = instance['VpcId']
        subnet_id = instance['SubnetId']
        
        # Verificar Internet Gateway
        igws = ec2.describe_internet_gateways(
            Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
        )['InternetGateways']
        
        if igws:
            print(f"   ✅ Internet Gateway: {igws[0]['InternetGatewayId']}")
        else:
            print(f"❌ PROBLEMA: VPC sin Internet Gateway")
            return
        
        # Verificar Route Table
        route_tables = ec2.describe_route_tables(
            Filters=[{'Name': 'association.subnet-id', 'Values': [subnet_id]}]
        )['RouteTables']
        
        if not route_tables:
            route_tables = ec2.describe_route_tables(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}, {'Name': 'association.main', 'Values': ['true']}]
            )['RouteTables']
        
        rt = route_tables[0]
        print(f"   Route Table: {rt['RouteTableId']}")
        
        internet_route = False
        for route in rt['Routes']:
            if route['DestinationCidrBlock'] == '0.0.0.0/0':
                internet_route = True
                gateway = route.get('GatewayId', route.get('NatGatewayId', 'N/A'))
                print(f"   ✅ Ruta a internet: 0.0.0.0/0 → {gateway}")
        
        if not internet_route:
            print(f"❌ PROBLEMA: Sin ruta a internet (0.0.0.0/0)")
            print(f"   💡 SOLUCIÓN: Añadir ruta:")
            print(f"   aws ec2 create-route --route-table-id {rt['RouteTableId']} --destination-cidr-block 0.0.0.0/0 --gateway-id {igws[0]['InternetGatewayId']}")
            return
        
        # Test de conectividad
        print(f"\n6. 🔍 TEST DE CONECTIVIDAD:")
        print(f"   Probando ping a {public_ip}...")
        
        try:
            result = subprocess.run(['ping', '-c', '3', public_ip], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"   ✅ Ping exitoso")
            else:
                print(f"   ⚠️  Ping falló - puede ser normal si ICMP está bloqueado")
        except:
            print(f"   ⚠️  No se pudo hacer ping")
        
        # Comando SSH sugerido
        print(f"\n7. 🔧 COMANDO SSH SUGERIDO:")
        print(f"   ssh -i {key_name}.pem ec2-user@{public_ip}")
        print(f"   # Para Ubuntu: ssh -i {key_name}.pem ubuntu@{public_ip}")
        print(f"   # Para Amazon Linux 2023: ssh -i {key_name}.pem ec2-user@{public_ip}")
        
        # Verificaciones adicionales
        print(f"\n8. ✅ VERIFICACIONES ADICIONALES:")
        print(f"   - ¿Tienes el archivo .pem en tu máquina local?")
        print(f"   - ¿El archivo .pem tiene permisos 400? (chmod 400 {key_name}.pem)")
        print(f"   - ¿Estás usando el usuario correcto? (ec2-user, ubuntu, admin)")
        print(f"   - ¿Tu IP pública ha cambiado? (curl ifconfig.me)")
        
    except Exception as e:
        print(f"❌ Error obteniendo información: {e}")

def quick_ssh_fix():
    """
    Script rápido para solucionar problemas SSH comunes
    """
    region = input("Región: ") or 'us-east-1'
    instance_id = input("Instance ID: ")
    
    ec2 = boto3.client('ec2', region_name=region)
    
    print("=== SOLUCIONES RÁPIDAS SSH ===")
    
    try:
        instance = ec2.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
        sg_id = instance['SecurityGroups'][0]['GroupId']
        
        print("1. Añadir regla SSH al Security Group:")
        print(f"aws ec2 authorize-security-group-ingress --group-id {sg_id} --protocol tcp --port 22 --cidr 0.0.0.0/0")
        
        print("\n2. Asignar IP pública (si no tiene):")
        print(f"aws ec2 allocate-address --domain vpc")
        print(f"aws ec2 associate-address --instance-id {instance_id} --allocation-id eipalloc-xxx")
        
        print("\n3. Verificar/crear ruta a internet:")
        vpc_id = instance['VpcId']
        subnet_id = instance['SubnetId']
        
        # Obtener IGW
        igws = ec2.describe_internet_gateways(
            Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
        )['InternetGateways']
        
        if igws:
            igw_id = igws[0]['InternetGatewayId']
            rt = ec2.describe_route_tables(
                Filters=[{'Name': 'association.subnet-id', 'Values': [subnet_id]}]
            )['RouteTables']
            
            if rt:
                rt_id = rt[0]['RouteTableId']
                print(f"aws ec2 create-route --route-table-id {rt_id} --destination-cidr-block 0.0.0.0/0 --gateway-id {igw_id}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("1. Diagnóstico completo SSH")
    print("2. Soluciones rápidas")
    choice = input("Selecciona opción (1/2): ")
    
    if choice == "1":
        diagnose_ssh_connection()
    elif choice == "2":
        quick_ssh_fix()
    else:
        print("Opción inválida")