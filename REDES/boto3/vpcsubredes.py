import boto3

# Crear cliente EC2
ec2 = boto3.client('ec2')

# CREACION VPC
vpc_response = ec2.create_vpc(
    CidrBlock='192.168.0.0/24',
    TagSpecifications=[
        {
            'ResourceType': 'vpc',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'nubePRACTICANATGW'
                }
            ]
        }
    ]
)
vpc_id = vpc_response['Vpc']['VpcId']

# CREACIÓN SUBRED PUBLICA
pub_subnet_response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='192.168.0.0/25',
    AvailabilityZone='us-east-1a',
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'PublicaCLI'
                }
            ]
        }
    ]
)
pub_subnet_id = pub_subnet_response['Subnet']['SubnetId']

# CREACION SUBRED PRIVADA
priv_subnet_response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='192.168.0.128/25',
    AvailabilityZone='us-east-1a',
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'PrivadaCLI'
                }
            ]
        }
    ]
)
priv_subnet_id = priv_subnet_response['Subnet']['SubnetId']

print(f"VPC ID: {vpc_id}")
print(f"Public Subnet ID: {pub_subnet_id}")
print(f"Private Subnet ID: {priv_subnet_id}")