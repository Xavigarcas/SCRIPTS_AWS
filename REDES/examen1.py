import boto3
import time

region = 'us-east-1'  # Ajusta a tu región
ec2 = boto3.client('ec2', region_name=region)

# Crear VPC 15.0.0.0/20
vpc_response = ec2.create_vpc(CidrBlock='15.0.0.0/20', TagSpecifications=[{'ResourceType': 'vpc', 'Tags': [{'Key': 'Name', 'Value': '3TierVPC'}]}])
vpc_id = vpc_response['Vpc']['VpcId']
print(f"VPC creada: {vpc_id}")

# Obtener AZs disponibles
azs = ec2.describe_availability_zones()['AvailabilityZones']
az1 = azs[0]['ZoneName']

# Subredes con las IPs solicitadas
public_subnet = ec2.create_subnet(VpcId=vpc_id, CidrBlock='15.0.1.0/24', AvailabilityZone=az1, TagSpecifications=[{'ResourceType': 'subnet', 'Tags': [{'Key': 'Name', 'Value': 'Public-Frontend'}]}])['Subnet']['SubnetId']
private_app_subnet = ec2.create_subnet(VpcId=vpc_id, CidrBlock='15.0.2.0/24', AvailabilityZone=az1, TagSpecifications=[{'ResourceType': 'subnet', 'Tags': [{'Key': 'Name', 'Value': 'Private-Backend'}]}])['Subnet']['SubnetId']
private_db_subnet = ec2.create_subnet(VpcId=vpc_id, CidrBlock='15.0.3.0/24', AvailabilityZone=az1, TagSpecifications=[{'ResourceType': 'subnet', 'Tags': [{'Key': 'Name', 'Value': 'Private-DB'}]}])['Subnet']['SubnetId']
print(f"Subredes: Public {public_subnet}, Backend {private_app_subnet}, DB {private_db_subnet}")

# Internet Gateway
igw = ec2.create_internet_gateway(TagSpecifications=[{'ResourceType': 'internet-gateway', 'Tags': [{'Key': 'Name', 'Value': 'IGW-3Tier'}]}])['InternetGateway']['InternetGatewayId']
ec2.attach_internet_gateway(VpcId=vpc_id, InternetGatewayId=igw)

# EIP y NAT Gateway en subred pública
eip = ec2.allocate_address(Domain='vpc')['AllocationId']
time.sleep(30)  # Espera propagación
nat_gw = ec2.create_nat_gateway(SubnetId=public_subnet, AllocationId=eip)['NatGateway']['NatGatewayId']
print(f"NAT GW: {nat_gw}")

# Añadir tag al NAT Gateway después de crearlo
time.sleep(10)
ec2.create_tags(Resources=[nat_gw], Tags=[{'Key': 'Name', 'Value': 'NAT-3Tier'}])

# Esperar a que NAT Gateway esté disponible
print("Esperando NAT Gateway...")
time.sleep(90)

# Route Tables
public_rt = ec2.create_route_table(VpcId=vpc_id, TagSpecifications=[{'ResourceType': 'route-table', 'Tags': [{'Key': 'Name', 'Value': 'PublicRT'}]}])['RouteTable']['RouteTableId']
private_rt = ec2.create_route_table(VpcId=vpc_id, TagSpecifications=[{'ResourceType': 'route-table', 'Tags': [{'Key': 'Name', 'Value': 'PrivateRT'}]}])['RouteTable']['RouteTableId']

# Rutas
ec2.create_route(RouteTableId=public_rt, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw)
ec2.create_route(RouteTableId=private_rt, DestinationCidrBlock='0.0.0.0/0', NatGatewayId=nat_gw)

# Asociaciones
ec2.associate_route_table(SubnetId=public_subnet, RouteTableId=public_rt)
ec2.associate_route_table(SubnetId=private_app_subnet, RouteTableId=private_rt)
ec2.associate_route_table(SubnetId=private_db_subnet, RouteTableId=private_rt)

