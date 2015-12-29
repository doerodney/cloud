Set-StrictMode -Version Latest

function Add-ParameterItem
{
<#
.SYNOPSIS
Adds a parameter to a template.
.DESCRIPTION
Adds a parameter object created by New-ParameterItem to a template object created by New-CFGenTemplate.
.PARAMETER Template
An object created by New-CFGenTemplate that contains objects to generate into a CloudFormation template.
.PARAMETER Parameter
A parameter object created by New-ParameterItem that describes a parameter in a CloudFormation template.
.EXAMPLE
$template = New-CFGenTemplate -Description 'Template for a demonstration project.'
$param = New-ParameterItem -Name KeyName -Type AWS::EC2::KeyPair::KeyName -Description 'Name of an existing EC2 KeyPair file (.pem) to use to create EC2 instances.' 
Add-ParamterItem -Template $template -Parameter $param
#>
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

function Add-ResourceItem
{
    [CmdletBinding()]
    
    param(
        [hashtable] $Template,

        [hashtable] $Item
    )

    # Template is a hash with a Parameters key
    # The value of the Parameters key is, you guessed it, a hash.
    # key = parameter name,
    # value = parameter object
    $txtName = Get-TextName

    # Get the name from the item.
    $name = $Item[$txtName]
    
    # Get the property set from the item
    $propertySet = $Item[(Get-TextPropertySet)]
    
    # Get the resources hash from the template.
    $hashResources = $Template[(Get-TextResources)]
    
    # TODO:  Complain if name already exists.
    # Add the item to the resources section of the template
    $hashResources[$name] = $propertySet   
}


function ConvertTo-Boolean
{
    param(
        [string] $Value
    )

    [boolean] $result = $false
    if ($Value -eq $true) { $result = $true }
    elseif ($Value -eq $false) { $result = $false }
    else {
        throw [System.ArgumentException] "Value '$Value' cannot be converted to a boolean value."
    }

    $result
}

#---Get-Text functions---------------------------------------------------------
function Get-TextAvailabilityZone { 'AvailabilityZone' }
function Get-TextAWSTemplateFormatVersion { 'AWSTemplateFormatVersion' }

function Get-TextBlockDeviceMappings { 'BlockDeviceMappings' }

function Get-TextConditions { 'Conditions' }

function Get-TextDescription { 'Description' }
function Get-TextDisableApiTermination { 'DisableApiTermination' }

function Get-TextEbsOptimized{ 'EbsOptimized' }

function Get-TextIamInstanceProfile { 'IamInstanceProfile' }
function Get-TextImageId { 'ImageId' }
function Get-TextInstanceInitiatedShutdownBehavior { 'InitiatedShutdownBehavior' }
function Get-TextInstanceType { 'InstanceType' } 

function Get-TextKernelId { 'KernelId' }
function Get-TextKeyName { 'KeyName' } 

function Get-TextMappings { 'Mappings' }
function Get-TextMetadata { 'Metadata' }
function Get-TextMonitoring { 'Monitoring' }

function Get-TextName { 'Name' }
function Get-TextNetworkInterfaces { 'NetworkInterfaces' }
function Get-TextOutputs { 'Outputs' }

function Get-TextParameters { 'Parameters' }
function Get-TextPlacementGroupName { 'PlacementGroupName' }
function Get-TextPrivateIpAddress { 'PrivateIpAddress' }
function Get-TextPropertySet { 'PropertySet' }

function Get-TextRamdiskId { 'RamdiskId' }
function Get-TextResources { 'Resources' }

function Get-TextSecurityGroupIds { 'SecurityGroupIds' }
function Get-TextSecurityGroups { 'SecurityGroups' }
function Get-TextSourceDestCheck { 'SourceDestCheck' }

function Get-TextType{ 'Type' }
#^^^-Get-Text functions--------------------------------------------------------

function New-CFGenTemplate
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


function New-EC2InstanceItem
{
    param(
         
        [Parameter(Mandatory=$true)]
        [string] $Name,

        [string] $AvailabilityZone = $null,

        [hashtable] $BlockDeviceMappings = $null,

        [string] $DisableApiTermination = $null,

        [boolean] $EbsOptimized = $false,

        [string] $IamInstanceProfile = $null,

        [Parameter(Mandatory=$true)]
        [string] $ImageId,

        [ValidateSet('stop', 'terminate')]
        [string] $InstanceInitiatedShutdownBehavior = $null,        

        [ValidateSet('m1.small',
            'm3.medium', 'm3.large',
            't2.micro', 't2.small', 't2.medium', 't2.large')]
        [string] $InstanceType = 'm1.small',

        [string] $KernelId = $null,

        [Parameter(Mandatory=$true)]
        [string] $KeyName,

        [boolean] $Monitoring = $false,

        [string[]] $NetworkInterfaces = $null,  # TODO:  Is type correct?

        [string] $PlacementGroupName = $null,

        [string] $PrivateIpAddress = $null,

        [string] $RamdiskId = $null,

        [string[]] $SecurityGroupIds = $null,

        [string[]] $SecurityGroups  = $null,

        [string] $SourceDestCheck = $null,

        [string[]] $UserData = $null
    )

    $txtName = Get-TextName
    $txtPropertySet = Get-TextPropertySet

    $txtType = Get-TextType

    # Add required values to the hash. 
    $hash = @{
        (Get-TextType) = 'AWS::EC2::Instance'
        (Get-TextImageId) = $ImageId
        (Get-TextInstanceType) = $InstanceType
        (Get-TextKeyName) = $KeyName
        
    }

    # Add optional args as defined. 
    if ($AvailabilityZone) {
        $hash[(Get-TextAvailabilityZone)] = $AvailabilityZone
    }
    if ($BlockDeviceMappings) {
        $hash[(Get-TextBlockDeviceMappings)] = $BlockDeviceMappings
    }
    if ($DisableApiTermination -eq $true) {
        $hash[(Get-TextDisableApiTermination)] = $DisableApiTermination  
    }
    if ($EbsOptimized -eq $true) {
        $hash[(Get-TextEbsOptimized)] = $EbsOptimized
    }
    if ($IamInstanceProfile) {
        $hash[(Get-TextIamInstanceProfile)] = $IamInstanceProfile
    }
    if ($DisableApiTermination) {
        $hash[(Get-TextDisableApiTermination)] = $true
    }
    if ($InstanceInitiatedShutdownBehavior) {
        $hash[(Get-TextInstanceInitiatedShutdownBehavior)] = $InstanceInitiatedShutdownBehavior
    }
    if ($KernelId) {
        $hash[(Get-TextKernelId)] = $KernelId   
    }
    if ($Monitoring) {
        $hash[(Get-TextMonitoring)] = $Monitoring
    }
    if ($NetworkInterfaces) {
        $hash[(Get-TextNetworkInterfaces)] = $NetworkInterfaces
    }
    if ($PlacementGroupName) {
        $hash[(Get-TextPlacementGroupName)] = $PlacementGroupName
    }
    if ($PrivateIpAddress) {
        $hash[(Get-TextPrivateIpAddress)] = $PrivateIpAddress
    }
    if ($RamdiskId) {
        $hash[(Get-TextRamdiskId)] = $RamdiskId
    }
    if ($SecurityGroupIds) {
        $hash[(Get-TextSecurityGroupIds)] = $SecurityGroupIds
    }
    if ($SecurityGroups) {
        $hash[(Get-TextSecurityGroups)] = $SecurityGroups
    }
    
    $resource = @{ (Get-TextName) = $Name; $txtPropertySet = $hash }

    $resource
}

function New-ParameterItem
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
    if (@($AllowedValues).Count -gt 0) { $hash['AllowedValues'] = @($AllowedValues) }
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

