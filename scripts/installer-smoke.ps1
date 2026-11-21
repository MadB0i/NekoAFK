param([string]$Installer = 'D:\Projects\NekoAFK\src-tauri\target\release\bundle\nsis\NekoAFK_0.1.0_x64-setup.exe')
$ErrorActionPreference = 'Stop'
$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$installRoot = [IO.Path]::GetFullPath((Join-Path $workspaceRoot '.artifacts\installer-smoke'))
if (-not $installRoot.StartsWith($workspaceRoot + [IO.Path]::DirectorySeparatorChar)) { throw 'Installer test path is outside workspace' }
if (Test-Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\NekoAFK') { throw 'An existing user installation is present; do not replace it during testing' }
$process = Start-Process -FilePath $Installer -ArgumentList @('/S',('/D=' + $installRoot)) -WindowStyle Hidden -Wait -PassThru
if ($process.ExitCode -ne 0) { throw "Installer exited $($process.ExitCode)" }
$binary = Join-Path $installRoot 'nekoafk.exe'
if (-not (Test-Path -LiteralPath $binary)) { throw 'Installer did not produce the desktop executable' }
try {
    python (Join-Path $workspaceRoot 'tests\native_smoke.py') --exe $binary
    if ($LASTEXITCODE -ne 0) { throw 'Installed native executable failed validation' }
} finally {
    $uninstaller = Join-Path $installRoot 'uninstall.exe'
    if (Test-Path -LiteralPath $uninstaller) {
        $cleanup = Start-Process -FilePath $uninstaller -ArgumentList @('/S') -WindowStyle Hidden -Wait -PassThru
        if ($cleanup.ExitCode -ne 0) { throw "Uninstaller exited $($cleanup.ExitCode)" }
    }
}
Write-Output 'Per-user NSIS installation, installed executable validation, and uninstall passed'
