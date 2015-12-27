Set-StrictMode -Version Latest


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
