Set-StrictMode -Version Latest

. .\LibCloudFormationTemplate.ps1
. .\LibEC2.ps1
. .\LibParameter.ps1
. .\LibText.ps1

#---main-----------------------------------------------------------------------
$template = New-CloudFormationTemplate -Description 'Test specimen'


#---parameters-----------------------------------------------------------------
$parameter = New-ParameterItem -Name 'KeyName' -Type AWS::EC2::KeyPair::KeyName `
    -Description 'Name of an existing EC2 KeyPair file (.pem) to use to create EC2 instances' `
    -Default 'id_rsa_usw1_dev'
Add-ParameterItem -Template $template -Parameter $parameter

$parameter = New-ParameterItem -Name 'EC2InstanceType' -Type String -ConstraintDescription 'Must be a valid EC2 instance type' -Description 'EC2 instance type, reference this parameter to insure consistency' -Default 't2.micro' -AllowedValues @('t2.small', 't2.micro', 't2.medium', 't2.large', 'm3.medium', 'm3.large', 'c4.large' )   
Add-ParameterItem -Template $template -Parameter $parameter

$parameter = New-ParameterItem -Name 'ImageId' -Type AWS::EC2::Image::Id -Description 'The AMI to be used to generate the EC2 instance.' -Default 'ami-a99df5c9'
Add-ParameterItem -Template $template -Parameter $parameter

#---resources---
$resource = New-EC2InstanceItem -Name EC2Instance -ImageId ami-4321dead -KeyName id_rsa_usw1_dev
Add-ResourceItem -Template $template -Item $resource
 
#---generation-----------------------------------------------------------------
$template | ConvertTo-Json -Depth 16  # Depth is important
