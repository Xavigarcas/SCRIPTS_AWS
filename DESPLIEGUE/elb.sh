#Moviendo los html de los codigos verde y azul
aws s3 cp blue.zip s3://TU-BUCKET/blue.zip
aws s3 cp green.zip s3://TU-BUCKET/green.zip

#Creando aplicación
aws elasticbeanstalk create-application --application-name "MiApp"

#Creando las versiones azul y verde de la aplicacion
aws elasticbeanstalk create-application-version \
  --application-name MiApp \
  --version-label azul \
  --source-bundle S3Bucket=TU-BUCKET,S3Key=blue.zip

aws elasticbeanstalk create-application-version \
  --application-name MiApp \
  --version-label verde \
  --source-bundle S3Bucket=TU-BUCKET,S3Key=green.zip

#Creando los entornos azul y verde
aws elasticbeanstalk create-environment   --application-name MiApp \
  --environment-name mi-entorno-azul \
  --version-label azul \
  --solution-stack-name "64bit Amazon Linux 2023 v4.7.8 running PHP 8.4" \
  --option-settings \
    Namespace=aws:autoscaling:launchconfiguration,OptionName=IamInstanceProfile,Value=LabInstanceProfile \
    Namespace=aws:elasticbeanstalk:environment,OptionName=ServiceRole,Value=LabRole \
    Namespace=aws:autoscaling:launchconfiguration,OptionName=EC2KeyName,Value=vockey

aws elasticbeanstalk create-environment   --application-name MiApp \
  --environment-name mi-entorno-verde \
  --version-label verde \
  --solution-stack-name "64bit Amazon Linux 2023 v4.7.8 running PHP 8.4" \
  --option-settings \
    Namespace=aws:autoscaling:launchconfiguration,OptionName=IamInstanceProfile,Value=LabInstanceProfile \
    Namespace=aws:elasticbeanstalk:environment,OptionName=ServiceRole,Value=LabRole \
    Namespace=aws:autoscaling:launchconfiguration,OptionName=EC2KeyName,Value=vockey


#Realizando el swap, es decir un balanceador de carga entre el azul y el verde, para que el trafico de la azul se redirija a la verde
aws elasticbeanstalk swap-environment-cnames \
  --source-environment-name mi-entorno-azul \
  --destination-environment-name mi-entorno-verde

