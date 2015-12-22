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
    $nameParameters = Get-NameParameters
    $Template[$nameParameters].Add($Parameter['Name'], $Parameter)
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


function Get-NameAWSTemplateFormatVersion { 'AWSTemplateFormatVersion' }
function Get-NameConditions { 'Conditions' }
function Get-NameDescription { 'Description' } 
function Get-NameMappings { 'Mappings' }
function Get-NameMetadata { 'Metadata' }
function Get-NameOutputs { 'Outputs' }
function Get-NameParameters { 'Parameters' }
function Get-NameResources { 'Resources' }
 

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

    $template = @{
        (Get-NameAWSTemplateFormatVersion) = $AWSTemplateFormatVersion
        (Get-NameDescription) = $Description
        (Get-NameMetadata) = @{}
        (Get-NameMappings) = @{}
        (Get-NameConditions) = @{}
        (Get-NameResources) = @{}
        (Get-NameOutputs) = @{}
    }
    
    $template
}


function New-Parameter
{
    [CmdletBinding()]
    param( 
        [string] $Name,
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
        [string[]] $AllowedValues = @(),
        [string] $AllowedPattern = $null,
        [int] $MaxLength = $null,
        [int] $MinLength = $null,
        [string] $Description = $null,
        [string] $ConstraintDescription = $null    
    )

    $hash = @{
        'Type' = $Type  
    }

    if ($Default) { $hash['Default'] = $Default }
    if ($NoEcho) { $hash['NoEcho'] = $true }
    if ($AllowedValues.Count -gt 0) { $hash['AllowedValues'] = $AllowedValues }
    if ($AllowedPattern) { $hash['AllowedPattern'] = $AllowedPattern }
    if ($MaxLength) { $hash['MaxLength'] = $MaxLength }
    if ($MinLength) { $hash['MinLength'] = $MinLength }
    if ($Description) {$hash['Description'] = $Description }
    if ($ConstraintDescription) {
        $hash['ConstraintDescription'] = $ConstraintDescription 
    }

    $parameter = @{ $Name = $hash }

    $parameter
}

$parameter = New-Parameter -Name 'Tuna' -Type AWS::EC2::AvailabilityZone::Name `
    -Description 'Availability Zone' `
    -AllowedValues @(1,2,3)
$parameter | ConvertTo-Json

#$template = New-CloudFormationTemplate
#$template | ConvertTo-Json
 