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

    [string]$VenvPath = (Join-Path (Split-Path -Parent $PSScriptRoot) '.venv')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $VenvPath 'Scripts\python.exe'

function Find-Python {
    $commands = @(
        @{ File = 'py'; Args = @('-3') },
        @{ File = 'python'; Args = @() },
        @{ File = 'python3'; Args = @() }
    )

    foreach ($command in $commands) {
        $candidate = Get-Command $command['File'] -ErrorAction SilentlyContinue
        if ($candidate) {
            return @{ File = $candidate.Source; Args = $command['Args'] }
        }
    }

    throw 'Python 3 was not found. Install Python for the current user from python.org or Microsoft Store, then retry.'
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    $python = Find-Python
    & $($python['File']) @($python['Args'] + @('-m', 'venv', $VenvPath))
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install --editable $repoRoot
& $venvPython -m pip install -r (Join-Path $repoRoot 'requirements.txt')

if (-not $SkipOcr) {
    & $venvPython -m pip install -r (Join-Path $repoRoot 'requirements-ocr.txt')
}

$installer = Join-Path $PSScriptRoot 'install-context-menu.ps1'
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
