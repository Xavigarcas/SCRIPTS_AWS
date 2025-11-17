#!/bin/bash

ID_INSTANCIA="$1"
NUEVO_TIPO="$2"

# Ver si estan bien pasados los parametros
if [ $# -ne 2 ]; then
    echo "Uso: $0 <id-instancia> <nuevo-tipo>"
    echo "Ejemplo: $0 i-021eb29ee0c69b2c3 t3.small"
    exit 1
fi

echo "Empezamos a cambiar el tipo de la instancia"
echo ""

# Verificar que la instancia existe y obtener su estado/información
echo "Verificando instancia..."
INFO=$(aws ec2 describe-instances --instance-ids "$ID_INSTANCIA" --query 'Reservations[0].Instances[0].[State.Name,InstanceType]' --output text 2>&1)

if echo "$INFO" | grep -q "InvalidInstanceID"; then
    echo "ERROR: La instancia $ID_INSTANCIA no existe."
    exit 1
fi

# Obtenemostipo actual y estado
ESTADO=$(echo "$INFO" | awk '{print $1}')
TIPO_ACTUAL=$(echo "$INFO" | awk '{print $2}')

echo "Instancia: $ID_INSTANCIA"
echo "Estado actual: $ESTADO"
echo "Tipo actual: $TIPO_ACTUAL"
echo "Tipo nuevo: $NUEVO_TIPO"
echo ""

# Comprobar si el tipo ya es igual
if [ "$TIPO_ACTUAL" == "$NUEVO_TIPO" ]; then
    echo "La instancia ya tiene el tipo $NUEVO_TIPO. No es necesario cambiar."
    exit 0
fi

# COnfirmacion
echo "La instancia se va a parar."
read -p "¿COntinuamos? (s/n): " CONFIRMACION

if [ "$CONFIRMACION" != "s" ]; then
    echo "Operación cancelada."
    exit 0
fi

echo ""
echo "Deteniendo la instancia"

# PArar la maquina si esta en ejecucion
if [ "$ESTADO" == "running" ]; then
    echo "Deteniendo instancia"
    aws ec2 stop-instances --instance-ids "$ID_INSTANCIA" > /dev/null
    echo "Esperando a que la instancia se pare completamente"
    aws ec2 wait instance-stopped --instance-ids "$ID_INSTANCIA"
    echo "Instancia detenida"
elif [ "$ESTADO" == "stopped" ]; then
    echo "La instancia ya está detenida."
else
    echo "La instancia está en estado: $ESTADO"
    echo "Esperando a que se pare"
    aws ec2 wait instance-stopped --instance-ids "$ID_INSTANCIA"
    echo "Instancia detenida"
fi

echo ""
echo "Cambiando el tipo"
aws ec2 modify-instance-attribute --instance-id "$ID_INSTANCIA" --instance-type "{\"Value\": \"$NUEVO_TIPO\"}"
echo "Tipo cambiado a $NUEVO_TIPO"
echo ""

echo "Iniciando la instancia"
aws ec2 start-instances --instance-ids "$ID_INSTANCIA" > /dev/null
echo "Esperando a que se inicie"
aws ec2 wait instance-running --instance-ids "$ID_INSTANCIA"
echo "Instancia iniciada"
echo ""

echo "FInalizado."
echo "La instancia $ID_INSTANCIA ahora es del tipo $NUEVO_TIPO y está en ejecución."
