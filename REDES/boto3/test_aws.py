import boto3
import sys

try:
    print("Probando conexión a AWS...")
    
    # Verificar credenciales
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()
    print(f"✓ Conectado como: {identity['Arn']}")
    
    # Verificar cliente EC2
    ec2 = boto3.client('ec2')
    regions = ec2.describe_regions()
    print(f"✓ Cliente EC2 funcionando. Regiones disponibles: {len(regions['Regions'])}")
    
    # Verificar región actual
    print(f"✓ Región actual: {ec2.meta.region_name}")
    
    print("\n¡Todo configurado correctamente!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPosibles soluciones:")
    print("1. Configura AWS CLI: aws configure")
    print("2. O exporta variables: export AWS_ACCESS_KEY_ID=xxx")
    print("3. O usa AWS SSO/IAM roles")