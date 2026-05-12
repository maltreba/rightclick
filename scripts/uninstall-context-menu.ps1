<#
.SYNOPSIS
Removes the per-user Windows right-click (context menu) command created by install-context-menu.ps1.

.EXAMPLE
.\scripts\uninstall-context-menu.ps1

.EXAMPLE
.\scripts\uninstall-context-menu.ps1 -MenuKey RightClickWork -Locations File,Directory
#>
[CmdletBinding()]
param(
    [string]$MenuKey = 'RightClickWork',

    [ValidateSet('File', 'Directory', 'Drive', 'DirectoryBackground', 'DesktopBackground')]
    [string[]]$Locations = @('File', 'Directory', 'Drive', 'DirectoryBackground', 'DesktopBackground')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function ConvertTo-RegistryPath {
    param([Parameter(Mandatory = $true)][string]$ShellPath)
    return "Registry::HKEY_CURRENT_USER\Software\Classes\$ShellPath\shell\$MenuKey"
}

function Get-ShellPath {
    param([Parameter(Mandatory = $true)][string]$Location)

    switch ($Location) {
        'File' { return '*' }
        'Directory' { return 'Directory' }
        'Drive' { return 'Drive' }
        'DirectoryBackground' { return 'Directory\Background' }
        'DesktopBackground' { return 'DesktopBackground' }
    }
}

foreach ($location in $Locations) {
    $menuRegistryPath = ConvertTo-RegistryPath -ShellPath (Get-ShellPath -Location $location)

    if (Test-Path -LiteralPath $menuRegistryPath) {
        Remove-Item -LiteralPath $menuRegistryPath -Recurse -Force
        Write-Host "Removed context menu entry for $location"
    }
    else {
        Write-Host "No context menu entry found for $location"
    }
}

Write-Host 'Context menu removal complete.'
