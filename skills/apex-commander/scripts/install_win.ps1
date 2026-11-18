param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PassThruArgs
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillSource = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$TargetDir = Join-Path $HOME ".gemini\config\skills\apex-commander"

function Test-PythonWorks {
    # A Microsoft Store "execution alias" stub is found by Get-Command but exits non-zero when run,
    # so being on PATH is not enough: run it once and check the exit code.
    param([string]$Exe, [string[]]$Prefix)
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $Exe @Prefix -c "import sys" *> $null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
    finally {
        $ErrorActionPreference = $saved
    }
}

function Find-Python {
    foreach ($candidate in @(@{ Name = "python"; Prefix = @() }, @{ Name = "py"; Prefix = @("-3") })) {
        $found = @(Get-Command $candidate.Name -All -CommandType Application -ErrorAction SilentlyContinue)
        foreach ($cmd in $found) {
            if (Test-PythonWorks -Exe $cmd.Source -Prefix $candidate.Prefix) {
                return @{ Exe = $cmd.Source; Prefix = $candidate.Prefix }
            }
        }
    }
    return $null
}

function Get-FullPath([string]$Path) {
    return [IO.Path]::GetFullPath($Path).TrimEnd('\')
}

$python = Find-Python
if ($python) {
    $pyPrefix = $python.Prefix
    & $python.Exe @pyPrefix (Join-Path $ScriptDir "install_global.py") @PassThruArgs
    exit $LASTEXITCODE
}

# ---------------------------------------------------------------------------
# Fallback: no working Python (python / py -3). Plain copy only; no options.
# ---------------------------------------------------------------------------
if ($PassThruArgs -and $PassThruArgs.Count -gt 0) {
    [Console]::Error.WriteLine("[ERROR] No working Python found (python / py -3), so these options cannot be honored: $($PassThruArgs -join ' '). Install Python 3, or run without options for a plain copy.")
    exit 2
}

$src = Get-FullPath $SkillSource
$dst = Get-FullPath $TargetDir

if ($src -ieq $dst) {
    Write-Host "[OK] Source is already at target location: $dst"
    exit 0
}
if ($dst.StartsWith($src + "\", [StringComparison]::OrdinalIgnoreCase)) {
    [Console]::Error.WriteLine("[ERROR] Target $dst is inside the source bundle $src; refusing to copy a directory into itself.")
    exit 1
}
if ($src.StartsWith($dst + "\", [StringComparison]::OrdinalIgnoreCase)) {
    [Console]::Error.WriteLine("[ERROR] Source $src is inside the target $dst; replacing the target would delete the source.")
    exit 1
}

$ParentDir = Split-Path -Parent $dst
if (-not (Test-Path $ParentDir)) {
    New-Item -ItemType Directory -Force -Path $ParentDir | Out-Null
}

# Build the new copy next to the target first, so a failed copy never destroys a working install.
$Staging = "$dst.staging-$PID"
try {
    Copy-Item -Recurse -Force $src $Staging

    # Same exclusions as install_global.py.
    @(Get-ChildItem -Recurse -Force -Directory $Staging -Filter "__pycache__") | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    @(Get-ChildItem -Recurse -Force -File $Staging | Where-Object { $_.Extension -eq ".pyc" -or $_.Name -eq ".DS_Store" }) | Remove-Item -Force

    # Same CRLF -> LF normalization as install_global.py (byte-level, so any BOM is preserved).
    foreach ($f in Get-ChildItem -Recurse -Force -File $Staging) {
        if (@(".sh", ".py", ".md", ".json") -contains $f.Extension.ToLower() -or $f.Name -eq ".gitattributes") {
            $bytes = [IO.File]::ReadAllBytes($f.FullName)
            if ([Array]::IndexOf($bytes, [byte]13) -ge 0) {
                $out = New-Object 'System.Collections.Generic.List[byte]' $bytes.Length
                for ($i = 0; $i -lt $bytes.Length; $i++) {
                    if ($bytes[$i] -eq 13 -and ($i + 1) -lt $bytes.Length -and $bytes[$i + 1] -eq 10) { continue }
                    $out.Add($bytes[$i])
                }
                [IO.File]::WriteAllBytes($f.FullName, $out.ToArray())
            }
        }
    }

    # Light verification (the full compile check needs Python).
    $skillMd = Join-Path $Staging "SKILL.md"
    if (-not (Test-Path $skillMd)) { throw "Missing SKILL.md in the copied skill." }
    if (-not (Test-Path (Join-Path $Staging "scripts\auto_orchestrator.py"))) { throw "Missing scripts\auto_orchestrator.py in the copied skill." }
    $text = [IO.File]::ReadAllText($skillMd)
    if ($text -notmatch '^---\r?\n') { throw "SKILL.md does not start with YAML frontmatter ('---')." }
    if ($text -notmatch 'name:' -or $text -notmatch 'description:') { throw "SKILL.md frontmatter is missing required name or description." }

    if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
    Move-Item $Staging $dst
}
catch {
    if (Test-Path $Staging) { Remove-Item -Recurse -Force $Staging -ErrorAction SilentlyContinue }
    [Console]::Error.WriteLine("[ERROR] Install failed: $($_.Exception.Message)")
    exit 1
}

Write-Host "[OK] Installed apex-commander globally to: $dst (PowerShell fallback)"
