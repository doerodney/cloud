Set-StrictMode -Version Latest

. .\LibText.ps1

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


function New-EC2InstanceItem
{
    param(
         
        [Parameter(Mandatory=$true)]
        [string] $Name,

        [string] $AvailabilityZone = $null,

        [hashtable] $BlockDeviceMappings = $null,

        [boolean] $DisableApiTermination = $null,

        [boolean] $EbsOptimized = $null,

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

        [boolean] $Monitoring = $null,

        [string[]] $SecurityGroupIds = $null,

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
    if ($DisableApiTermination) {
        $hash[(Get-TextDisableApiTermination)] = $DisableApiTermination  
    }
    if ($EbsOptimized) {
        $hash[(Get-TextEbsOptimized)] = $EbsOptimized
    }
    if ($IamInstanceProfile) {
        $hash[(Get-TextIamInstanceProfile)] = $IamInstanceProfile
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

    
    $resource = @{ (Get-TextName) = $Name; $txtPropertySet = $hash }

    $resource
}