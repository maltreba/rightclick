<#
.SYNOPSIS
Installs RightClick AI Markdown and registers a Windows right-click menu without Administrator privileges.

.DESCRIPTION
Creates a local Python virtual environment, installs this project into that environment,
and registers a per-user context menu item that converts selected files/folders to Markdown.
#>
[CmdletBinding()]
param(
    [string]$MenuText = 'Convert to Markdown for AI',

    [string]$MenuKey = 'RightClickAiMarkdown',

    [ValidateSet('File', 'Directory', 'Drive', 'DirectoryBackground', 'DesktopBackground')]
    [string[]]$Locations = @('File', 'Directory'),

    [switch]$SkipOcr,

    # Backward-compatible no-op: OCR dependencies are installed by default now.
    [switch]$WithOcr,

    # Default resolved in script body so $PSScriptRoot is never evaluated in
    # the param block, where it can be empty when called from a .bat file.
    [string]$VenvPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# $PSScriptRoot is empty when PowerShell is launched from cmd.exe/bat in a
# path that contains parentheses or spaces. Fall back to MyInvocation.
$scriptDir = if ($PSScriptRoot) {
    $PSScriptRoot
} else {
    Split-Path -Parent $MyInvocation.MyCommand.Definition
}

$repoRoot = Split-Path -Parent $scriptDir
if (-not $VenvPath) {
    $VenvPath = Join-Path $repoRoot '.venv'
}
$venvPython = Join-Path $VenvPath 'Scripts\python.exe'

function Get-PythonVersionText {
    param(
        [Parameter(Mandatory = $true)][string]$File,
        [string[]]$Args = @()
    )

    $versionOutput = & $File @($Args + @('--version')) 2>&1
    if ($LASTEXITCODE -ne 0) {
        return $null
    }

    return ($versionOutput | Select-Object -First 1)
}

function Test-PythonSupported {
    param(
        [Parameter(Mandatory = $true)][string]$File,
        [string[]]$Args = @()
    )

    $versionText = Get-PythonVersionText -File $File -Args $Args
    if (-not $versionText) {
        return $false
    }

    $match = [regex]::Match($versionText, 'Python\s+(\d+)\.(\d+)')
    if (-not $match.Success) {
        return $false
    }

    $major = [int]$match.Groups[1].Value
    $minor = [int]$match.Groups[2].Value
    return ($major -eq 3 -and $minor -ge 10 -and $minor -le 12)
}

function Find-Python {
    $commands = @(
        @{ File = 'py'; Args = @('-3.12') },
        @{ File = 'py'; Args = @('-3.11') },
        @{ File = 'py'; Args = @('-3.10') },
        @{ File = 'python'; Args = @() },
        @{ File = 'python3'; Args = @() },
        @{ File = 'py'; Args = @('-3') }
    )

    foreach ($command in $commands) {
        $candidate = Get-Command $command['File'] -ErrorAction SilentlyContinue
        if ($candidate -and (Test-PythonSupported -File $candidate.Source -Args $command['Args'])) {
            return @{ File = $candidate.Source; Args = $command['Args'] }
        }
    }

    throw 'Python 3.10, 3.11, or 3.12 was not found. OCR dependencies currently need prebuilt wheels, and Python 3.13/3.14 may try to compile native/Rust packages such as python-bidi. Install Python 3.12 for the current user from python.org, then retry.'
}

function Assert-VenvPythonSupported {
    if (-not (Test-PythonSupported -File $venvPython)) {
        $version = Get-PythonVersionText -File $venvPython
        throw "Existing venv uses unsupported Python $version. Delete '$VenvPath' and rerun this installer with Python 3.10, 3.11, or 3.12."
    }
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    $python = Find-Python
    & $($python['File']) @($python['Args'] + @('-m', 'venv', $VenvPath))
}

Assert-VenvPythonSupported

& $venvPython -m pip install --upgrade --only-binary=:all: pip "setuptools<82" wheel
& $venvPython -m pip install --no-build-isolation --editable $repoRoot
& $venvPython -m pip install --only-binary=:all: -r (Join-Path $repoRoot 'requirements.txt')

if (-not $SkipOcr) {
    & $venvPython -m pip install --only-binary=:all: -r (Join-Path $repoRoot 'requirements-ocr.txt')
}

$installer = Join-Path $scriptDir 'install-context-menu.ps1'
& $installer `
    -MenuText $MenuText `
    -MenuKey $MenuKey `
    -CommandPath $venvPython `
    -CommandArguments @('-m', 'rightclick_ai_markdown', '--open-output') `
    -Locations $Locations

if ($SkipOcr) {
    Write-Host 'OCR dependencies were skipped. Scanned/photo PDFs and images may produce OCR warnings until requirements-ocr.txt is installed.'
}

Write-Host "Installed '$MenuText'. Right-click a file or folder and choose the menu item to create Markdown output."
