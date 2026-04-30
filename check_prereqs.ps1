# ──────────────────────────────────────────────────────────────────────────────
#  Job Application Tracker — Prerequisite checker
# ──────────────────────────────────────────────────────────────────────────────
#  Run from PowerShell (no admin needed):
#      powershell -ExecutionPolicy Bypass -File check_prereqs.ps1
#
#  Verifies everything the tracker needs at runtime AND at install time.
#  Exits 0 if all required checks pass, non-zero otherwise.
# ──────────────────────────────────────────────────────────────────────────────

[CmdletBinding()]
param(
    [string]$InstallDir = (Join-Path $env:USERPROFILE 'JobTracker'),
    [string]$RepoUrl    = 'https://github.com/Sharmagowtham709/JobTracker.git'
)

$ErrorActionPreference = 'Continue'
$ProgressPreference    = 'SilentlyContinue'

$script:Failures = 0
$script:Warnings = 0

function Write-Header($msg) {
    Write-Host ""
    Write-Host "── $msg " -ForegroundColor Cyan -NoNewline
    Write-Host ("─" * [Math]::Max(0, 60 - $msg.Length)) -ForegroundColor Cyan
}
function PassMsg($msg)  { Write-Host "  [PASS] $msg" -ForegroundColor Green }
function FailMsg($msg)  { Write-Host "  [FAIL] $msg" -ForegroundColor Red;    $script:Failures++ }
function WarnMsg($msg)  { Write-Host "  [WARN] $msg" -ForegroundColor Yellow; $script:Warnings++ }
function InfoMsg($msg)  { Write-Host "         $msg" -ForegroundColor DarkGray }

function Test-Cmd($name) { $null -ne (Get-Command $name -ErrorAction SilentlyContinue) }

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
                [System.Environment]::GetEnvironmentVariable('Path','User')
    $uvBin = Join-Path $env:USERPROFILE '.local\bin'
    if (Test-Path $uvBin -PathType Container) { $env:Path = "$uvBin;$env:Path" }
}
Refresh-Path

# ── Header ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Job Application Tracker — Prerequisite Check      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "Install dir : $InstallDir"

# ── 1. Operating system ──────────────────────────────────────────────────────
Write-Header "Operating system"
$os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
if ($os) {
    PassMsg "$($os.Caption) — build $($os.BuildNumber)"
} else {
    FailMsg "Could not query OS information."
}

# ── 2. PowerShell ────────────────────────────────────────────────────────────
Write-Header "PowerShell"
$psv = $PSVersionTable.PSVersion
if ($psv.Major -ge 5) {
    PassMsg "PowerShell $psv"
} else {
    FailMsg "PowerShell $psv (need >= 5.0)"
}

# ── 3. winget (used by installer to fetch Git) ───────────────────────────────
Write-Header "winget (only needed for first-time install)"
if (Test-Cmd winget) {
    PassMsg ("winget found: " + ((winget --version) 2>$null))
} else {
    WarnMsg "winget not found. install.ps1 needs it to install Git automatically."
    InfoMsg "If Git is already installed, you can skip winget."
    InfoMsg "Otherwise: install 'App Installer' from the Microsoft Store."
}

# ── 4. Git ───────────────────────────────────────────────────────────────────
Write-Header "Git (required — used for clone + in-app updates)"
if (Test-Cmd git) {
    PassMsg ((git --version) 2>$null)
} else {
    FailMsg "Git is not on PATH."
    InfoMsg "Fix: run install.ps1, OR install from https://git-scm.com/download/win"
}

# ── 5. uv (Python manager) ───────────────────────────────────────────────────
Write-Header "uv (required — manages the private Python 3.12)"
if (Test-Cmd uv) {
    PassMsg ((uv --version) 2>$null)
} else {
    FailMsg "uv is not on PATH."
    InfoMsg "Fix: run install.ps1, OR: irm https://astral.sh/uv/install.ps1 | iex"
}

