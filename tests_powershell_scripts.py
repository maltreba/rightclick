from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).parent / "scripts"
POWERSHELL_SCRIPTS = sorted(SCRIPT_DIR.glob("*.ps1"))


def read_script(name: str) -> str:
    return (SCRIPT_DIR / name).read_text(encoding="utf-8")


def test_all_powershell_scripts_use_strict_error_handling():
    assert POWERSHELL_SCRIPTS, "Expected at least one PowerShell script to test."

    for script in POWERSHELL_SCRIPTS:
        content = script.read_text(encoding="utf-8")
        assert "Set-StrictMode -Version Latest" in content, script
        assert "$ErrorActionPreference = 'Stop'" in content, script
        assert content.endswith("\n"), script


def test_generic_context_menu_installer_registers_per_user_entries_and_command_arguments():
    content = read_script("install-context-menu.ps1")

    assert "HKEY_CURRENT_USER\\Software\\Classes" in content
    assert "[string[]]$CommandArguments" in content
    assert "Join-CommandLine" in content
    assert 'Set-Item -Path $commandRegistryPath -Value $commandLine' in content
    assert "Set-ItemProperty -Path $commandRegistryPath -Name '(default)'" not in content

    for location in ["File", "Directory", "Drive", "DirectoryBackground", "DesktopBackground"]:
        assert location in content

    assert "SelectedPathToken = '%1'" in content
    assert "SelectedPathToken = '%V'" in content
    assert "$spec['ShellPath']" in content
    assert "$spec['SelectedPathToken']" in content
    assert "$spec.ShellPath" not in content
    assert "$spec.SelectedPathToken" not in content


def test_ai_markdown_installer_creates_local_venv_and_registers_module_command():
    content = read_script("install-ai-markdown-context-menu.ps1")

    assert "RightClickAiMarkdown" in content
    assert "Convert to Markdown for AI" in content
    assert "'.venv'" in content
    assert "-m', 'venv'" in content
    assert "-m pip install --editable $repoRoot" in content
    assert "requirements.txt" in content
    assert "requirements-ocr.txt" in content
    assert "if ($WithOcr)" in content
    assert "install-context-menu.ps1" in content
    assert "-CommandPath $venvPython" in content
    assert "'-m', 'rightclick_ai_markdown', '--open-output'" in content
    assert "$python['File']" in content
    assert "$python['Args']" in content
    assert "$python.File" not in content
    assert "$python.Args" not in content


def test_context_menu_uninstaller_removes_expected_registry_locations():
    content = read_script("uninstall-context-menu.ps1")

    assert "HKEY_CURRENT_USER\\Software\\Classes" in content
    assert "Remove-Item -LiteralPath $menuRegistryPath -Recurse -Force" in content
    assert "RightClickWork" in content

    for shell_path in ["'*'", "'Directory'", "'Drive'", "'Directory\\Background'", "'DesktopBackground'"]:
        assert shell_path in content


def test_powershell_scripts_parse_when_pwsh_is_available():
    pwsh = shutil.which("pwsh")
    if not pwsh:
        pytest.skip("pwsh is not installed in this environment; static PowerShell script tests still run.")

    for script in POWERSHELL_SCRIPTS:
        command = (
            "$tokens = $null; $errors = $null; "
            f"[System.Management.Automation.Language.Parser]::ParseFile('{script}', [ref]$tokens, [ref]$errors) | Out-Null; "
            "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
        )
        subprocess.run([pwsh, "-NoProfile", "-Command", command], check=True)
