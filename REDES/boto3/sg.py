# CREAMOS GRUPOS DE SEGURIDAD
sg_response = ec2.create_security_group(
    GroupName='SG-SSH-ICMP',
    Description='Permite SSH y ping desde cualquier lugar',
    VpcId=vpc_id
)
sg_id = sg_response['GroupId']

ec2.authorize_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        },
        {
            'IpProtocol': 'icmp',
            'FromPort': -1,
            'ToPort': -1,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
    ]
)