# ── 6. Python 3.12 via uv ────────────────────────────────────────────────────
Write-Header "Python 3.12 (managed by uv)"
if (Test-Cmd uv) {
    $pyList = (uv python list --only-installed 2>$null)
    if ($pyList -match '3\.12') {
        PassMsg "Python 3.12 is installed under uv."
    } else {
        WarnMsg "Python 3.12 not yet installed via uv."
        InfoMsg "Fix: uv python install 3.12"
    }
} else {
    WarnMsg "Skipped — uv is not available."
}

# ── 7. tkinter inside that Python ────────────────────────────────────────────
Write-Header "Tkinter GUI runtime (needed by tracker.py)"
if (Test-Cmd uv) {
    $tk = (uv run --python 3.12 --no-project python -c "import tkinter,sys;print(tkinter.TkVersion)" 2>$null)
    if ($LASTEXITCODE -eq 0 -and $tk) {
        PassMsg "tkinter $tk available in uv-managed Python 3.12"
    } else {
        FailMsg "tkinter import failed in uv-managed Python 3.12."
        InfoMsg "Fix: uv python install 3.12 --reinstall"
    }
} else {
    WarnMsg "Skipped — uv is not available."
}

# ── 8. Repo checkout ─────────────────────────────────────────────────────────
Write-Header "Repo checkout at $InstallDir"
$gitDir = Join-Path $InstallDir '.git'
$tracker = Join-Path $InstallDir 'tracker.py'
if (Test-Path $tracker) {
    PassMsg "tracker.py found."
} else {
    FailMsg "tracker.py is missing from $InstallDir."
    InfoMsg "Fix: run install.ps1 to clone the repo."
}
if (Test-Path $gitDir) {
    PassMsg ".git directory present — in-app Update will work."
    if (Test-Cmd git) {
        Push-Location $InstallDir
        try {
            $remote = (git config --get remote.origin.url) 2>$null
            if ($remote) { InfoMsg "remote.origin.url = $remote" }
        } finally { Pop-Location }
    }
} else {
    WarnMsg "No .git directory — in-app Update button will refuse to run."
    InfoMsg "Fix: re-install via install.ps1 (which clones via git)."
}

# ── 9. Generated icon ────────────────────────────────────────────────────────
Write-Header "Application icon"
$ico = Join-Path $InstallDir 'tracker.ico'
if (Test-Path $ico) {
    PassMsg "tracker.ico present."
} else {
    WarnMsg "tracker.ico missing (the app will still run, but the shortcut will use a default icon)."
    InfoMsg "Fix: cd $InstallDir; uv run --python 3.12 python make_icon.py"
}

# ── 10. Desktop shortcut ─────────────────────────────────────────────────────
Write-Header "Desktop shortcut"
$desktop = [Environment]::GetFolderPath('Desktop')
$lnk = Join-Path $desktop 'Job Tracker.lnk'
if (Test-Path $lnk) {
    PassMsg "'Job Tracker' shortcut found on Desktop."
} else {
    WarnMsg "'Job Tracker.lnk' not on Desktop."
    InfoMsg "Fix: powershell -ExecutionPolicy Bypass -File `"$InstallDir\create_shortcut.ps1`""
}

# ── 11. GitHub reachability ──────────────────────────────────────────────────
Write-Header "Network — github.com reachable"
try {
    $resp = Invoke-WebRequest -Uri 'https://github.com' -UseBasicParsing -TimeoutSec 8 -Method Head
    if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400) {
        PassMsg "github.com responded (HTTP $($resp.StatusCode))."
    } else {
        WarnMsg "github.com responded with HTTP $($resp.StatusCode)."
    }
} catch {
    WarnMsg "Could not reach github.com — install/update will fail offline."
}

# ── Summary ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "──────────────────────────────────────────────────────────" -ForegroundColor Cyan
if ($Failures -eq 0 -and $Warnings -eq 0) {
    Write-Host "  All prerequisites satisfied. You're good to go." -ForegroundColor Green
} elseif ($Failures -eq 0) {
    Write-Host "  $Warnings warning(s), 0 failures — the app will run, but some features may not." -ForegroundColor Yellow
} else {
    Write-Host "  $Failures failure(s), $Warnings warning(s) — fix the [FAIL] items above before running the app." -ForegroundColor Red
}
Write-Host "──────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host ""

if ($Failures -gt 0) { exit 1 } else { exit 0 }
