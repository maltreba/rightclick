<#
.SYNOPSIS
Registers a per-user Windows right-click (context menu) command.

.DESCRIPTION
Creates HKCU registry entries so no Administrator prompt is required. By
 default the menu item is installed for files, folders, drives, folder
 background, and desktop background, then passes the selected path to your
 command.

.EXAMPLE
.\scripts\install-context-menu.ps1 -CommandPath "C:\Tools\rightclickwork.exe"

.EXAMPLE
.\scripts\install-context-menu.ps1 -MenuText "Send to RightClickWork" -CommandPath "C:\Tools\rightclickwork.exe" -Locations File,Directory,DirectoryBackground
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$CommandPath,

    [string]$MenuText = 'Open with RightClickWork',

    [string]$MenuKey = 'RightClickWork',

    [string]$IconPath,

    [ValidateSet('File', 'Directory', 'Drive', 'DirectoryBackground', 'DesktopBackground')]
    [string[]]$Locations = @('File', 'Directory', 'Drive', 'DirectoryBackground', 'DesktopBackground'),

    [string[]]$CommandArguments = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function ConvertTo-RegistryPath {
    param([Parameter(Mandatory = $true)][string]$ShellPath)
    return "Registry::HKEY_CURRENT_USER\Software\Classes\$ShellPath\shell\$MenuKey"
}

function Get-LocationSpec {
    param([Parameter(Mandatory = $true)][string]$Location)

    switch ($Location) {
        'File' {
            return @{ ShellPath = '*'; SelectedPathToken = '%1' }
        }
        'Directory' {
            return @{ ShellPath = 'Directory'; SelectedPathToken = '%1' }
        }
        'Drive' {
            return @{ ShellPath = 'Drive'; SelectedPathToken = '%1' }
        }
        'DirectoryBackground' {
            return @{ ShellPath = 'Directory\Background'; SelectedPathToken = '%V' }
        }
        'DesktopBackground' {
            return @{ ShellPath = 'DesktopBackground'; SelectedPathToken = '%V' }
        }
    }
}

function Join-CommandLine {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string]$SelectedPathToken,
        [string[]]$ExtraArguments = @()
    )

    $quotedArguments = foreach ($argument in $ExtraArguments) {
        '"' + ($argument -replace '"', '\"') + '"'
    }

    $parts = @('"' + $Executable + '"') + $quotedArguments + @('"' + $SelectedPathToken + '"')
    return ($parts -join ' ')
}

if (-not (Test-Path -LiteralPath $CommandPath)) {
    throw "CommandPath does not exist: $CommandPath"
}

$resolvedCommandPath = (Resolve-Path -LiteralPath $CommandPath).Path
$resolvedIconPath = $null
if ($IconPath) {
    if (-not (Test-Path -LiteralPath $IconPath)) {
        throw "IconPath does not exist: $IconPath"
    }
    $resolvedIconPath = (Resolve-Path -LiteralPath $IconPath).Path
}

foreach ($location in $Locations) {
    $spec = Get-LocationSpec -Location $location
    $menuRegistryPath = ConvertTo-RegistryPath -ShellPath $spec['ShellPath']
    $commandRegistryPath = Join-Path $menuRegistryPath 'command'
    $commandLine = Join-CommandLine -Executable $resolvedCommandPath -ExtraArguments $CommandArguments -SelectedPathToken $spec['SelectedPathToken']

    New-Item -Path $menuRegistryPath -Force | Out-Null
    New-ItemProperty -Path $menuRegistryPath -Name 'MUIVerb' -Value $MenuText -PropertyType String -Force | Out-Null
    if ($resolvedIconPath) {
        New-ItemProperty -Path $menuRegistryPath -Name 'Icon' -Value $resolvedIconPath -PropertyType String -Force | Out-Null
    }

    New-Item -Path $commandRegistryPath -Force | Out-Null
    Set-Item -Path $commandRegistryPath -Value $commandLine

    Write-Host "Installed '$MenuText' for $location -> $commandLine"
}

Write-Host 'Context menu registration complete. Restart File Explorer if the menu does not appear immediately.'
