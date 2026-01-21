#!/usr/bin/env python3
import boto3

# Configuración - Actualiza estos valores con tus recursos existentes
REGION = 'us-east-1'
VPC_ID = 'vpc-07179b04704ead4e6'  # Tu VPC ID
SUBNET_IDS = ['subnet-07d3b6b2bf15397ae', 'subnet-0d47e6561ff582e1a']  # Tus subnet IDs
SECURITY_GROUP_ID = 'sg-00c2229c7d9330de6'  # Tu security group ID
INSTANCE_IDS = ['i-075713c3d6eddb58c', 'i-06d4dfbe5642c6df4']  # Tus instance IDs

def create_load_balancer_only():
    elbv2 = boto3.client('elbv2', region_name=REGION)
    
    # Crear Application Load Balancer
    print("Creando Application Load Balancer...")
    lb_response = elbv2.create_load_balancer(
        Name='web-load-balancer',
        Subnets=SUBNET_IDS,
        SecurityGroups=[SECURITY_GROUP_ID],
        Scheme='internet-facing',
        Type='application'
    )
    
    lb_arn = lb_response['LoadBalancers'][0]['LoadBalancerArn']
    lb_dns = lb_response['LoadBalancers'][0]['DNSName']
    
    # Crear Target Group
    print("Creando Target Group...")
    tg_response = elbv2.create_target_group(
        Name='web-servers-tg',
        Protocol='HTTP',
        Port=80,
        VpcId=VPC_ID,
        HealthCheckPath='/',
        HealthCheckProtocol='HTTP'
    )
    
    tg_arn = tg_response['TargetGroups'][0]['TargetGroupArn']
    
    # Registrar instancias en Target Group
    print("Registrando instancias en Target Group...")
    targets = [{'Id': instance_id, 'Port': 80} for instance_id in INSTANCE_IDS]
    elbv2.register_targets(TargetGroupArn=tg_arn, Targets=targets)
    
    # Crear Listener
    print("Creando Listener...")
    elbv2.create_listener(
        LoadBalancerArn=lb_arn,
        Protocol='HTTP',
        Port=80,
        DefaultActions=[{
            'Type': 'forward',
            'TargetGroupArn': tg_arn
        }]
    )
    
    print(f"\n✅ Load Balancer creado exitosamente!")
    print(f"DNS: {lb_dns}")
    print(f"URL: http://{lb_dns}")
    
    return lb_dns

if __name__ == "__main__":
    create_load_balancer_only()