
# CREAMOS LA NAT GATEWAY EN LA SUBRED PUBLICA
nat_gw_response = ec2.create_nat_gateway(
    SubnetId=pub_subnet_id,
    AllocationId=eip_alloc_id,
    TagSpecifications=[
        {
            'ResourceType': 'natgateway',
            'Tags': [{'Key': 'Name', 'Value': 'NAT-Publica'}]
        }
    ]
)
nat_gw_id = nat_gw_response['NatGateway']['NatGatewayId']

# Esperar a que el NAT esté disponible
waiter = ec2.get_waiter('nat_gateway_available')
waiter.wait(NatGatewayIds=[nat_gw_id])

# CREAMOS LA TABLA DE RUTAS PARA LA SUBRED PRIVADA
rt_private_response = ec2.create_route_table(VpcId=vpc_id)
rt_private_id = rt_private_response['RouteTable']['RouteTableId']

# ASOCIAMOS LA TABLAS DE RUTAS PRIVADA A LA SUBRED PRIVADA
ec2.associate_route_table(
    SubnetId=priv_subnet_id,
    RouteTableId=rt_private_id
)

# CREAMOS LA RUTA EN LA TABLA DE RUTAS APUNTANDO HACIA LA NATGW
ec2.create_route(
    RouteTableId=rt_private_id,
    DestinationCidrBlock='0.0.0.0/0',
    NatGatewayId=nat_gw_id
)