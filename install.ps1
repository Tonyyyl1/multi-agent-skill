param(
    [switch]$WithRule,
    [switch]$VerifyOnly,
    [switch]$Uninstall,
    [string]$ConfigDir = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallPy = Join-Path $RepoRoot "install.py"
$SkillSource = Join-Path $RepoRoot "skills\apex-commander"

$PyArgs = @()
if ($WithRule)   { $PyArgs += "--with-rule" }
if ($VerifyOnly) { $PyArgs += "--verify-only" }
if ($Uninstall)  { $PyArgs += "--uninstall" }
if ($ConfigDir)  { $PyArgs += @("--config-dir", $ConfigDir) }

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python $InstallPy @PyArgs
    exit $LASTEXITCODE
}
elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $InstallPy @PyArgs
    exit $LASTEXITCODE
}
else {
    $BaseConfig = if ($ConfigDir) { $ConfigDir } else { Join-Path $HOME ".gemini\config" }
    $TargetDir = Join-Path $BaseConfig "skills\apex-commander"
    if ($Uninstall) {
        if (Test-Path $TargetDir) { Remove-Item -Recurse -Force $TargetDir }
        Write-Host "[OK] Removed $TargetDir"
        exit 0
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetDir) | Out-Null
    if (Test-Path $TargetDir) { Remove-Item -Recurse -Force $TargetDir }
    Copy-Item -Recurse -Force $SkillSource $TargetDir
    Write-Host "[OK] Installed apex-commander to: $TargetDir (PowerShell fallback)"
}
