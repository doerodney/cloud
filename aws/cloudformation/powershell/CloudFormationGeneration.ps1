Set-StrictMode -Version Latest

. .\LibParameter.ps1
. .\LibText.ps1



function Add-Resource
{
    [CmdletBinding()]
    
    param(
        [hashtable] $Template,

        [hashtable] $Resource
    )

    # $Template[
}


 

function New-AWSResource
{
    [CmdletBinding()]
    
    param(
        [string] $Type,

        [string] $Name
    )

    $obj = @{
        'Type' = $Type
        'Name' = $Name
        'Properties' = @{}
    }

    $obj
}


function New-AutoScalingGroup
{
    [CmdletBinding()]
    
    param(
        [string] $Name = 'AutoScalingGroup'
    )

    [hashtable] $obj = New-AWSResource -Type 'AWS::AutoScaling::AutoScalingGroup' -Name $Name

    $obj
}


function New-CloudFormationTemplate
{
    [CmdletBinding()]
    
    param(
        [string] $Description = 'CloudFormation template generated from PowerShell',

        [string] $AWSTemplateFormatVersion = '2010-09-09'
    )

    # Initialize each section as an empty hash.
    $template = @{
        (Get-TextAWSTemplateFormatVersion) = $AWSTemplateFormatVersion
        (Get-TextConditions) = @{}
        (Get-TextDescription) = $Description
        (Get-TextMappings) = @{}
        (Get-TextMetadata) = @{}                       
        (Get-TextOutputs) = @{}
        (Get-TextParameters) = @{}
        (Get-TextResources) = @{}
    }
    
    $template
}




#---main----
$template = New-CloudFormationTemplate -Description 'Test specimen'

$parameter = New-ParameterTemplate -Name 'KeyName' -Type AWS::EC2::KeyPair::KeyName `
    -Description 'Name of an existing EC2 KeyPair file (.pem) to use to create EC2 instances' `
    -Default 'id_rsa_usw1_dev'
Add-ParameterTemplate -Template $template -Parameter $parameter

$parameter = New-ParameterTemplate -Name 'EC2InstanceType' -Type String -ConstraintDescription 'Must be a valid EC2 instance type' -Description 'EC2 instance type, reference this parameter to insure consistency' -Default 't2.micro' -AllowedValues @('t2.small', 't2.micro', 't2.medium', 't2.large', 'm3.medium', 'm3.large', 'c4.large' )   
Add-ParameterTemplate -Template $template -Parameter $parameter

$parameter = New-ParameterTemplate -Name 'ImageId' -Type AWS::EC2::Image::Id -Description 'The AMI to be used to generate the EC2 instance.' -Default 'ami-a99df5c9'
Add-ParameterTemplate -Template $template -Parameter $parameter


$template | ConvertTo-Json -Depth 16  # Depth is important
