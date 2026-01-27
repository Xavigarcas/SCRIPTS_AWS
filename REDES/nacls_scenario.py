#!/usr/bin/env python3

import boto3
import time

def create_nacls_scenario():
    region = 'us-east-1'
    ec2 = boto3.client('ec2', region_name=region)
    
    # Usar VPC y subredes del script anterior (cambiar por tus IDs)
    vpc_id = input("Introduce VPC ID: ")
    public_subnet = input("Introduce Public Subnet ID: ")
    private_subnet = input("Introduce Private Subnet ID: ")
    
    print(f"Configurando NACLs para VPC: {vpc_id}")
    
    # ==========================================
    # CREAR NACL PÚBLICA
    # ==========================================
    
    print("Creando NACL pública...")
    public_nacl_response = ec2.create_network_acl(
        VpcId=vpc_id,
        TagSpecifications=[{
            'ResourceType': 'network-acl',
            'Tags': [{'Key': 'Name', 'Value': 'PublicNACL'}]
        }]
    )
    public_nacl = public_nacl_response['NetworkAcl']['NetworkAclId']
    print(f"NACL pública creada: {public_nacl}")
    
    # Reglas NACL pública: ALLOW 80/443 inbound, DENY resto, ALLOW outbound
    print("Configurando reglas NACL pública...")
    
    # INBOUND: HTTP (80)
    ec2.create_network_acl_entry(
        NetworkAclId=public_nacl,
        RuleNumber=100,
        Protocol='6',  # TCP
        PortRange={'From': 80, 'To': 80},
        CidrBlock='0.0.0.0/0',
        RuleAction='allow',
        Egress=False
    )
    
    # INBOUND: HTTPS (443)
    ec2.create_network_acl_entry(
        NetworkAclId=public_nacl,
        RuleNumber=110,
        Protocol='6',  # TCP
        PortRange={'From': 443, 'To': 443},
        CidrBlock='0.0.0.0/0',
        RuleAction='allow',
        Egress=False
    )
    
    # INBOUND: SSH (22) para testing
    ec2.create_network_acl_entry(
        NetworkAclId=public_nacl,
        RuleNumber=120,
        Protocol='6',  # TCP
        PortRange={'From': 22, 'To': 22},
        CidrBlock='0.0.0.0/0',
        RuleAction='allow',
        Egress=False
    )
    
    # INBOUND: Puertos efímeros para respuestas
    ec2.create_network_acl_entry(
        NetworkAclId=public_nacl,
        RuleNumber=130,
        Protocol='6',  # TCP
        PortRange={'From': 1024, 'To': 65535},
        CidrBlock='0.0.0.0/0',
        RuleAction='allow',
        Egress=False
    )
    
    # OUTBOUND: Permitir todo
    ec2.create_network_acl_entry(
        NetworkAclId=public_nacl,
        RuleNumber=200,
        Protocol='-1',  # All protocols
        CidrBlock='0.0.0.0/0',
        RuleAction='allow',
        Egress=True
    )
    
    # ==========================================
    # CREAR NACL PRIVADA
    # ==========================================
    
    print("Creando NACL privada...")
    private_nacl_response = ec2.create_network_acl(
        VpcId=vpc_id,
        TagSpecifications=[{
            'ResourceType': 'network-acl',
            'Tags': [{'Key': 'Name', 'Value': 'PrivateNACL'}]
        }]
    )
    private_nacl = private_nacl_response['NetworkAcl']['NetworkAclId']
    print(f"NACL privada creada: {private_nacl}")
    
    # Reglas NACL privada: ALLOW desde pública todos puertos
    print("Configurando reglas NACL privada...")
    
    # INBOUND: Permitir desde subred pública
    ec2.create_network_acl_entry(
        NetworkAclId=private_nacl,
        RuleNumber=100,
        Protocol='-1',  # All protocols
        CidrBlock='15.0.1.0/24',  # CIDR subred pública
        RuleAction='allow',
        Egress=False
    )
    
    # INBOUND: Puertos efímeros para respuestas NAT
    ec2.create_network_acl_entry(
        NetworkAclId=private_nacl,
        RuleNumber=110,
        Protocol='6',  # TCP
        PortRange={'From': 1024, 'To': 65535},
        CidrBlock='0.0.0.0/0',
        RuleAction='allow',
        Egress=False
    )
    
    # OUTBOUND: Permitir todo (para NAT Gateway)
    ec2.create_network_acl_entry(
        NetworkAclId=private_nacl,
        RuleNumber=200,
        Protocol='-1',  # All protocols
        CidrBlock='0.0.0.0/0',
        RuleAction='allow',
        Egress=True
    )
    
    # ==========================================
    # ASOCIAR NACLs A SUBREDES
    # ==========================================
    
    print("Asociando NACLs a subredes...")
    
    # Obtener asociaciones actuales para reemplazarlas
    public_associations = ec2.describe_network_acls(
        Filters=[{'Name': 'association.subnet-id', 'Values': [public_subnet]}]
    )['NetworkAcls'][0]['Associations']
    
    private_associations = ec2.describe_network_acls(
        Filters=[{'Name': 'association.subnet-id', 'Values': [private_subnet]}]
    )['NetworkAcls'][0]['Associations']
    
    # Reemplazar asociación pública
    for assoc in public_associations:
        if assoc['SubnetId'] == public_subnet:
            ec2.replace_network_acl_association(
                AssociationId=assoc['NetworkAclAssociationId'],
                NetworkAclId=public_nacl
            )
            break
    
    # Reemplazar asociación privada
    for assoc in private_associations:
        if assoc['SubnetId'] == private_subnet:
            ec2.replace_network_acl_association(
                AssociationId=assoc['NetworkAclAssociationId'],
                NetworkAclId=private_nacl
            )
            break
    
    print(f"\n=== CONFIGURACIÓN COMPLETADA ===")
    print(f"NACL Pública: {public_nacl}")
    print(f"NACL Privada: {private_nacl}")
    print(f"\nReglas implementadas:")
    print(f"- Subred pública: Solo HTTP/HTTPS/SSH desde internet")
    print(f"- Subred privada: Solo comunicación con subred pública")
    print(f"\nVentajas NACLs vs Security Groups:")
    print(f"1. NACLs actúan a nivel de SUBRED (stateless)")
    print(f"2. Security Groups actúan a nivel de INSTANCIA (stateful)")
    print(f"3. NACLs proporcionan defensa en profundidad")
    print(f"4. NACLs pueden DENEGAR explícitamente")
    print(f"5. Orden de evaluación: NACL → Security Group → Instancia")

if __name__ == "__main__":
    create_nacls_scenario()