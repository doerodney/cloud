Set-StrictMode -Version Latest

. .\LibText.ps1

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