# Enable auto-assign public IP en pública
ec2.modify_subnet_attribute(SubnetId=public_subnet, MapPublicIpOnLaunch={'Value': True})

# Security Groups (3-tier restrictivo)
# Frontend SG: HTTP/HTTPS + SSH inbound internet
sg_frontend = ec2.create_security_group(GroupName='SG-Frontend', Description='Frontend public', VpcId=vpc_id, TagSpecifications=[{'ResourceType': 'security-group', 'Tags': [{'Key': 'Name', 'Value': 'SG-Frontend'}]}])['GroupId']
ec2.authorize_security_group_ingress(GroupId=sg_frontend, IpPermissions=[
    {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
    {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
    {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
])

# Backend SG: HTTP desde frontend + SSH desde internet (para testing)
sg_backend = ec2.create_security_group(GroupName='SG-Backend', Description='Backend private', VpcId=vpc_id, TagSpecifications=[{'ResourceType': 'security-group', 'Tags': [{'Key': 'Name', 'Value': 'SG-Backend'}]}])['GroupId']
ec2.authorize_security_group_ingress(GroupId=sg_backend, IpPermissions=[
    {'IpProtocol': 'tcp', 'FromPort': 8080, 'ToPort': 8080, 'UserIdGroupPairs': [{'GroupId': sg_frontend}]},
    {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}  # SSH desde internet para testing
])

# DB SG: Puerto DB + SSH solo desde backend
sg_db = ec2.create_security_group(GroupName='SG-DB', Description='DB private', VpcId=vpc_id, TagSpecifications=[{'ResourceType': 'security-group', 'Tags': [{'Key': 'Name', 'Value': 'SG-DB'}]}])['GroupId']
ec2.authorize_security_group_ingress(GroupId=sg_db, IpPermissions=[
    {'IpProtocol': 'tcp', 'FromPort': 3306, 'ToPort': 3306, 'UserIdGroupPairs': [{'GroupId': sg_backend}]},
    {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'UserIdGroupPairs': [{'GroupId': sg_backend}]}
])

print("IDs para capturas: SGs - Frontend:", sg_frontend, "Backend:", sg_backend, "DB:", sg_db)
print("Infra creada. Revisa consola VPC para capturas de SGs y Route Tables.")

# ==========================================
# CONFIGURAR NACLs PARA EL ESCENARIO
# ==========================================

print("\n=== CONFIGURANDO NACLs ===")

# NACL pública: Solo HTTP/HTTPS desde internet
public_nacl = ec2.create_network_acl(
    VpcId=vpc_id,
    TagSpecifications=[{'ResourceType': 'network-acl', 'Tags': [{'Key': 'Name', 'Value': 'PublicNACL'}]}]
)['NetworkAcl']['NetworkAclId']

# Reglas NACL pública
ec2.create_network_acl_entry(NetworkAclId=public_nacl, RuleNumber=100, Protocol='6', PortRange={'From': 80, 'To': 80}, CidrBlock='0.0.0.0/0', RuleAction='allow', Egress=False)
ec2.create_network_acl_entry(NetworkAclId=public_nacl, RuleNumber=110, Protocol='6', PortRange={'From': 443, 'To': 443}, CidrBlock='0.0.0.0/0', RuleAction='allow', Egress=False)
ec2.create_network_acl_entry(NetworkAclId=public_nacl, RuleNumber=120, Protocol='6', PortRange={'From': 22, 'To': 22}, CidrBlock='0.0.0.0/0', RuleAction='allow', Egress=False)
ec2.create_network_acl_entry(NetworkAclId=public_nacl, RuleNumber=130, Protocol='6', PortRange={'From': 1024, 'To': 65535}, CidrBlock='0.0.0.0/0', RuleAction='allow', Egress=False)
ec2.create_network_acl_entry(NetworkAclId=public_nacl, RuleNumber=200, Protocol='-1', CidrBlock='0.0.0.0/0', RuleAction='allow', Egress=True)

# NACL privada: Solo desde subred pública
private_nacl = ec2.create_network_acl(
    VpcId=vpc_id,
    TagSpecifications=[{'ResourceType': 'network-acl', 'Tags': [{'Key': 'Name', 'Value': 'PrivateNACL'}]}]
)['NetworkAcl']['NetworkAclId']

# Reglas NACL privada
ec2.create_network_acl_entry(NetworkAclId=private_nacl, RuleNumber=100, Protocol='-1', CidrBlock='15.0.1.0/24', RuleAction='allow', Egress=False)
ec2.create_network_acl_entry(NetworkAclId=private_nacl, RuleNumber=110, Protocol='6', PortRange={'From': 1024, 'To': 65535}, CidrBlock='0.0.0.0/0', RuleAction='allow', Egress=False)
ec2.create_network_acl_entry(NetworkAclId=private_nacl, RuleNumber=200, Protocol='-1', CidrBlock='0.0.0.0/0', RuleAction='allow', Egress=True)

# Asociar NACLs
time.sleep(5)
public_assoc = ec2.describe_network_acls(Filters=[{'Name': 'association.subnet-id', 'Values': [public_subnet]}])['NetworkAcls'][0]['Associations']
private_assoc = ec2.describe_network_acls(Filters=[{'Name': 'association.subnet-id', 'Values': [private_app_subnet]}])['NetworkAcls'][0]['Associations']

for assoc in public_assoc:
    if assoc['SubnetId'] == public_subnet:
        ec2.replace_network_acl_association(AssociationId=assoc['NetworkAclAssociationId'], NetworkAclId=public_nacl)
        break

for assoc in private_assoc:
    if assoc['SubnetId'] == private_app_subnet:
        ec2.replace_network_acl_association(AssociationId=assoc['NetworkAclAssociationId'], NetworkAclId=private_nacl)
        break

print(f"NACLs configurados: Pública {public_nacl}, Privada {private_nacl}")

# AMI ID y Key Pair
ami_id = 'ami-07ff62358b87c7116'
key_name = 'user'  # Cambia por tu key pair name

# Crear bastion host en subred pública
bastion = ec2.run_instances(
    ImageId=ami_id, InstanceType='t3.micro', MinCount=1, MaxCount=1, KeyName=key_name,
    NetworkInterfaces=[{'DeviceIndex': 0, 'SubnetId': public_subnet, 'Groups': [sg_frontend], 'AssociatePublicIpAddress': True}],
    TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Bastion-Host'}]}]
)['Instances'][0]['InstanceId']

# Instancia test en privada para apt-get (con IP pública para testing)
instance = ec2.run_instances(
    ImageId=ami_id, InstanceType='t3.micro', MinCount=1, MaxCount=1, KeyName=key_name,
    NetworkInterfaces=[{'DeviceIndex': 0, 'SubnetId': private_app_subnet, 'Groups': [sg_backend], 'AssociatePublicIpAddress': True}],  # IP pública para testing
    TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Test-Private-Backend'}]}]
)['Instances'][0]['InstanceId']

print(f"\n=== RESUMEN INFRAESTRUCTURA ===")
print(f"VPC: {vpc_id}")
print(f"Subredes: Public {public_subnet}, Backend {private_app_subnet}, DB {private_db_subnet}")
print(f"Security Groups: Frontend {sg_frontend}, Backend {sg_backend}, DB {sg_db}")
print(f"NACLs: Pública {public_nacl}, Privada {private_nacl}")
print(f"Bastion Host: {bastion}")
print(f"Instancia privada: {instance}")
print(f"\n=== VENTAJAS NACLs vs Security Groups ===")
print(f"1. NACLs: Stateless, evalúan tráfico inbound/outbound por separado")
print(f"2. Security Groups: Stateful, permiten respuestas automáticamente")
print(f"3. NACLs: Nivel de subred, afectan a TODAS las instancias")
print(f"4. Security Groups: Nivel de instancia, más granular")
print(f"5. NACLs: Pueden DENEGAR explícitamente")
print(f"6. Security Groups: Solo PERMITEN (deny implícito)")
print(f"7. Orden: Internet → NACL → Security Group → Instancia")
