Set-StrictMode -Version Latest


function Add-Parameter
{
    [CmdletBinding()]
    
    param(
        [hashtable] $Template,

        [hashtable] $Parameter
    )

    # Template is a hash with a Parameters key
    # The value of the Parameters key is, you guessed it, a hash.
    # key = parameter name,
    # value = parameter object
    $txtName = Get-TextName
    $txtParameters = Get-TextParameters

    $name = $Parameter[(Get-TextName)]
    $propertySet = $Parameter[(Get-TextPropertySet)]
    
    $hashParams = $Template[$txtParameters]
    # TODO:  Complain if name already exists.
    $hashParams[$name] = $propertySet   
}


function Add-Resource
{
    [CmdletBinding()]
    
    param(
        [hashtable] $Template,

        [hashtable] $Resource
    )

    # $Template[
}


function Get-TextAWSTemplateFormatVersion { 'AWSTemplateFormatVersion' }
function Get-TextConditions { 'Conditions' }
function Get-TextDescription { 'Description' } 
function Get-TextMappings { 'Mappings' }
function Get-TextMetadata { 'Metadata' }
function Get-TextName { 'Name' }
function Get-TextOutputs { 'Outputs' }
function Get-TextParameters { 'Parameters' }
function Get-TextPropertySet { 'PropertySet' }
function Get-TextResources { 'Resources' }
function Get-TextType{ 'Type' }
 

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


function New-Parameter
{
    [CmdletBinding()]
    param( 
        
        [Parameter(Mandatory=$true)]
        [string] $Name,

        [Parameter(Mandatory=$true)]
        [ValidateSet('String', 
            'Number', 
            'List<Number>', 
            'CommaDelimitedList', 
            'AWS::EC2::AvailabilityZone::Name',
            'AWS::EC2::Image::Id',
            'AWS::EC2::Instance::Id',
            'AWS::EC2::KeyPair::KeyName',
            'AWS::EC2::SecurityGroup::GroupName',
            'AWS::EC2::SecurityGroup::Id',
            'AWS::EC2::Subnet::Id',
            'AWS::EC2::Volume::Id',
            'AWS::EC2::VPC::Id',
            'AWS::Route53::HostedZone::Id',
            'List<AWS::EC2::AvailabilityZone::Name>',
            'List<AWS::EC2::Image::Id>',
            'List<AWS::EC2::Instance::Id>',
            'List<AWS::EC2::SecurityGroup::GroupName>',
            'List<AWS::EC2::SecurityGroup::Id>',
            'List<AWS::EC2::Subnet::Id>',
            'List<AWS::EC2::Volume::Id>',
            'List<AWS::EC2::VPC::Id>',
            'List<AWS::Route53::HostedZone::Id>')]
        [string] $Type = 'String',

        [string] $Default = $null,
        [switch] $NoEcho,
        [string[]] $AllowedValues = $null,
        [string] $AllowedPattern = $null,
        [int] $MaxLength = $null,
        [int] $MinLength = $null,
        [string] $Description = $null,
        [string] $ConstraintDescription = $null    
    )

    $txtType = Get-TextType

    $hash = @{
        $txtType = $Type  
    }

    if ($Default) { $hash['Default'] = $Default }
    if ($NoEcho) { $hash['NoEcho'] = $true }
    if ($AllowedValues.Count -gt 0) { $hash['AllowedValues'] = @($AllowedValues) }
    if ($AllowedPattern) { $hash['AllowedPattern'] = $AllowedPattern }
    if ($MaxLength) { $hash['MaxLength'] = $MaxLength }
    if ($MinLength) { $hash['MinLength'] = $MinLength }
    if ($Description) {$hash['Description'] = $Description }
    if ($ConstraintDescription) {
        $hash['ConstraintDescription'] = $ConstraintDescription 
    }

    $txtName = Get-TextName
    $txtPropertySet = Get-TextPropertySet

    $parameter = @{ $txtName = $Name; $txtPropertySet = $hash }

    $parameter
}


#---main----
$template = New-CloudFormationTemplate -Description 'Test specimen'

$parameter = New-Parameter -Name 'KeyName' -Type AWS::EC2::KeyPair::KeyName `
    -Description 'Name of an existing EC2 KeyPair file (.pem) to use to create EC2 instances' `
    -Default 'id_rsa_usw1_dev'
Add-Parameter -Template $template -Parameter $parameter

$parameter = New-Parameter -Name 'EC2InstanceType' -Type String -ConstraintDescription 'Must be a valid EC2 instance type' -Description 'EC2 instance type, reference this parameter to insure consistency' -Default 't2.micro' -AllowedValues @('t2.small', 't2.micro', 't2.medium', 't2.large', 'm3.medium', 'm3.large', 'c4.large' )   
Add-Parameter -Template $template -Parameter $parameter

$parameter = New-Parameter -Name 'ImageId' -Type AWS::EC2::Image::Id -Description 'The AMI to be used to generate the EC2 instance.' -Default 'ami-a99df5c9'
Add-Parameter -Template $template -Parameter $parameter


$template | ConvertTo-Json -Depth 16  # Depth is important
