# LANZAMOS INSTANCIAS
ec2_publica_response = ec2.run_instances(
    ImageId='ami-0360c520857e3138f',
    InstanceType='t2.micro',
    SubnetId=pub_subnet_id,
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'ec2publica'}]
        }
    ],
    KeyName='vockey',
    SecurityGroupIds=[sg_id],
    PrivateIpAddress='192.168.0.100',
    MinCount=1,
    MaxCount=1
)
ec2_publica_id = ec2_publica_response['Instances'][0]['InstanceId']