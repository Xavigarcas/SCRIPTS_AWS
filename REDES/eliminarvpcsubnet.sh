VPC_IDS=$(aws ec2 describe-vpcs \
    --filters "Name=tag:entorno,Values=prueba" \
    --query "Vpcs[*].VpcId" \
    --output text)

for VPC_ID in $VPC_IDS; do
    echo "Eliminando VPC $VPC_ID..."

    # Eliminar subredes asociadas
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text)
    for SUBNET_ID in $SUBNET_IDS; do
        echo " Procesando subnet $SUBNET_ID..."

        # Buscar instancias EC2 en la subred
        EC2_IDS=$(aws ec2 describe-instances \
            --filters "Name=subnet-id,Values=$SUBNET_ID" "Name=instance-state-name,Values=running,stopped,stopping,pending" \
            --query "Reservations[*].Instances[*].InstanceId" \
            --output text)

        # Terminar instancias EC2 si existen
        for EC2_ID in $EC2_IDS; do
            aws ec2 terminate-instances --instance-ids $EC2_ID
            echo "  Instancia EC2 $EC2_ID terminada."
        done

        # Esperar a que las instancias se terminen
        if [ -n "$EC2_IDS" ]; then
            echo "  Esperando que las instancias terminen..."
            aws ec2 wait instance-terminated --instance-ids $EC2_IDS
        fi

        # Eliminar la subred
        aws ec2 delete-subnet --subnet-id $SUBNET_ID && \
            echo " Subnet $SUBNET_ID eliminada." || \
            echo " ERROR: No se pudo eliminar subnet $SUBNET_ID"
    done

    # Eliminar la VPC
    aws ec2 delete-vpc --vpc-id $VPC_ID && \
        echo "VPC $VPC_ID eliminada correctamente." || \
        echo "ERROR: No se pudo eliminar VPC $VPC_ID"
done
