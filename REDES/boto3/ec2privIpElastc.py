
ec2_privada_response = ec2.run_instances(
    ImageId='ami-0360c520857e3138f',
    InstanceType='t2.micro',
    SubnetId=priv_subnet_id,
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'ec2privada'}]
        }
    ],
    KeyName='vockey',
    SecurityGroupIds=[sg_id],
    PrivateIpAddress='192.168.0.200',
    MinCount=1,
    MaxCount=1
)
ec2_privada_id = ec2_privada_response['Instances'][0]['InstanceId']

# CREACION DE LA IP ELASTICA PARA EL NAT GATEWAY
eip_response = ec2.allocate_address(Domain='vpc')
eip_alloc_id = eip_response['AllocationId']
