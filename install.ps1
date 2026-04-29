# ──────────────────────────────────────────────────────────────────────────────
#  Job Application Tracker — One-shot installer for Windows
# ──────────────────────────────────────────────────────────────────────────────
#  Run from PowerShell:
#      iwr -useb https://raw.githubusercontent.com/Sharmagowtham709/JobTracker/main/install.ps1 | iex
#  Or, after cloning:
#      powershell -ExecutionPolicy Bypass -File install.ps1
#
#  What it does:
#    1. Installs winget-managed Git if missing.
#    2. Installs uv (fast Python package/version manager) if missing.
#    3. Uses uv to install a private Python 3.12.
#    4. Clones (or updates) the JobTracker repo into %USERPROFILE%\JobTracker.
#    5. Generates the application icon.
#    6. Creates a "Job Tracker" shortcut on your Desktop.
#  Re-runnable: safe to execute multiple times.
# ──────────────────────────────────────────────────────────────────────────────

[CmdletBinding()]
param(
    [string]$InstallDir = (Join-Path $env:USERPROFILE 'JobTracker'),
    [string]$RepoUrl    = 'https://github.com/Sharmagowtham709/JobTracker.git',
    [string]$Branch     = 'main',
    [switch]$NoShortcut
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

function Write-Step($msg)  { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-OK($msg)    { Write-Host "    ✓ $msg" -ForegroundColor Green }
function Write-Warn2($msg) { Write-Host "    ! $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "    ✗ $msg" -ForegroundColor Red }

function Test-Cmd($name) {
    $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
                [System.Environment]::GetEnvironmentVariable('Path','User')
    $uvBin = Join-Path $env:USERPROFILE '.local\bin'
    if (Test-Path $uvBin -PathType Container) { $env:Path = "$uvBin;$env:Path" }
}

# ── Header ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      Job Application Tracker — Installer            ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "Install dir : $InstallDir"
Write-Host "Repo        : $RepoUrl"
Write-Host "Branch      : $Branch"

# ── 1. Git ───────────────────────────────────────────────────────────────────
Write-Step "Checking Git"
if (Test-Cmd git) {
    Write-OK ("Git found: " + (git --version))
} else {
    Write-Warn2 "Git not found — installing via winget…"
    if (-not (Test-Cmd winget)) {
        Write-Err "winget is not available. Install Git manually from https://git-scm.com/download/win"
        exit 1
    }
    winget install --id Git.Git -e --silent --accept-source-agreements --accept-package-agreements | Out-Null
    Refresh-Path
    if (-not (Test-Cmd git)) {
        Write-Err "Git installation didn't expose 'git' on PATH. Open a new PowerShell and re-run."
        exit 1
    }
    Write-OK ("Git installed: " + (git --version))
}

# ── 2. uv ────────────────────────────────────────────────────────────────────
Write-Step "Checking uv (Python manager)"
if (Test-Cmd uv) {
    Write-OK ("uv found: " + (uv --version))
} else {
    Write-Warn2 "uv not found — installing…"
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    } catch {
        Write-Err "uv install failed: $_"
        exit 1
    }
    Refresh-Path
    if (-not (Test-Cmd uv)) {
        Write-Err "uv didn't appear on PATH after install. Open a new PowerShell and re-run."
        exit 1
    }
    Write-OK ("uv installed: " + (uv --version))
}

# ── 3. Python 3.12 ───────────────────────────────────────────────────────────
Write-Step "Ensuring Python 3.12 (managed by uv)"
& uv python install 3.12 | Out-Null
Write-OK "Python 3.12 ready."

# ── 4. Clone or update the repo ──────────────────────────────────────────────
Write-Step "Setting up source at $InstallDir"
if (Test-Path (Join-Path $InstallDir '.git')) {
    Write-OK "Existing checkout found — pulling latest…"
    Push-Location $InstallDir
    try {
        & git fetch --quiet
        & git checkout --quiet $Branch
        & git pull --ff-only --quiet origin $Branch
    } finally { Pop-Location }
    Write-OK "Repo updated."
} else {
    if (Test-Path $InstallDir) {
        if (@(Get-ChildItem $InstallDir -Force).Count -gt 0) {
            Write-Err "Target $InstallDir exists and is not empty (and not a git repo). Move it or pick another -InstallDir."
            exit 1
        }
    } else {
        New-Item -ItemType Directory -Path $InstallDir | Out-Null
    }
    & git clone --branch $Branch --quiet $RepoUrl $InstallDir
    Write-OK "Repo cloned."
}

# ── 5. Icon ──────────────────────────────────────────────────────────────────
Write-Step "Generating application icon"
Push-Location $InstallDir
try {
    & uv run --python 3.12 python make_icon.py
    if (Test-Path (Join-Path $InstallDir 'tracker.ico')) {
        Write-OK "Icon generated: tracker.ico"
    } else {
        Write-Warn2 "Icon generation didn't produce tracker.ico (continuing)."
    }
} finally { Pop-Location }

# ── 6. Desktop shortcut ──────────────────────────────────────────────────────
if (-not $NoShortcut) {
    Write-Step "Creating Desktop shortcut"
    $shortcutScript = Join-Path $InstallDir 'create_shortcut.ps1'
    if (Test-Path $shortcutScript) {
        & powershell -ExecutionPolicy Bypass -File $shortcutScript | Out-Null
        Write-OK "Shortcut placed on Desktop ('Job Tracker')."
    } else {
        Write-Warn2 "create_shortcut.ps1 not found in repo — skipping shortcut."
    }
}

# ── Done ─────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "──────────────────────────────────────────────────────────" -ForegroundColor Green
Write-Host "  ✓ Install complete." -ForegroundColor Green
Write-Host "──────────────────────────────────────────────────────────" -ForegroundColor Green
Write-Host ""
Write-Host "Launch options:"
Write-Host "  • Double-click 'Job Tracker' on your Desktop"
Write-Host "  • Or from PowerShell:"
Write-Host "      cd `"$InstallDir`""
Write-Host "      uv run --python 3.12 python tracker.py"
Write-Host ""
Write-Host "To update later, click the ⟳ Update button in the app, or re-run this installer."
Write-Host ""
