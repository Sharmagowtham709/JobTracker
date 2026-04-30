# ==============================================================================
#  Job Application Tracker - Installer + Prerequisite Check (Windows)
# ==============================================================================
#  Run from PowerShell:
#      iwr -useb https://raw.githubusercontent.com/Sharmagowtham709/JobTracker/main/install.ps1 | iex
#  Or, after cloning:
#      powershell -ExecutionPolicy Bypass -File install.ps1
#
#  Verify-only mode (no install actions, just report status):
#      powershell -ExecutionPolicy Bypass -File install.ps1 -CheckOnly
#
#  Install steps (default mode):
#    1. Installs winget-managed Git if missing.
#    2. Installs uv (Python version manager) if missing.
#    3. Uses uv to install a private Python 3.12.
#    4. Clones (or updates) the repo into %USERPROFILE%\JobTracker.
#    5. Generates the application icon.
#    6. Creates a "Job Tracker" shortcut on your Desktop.
#    7. Runs the prerequisite check at the end.
#  Re-runnable: safe to execute multiple times.
# ==============================================================================

[CmdletBinding()]
param(
    [string]$InstallDir = (Join-Path $env:USERPROFILE 'JobTracker'),
    [string]$RepoUrl    = 'https://github.com/Sharmagowtham709/JobTracker.git',
    [string]$Branch     = 'main',
    [switch]$NoShortcut,
    [switch]$CheckOnly,
    [switch]$SkipCheck,
    [switch]$NoFix
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

function Write-Step($msg)  { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-OK($msg)    { Write-Host "    [OK]   $msg" -ForegroundColor Green }
function Write-Warn2($msg) { Write-Host "    [WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "    [FAIL] $msg" -ForegroundColor Red }

function Test-Cmd($name) { $null -ne (Get-Command $name -ErrorAction SilentlyContinue) }

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
                [System.Environment]::GetEnvironmentVariable('Path','User')
    $uvBin = Join-Path $env:USERPROFILE '.local\bin'
    if (Test-Path $uvBin -PathType Container) { $env:Path = "$uvBin;$env:Path" }
}

# ------------------------------------------------------------------------------
# Prerequisite check (used by -CheckOnly and at the end of an install)
# ------------------------------------------------------------------------------
function Invoke-PrereqCheck {
    param(
        [string]$Dir,
        [bool]$Fix = $true
    )

    $script:Failures = 0
    $script:Warnings = 0

    function Section($t) {
        Write-Host ""
        Write-Host ("-- " + $t) -ForegroundColor Cyan
    }
    function P($m) { Write-Host "   [PASS] $m" -ForegroundColor Green }
    function F($m) { Write-Host "   [FAIL] $m" -ForegroundColor Red;    $script:Failures++ }
    function W($m) { Write-Host "   [WARN] $m" -ForegroundColor Yellow; $script:Warnings++ }
    function I($m) { Write-Host "          $m" -ForegroundColor DarkGray }
    function Fixing($m) { Write-Host "   [FIX]  $m" -ForegroundColor Magenta }

    Refresh-Path

    Section "Operating system"
    $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
    if ($os) { P "$($os.Caption) (build $($os.BuildNumber))" } else { F "Could not query OS info." }

    Section "PowerShell"
    $psv = $PSVersionTable.PSVersion
    if ($psv.Major -ge 5) { P "PowerShell $psv" } else { F "PowerShell $psv (need >= 5.0)" }

    Section "winget (only needed at first install)"
    if (Test-Cmd winget) {
        P ("winget " + ((winget --version) 2>$null))
    } else {
        W "winget not found. Needed only if Git is missing."
        I "Install 'App Installer' from the Microsoft Store if Git is also missing."
    }

    Section "Git (required for clone + in-app Update)"
    if (Test-Cmd git) {
        P ((git --version) 2>$null)
    } elseif ($Fix) {
        Fixing "Installing Git via winget..."
        if (Test-Cmd winget) {
            try {
                winget install --id Git.Git -e --silent --accept-source-agreements --accept-package-agreements | Out-Null
                Refresh-Path
            } catch { I "winget install raised: $_" }
            if (Test-Cmd git) { P ("Git installed: " + (git --version)) }
            else { F "Git install did not expose 'git' on PATH (open a new shell)." }
        } else {
            F "winget unavailable; cannot auto-install Git. See https://git-scm.com/download/win"
        }
    } else {
        F "Git is not on PATH."
        I "Fix: re-run install.ps1, or install from https://git-scm.com/download/win"
    }

    Section "uv (required - manages private Python 3.12)"
    if (Test-Cmd uv) {
        P ((uv --version) 2>$null)
    } elseif ($Fix) {
        Fixing "Installing uv from astral.sh..."
        try {
            Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
            Refresh-Path
        } catch { I "uv install raised: $_" }
        if (Test-Cmd uv) { P ("uv installed: " + (uv --version)) }
        else { F "uv did not appear on PATH after install (open a new shell)." }
    } else {
        F "uv is not on PATH."
        I "Fix: re-run install.ps1, or: irm https://astral.sh/uv/install.ps1 | iex"
    }

    Section "Python 3.12 (managed by uv)"
    if (Test-Cmd uv) {
        $pyList = (uv python list --only-installed 2>$null)
        if ($pyList -match '3\.12') {
            P "Python 3.12 installed under uv."
        } elseif ($Fix) {
            Fixing "Installing Python 3.12 via uv..."
            & uv python install 3.12 | Out-Null
            $pyList2 = (uv python list --only-installed 2>$null)
            if ($pyList2 -match '3\.12') { P "Python 3.12 installed under uv." }
            else { F "uv python install 3.12 failed." }
        } else {
            W "Python 3.12 not yet installed via uv."
            I "Fix: uv python install 3.12"
        }
    } else { W "Skipped - uv not available." }

    Section "Tkinter GUI runtime"
    if (Test-Cmd uv) {
        $tk = (uv run --python 3.12 --no-project python -c "import tkinter,sys;print(tkinter.TkVersion)" 2>$null)
        if ($LASTEXITCODE -eq 0 -and $tk) {
            P "tkinter $tk available in uv-managed Python 3.12"
        } elseif ($Fix) {
            Fixing "Reinstalling Python 3.12 to restore tkinter..."
            & uv python install 3.12 --reinstall | Out-Null
            $tk2 = (uv run --python 3.12 --no-project python -c "import tkinter,sys;print(tkinter.TkVersion)" 2>$null)
            if ($LASTEXITCODE -eq 0 -and $tk2) { P "tkinter $tk2 available." }
            else { F "tkinter still not importable after reinstall." }
        } else {
            F "tkinter import failed in uv-managed Python 3.12."
            I "Fix: uv python install 3.12 --reinstall"
        }
    } else { W "Skipped - uv not available." }

    Section "Repo checkout at $Dir"
    $tracker = Join-Path $Dir 'tracker.py'
    $gitDir  = Join-Path $Dir '.git'
    if (Test-Path $tracker) { P "tracker.py present." } else { F "tracker.py missing in $Dir." }
    if (Test-Path $gitDir) {
        P ".git directory present (in-app Update will work)."
        if (Test-Cmd git) {
            Push-Location $Dir
            try {
                $remote = (git config --get remote.origin.url) 2>$null
                if ($remote) { I "remote.origin.url = $remote" }
            } finally { Pop-Location }
        }
    } elseif ($Fix -and (Test-Cmd git)) {
        Fixing "Cloning repo into $Dir..."
        try {
            if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir | Out-Null }
            if (@(Get-ChildItem $Dir -Force -ErrorAction SilentlyContinue).Count -gt 0) {
                W "Target $Dir is not empty; skipping clone (move it aside and re-run)."
            } else {
                & git clone --branch $Branch --quiet $RepoUrl $Dir
                if (Test-Path (Join-Path $Dir '.git')) { P "Repo cloned." } else { F "Clone failed." }
            }
        } catch { F "Clone failed: $_" }
    } else {
        W "No .git directory - in-app Update button will refuse to run."
        I "Fix: re-run install.ps1 (which clones via git)."
    }

    Section "Application icon"
    if (Test-Path (Join-Path $Dir 'tracker.ico')) {
        P "tracker.ico present."
    } elseif ($Fix -and (Test-Cmd uv) -and (Test-Path (Join-Path $Dir 'make_icon.py'))) {
        Fixing "Generating tracker.ico via make_icon.py..."
        Push-Location $Dir
        try { & uv run --python 3.12 python make_icon.py | Out-Null } finally { Pop-Location }
        if (Test-Path (Join-Path $Dir 'tracker.ico')) { P "tracker.ico generated." }
        else { W "Icon generation did not produce tracker.ico." }
    } else {
        W "tracker.ico missing."
        I "Fix: cd `"$Dir`"; uv run --python 3.12 python make_icon.py"
    }

    Section "Desktop shortcut"
    $lnk = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Job Tracker.lnk'
    $shortcutScript = Join-Path $Dir 'create_shortcut.ps1'
    if (Test-Path $lnk) {
        P "'Job Tracker' shortcut found on Desktop."
    } elseif ($Fix -and (Test-Path $shortcutScript)) {
        Fixing "Creating Desktop shortcut..."
        & powershell -ExecutionPolicy Bypass -File $shortcutScript | Out-Null
        if (Test-Path $lnk) { P "Shortcut created." } else { W "Shortcut script ran but Desktop\Job Tracker.lnk not found." }
    } else {
        W "'Job Tracker.lnk' not on Desktop."
        I "Fix: powershell -ExecutionPolicy Bypass -File `"$Dir\create_shortcut.ps1`""
    }

    Section "Network - github.com reachable"
    try {
        $resp = Invoke-WebRequest -Uri 'https://github.com' -UseBasicParsing -TimeoutSec 8 -Method Head
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400) {
            P "github.com responded (HTTP $($resp.StatusCode))."
        } else {
            W "github.com responded with HTTP $($resp.StatusCode)."
        }
    } catch {
        W "Could not reach github.com - install/update will fail offline."
    }

    Write-Host ""
    Write-Host "----------------------------------------------------------" -ForegroundColor Cyan
    if ($script:Failures -eq 0 -and $script:Warnings -eq 0) {
        Write-Host "  All prerequisites satisfied." -ForegroundColor Green
    } elseif ($script:Failures -eq 0) {
        Write-Host ("  {0} warning(s), 0 failures - app will run." -f $script:Warnings) -ForegroundColor Yellow
    } else {
        Write-Host ("  {0} failure(s), {1} warning(s) - fix [FAIL] items above." -f $script:Failures, $script:Warnings) -ForegroundColor Red
    }
    Write-Host "----------------------------------------------------------" -ForegroundColor Cyan
    Write-Host ""

    return $script:Failures
}

# ------------------------------------------------------------------------------
# Header
# ------------------------------------------------------------------------------
Write-Host ""
if ($CheckOnly) {
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "   Job Application Tracker - Prerequisite Check (-CheckOnly)" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "Install dir : $InstallDir"
    $rc = Invoke-PrereqCheck -Dir $InstallDir -Fix:(-not $NoFix)
    if ($rc -gt 0) { exit 1 } else { exit 0 }
}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "      Job Application Tracker - Installer" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Install dir : $InstallDir"
Write-Host "Repo        : $RepoUrl"
Write-Host "Branch      : $Branch"

# ------------------------------------------------------------------------------
# Pre-install snapshot of prerequisites (informational; the installer fixes
# anything missing). Skipped with -SkipCheck.
# ------------------------------------------------------------------------------
if (-not $SkipCheck) {
    Write-Step "Pre-install prerequisite snapshot"
    [void](Invoke-PrereqCheck -Dir $InstallDir -Fix:(-not $NoFix))
}

# ------------------------------------------------------------------------------
# 1. Git
# ------------------------------------------------------------------------------
Write-Step "Checking Git"
if (Test-Cmd git) {
    Write-OK ("Git found: " + (git --version))
} else {
    Write-Warn2 "Git not found - installing via winget..."
    if (-not (Test-Cmd winget)) {
        Write-Err "winget not available. Install Git manually: https://git-scm.com/download/win"
        exit 1
    }
    winget install --id Git.Git -e --silent --accept-source-agreements --accept-package-agreements | Out-Null
    Refresh-Path
    if (-not (Test-Cmd git)) {
        Write-Err "Git did not appear on PATH after install. Open a new PowerShell and re-run."
        exit 1
    }
    Write-OK ("Git installed: " + (git --version))
}

# ------------------------------------------------------------------------------
# 2. uv
# ------------------------------------------------------------------------------
Write-Step "Checking uv (Python manager)"
if (Test-Cmd uv) {
    Write-OK ("uv found: " + (uv --version))
} else {
    Write-Warn2 "uv not found - installing..."
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    } catch {
        Write-Err "uv install failed: $_"
        exit 1
    }
    Refresh-Path
    if (-not (Test-Cmd uv)) {
        Write-Err "uv did not appear on PATH after install. Open a new PowerShell and re-run."
        exit 1
    }
    Write-OK ("uv installed: " + (uv --version))
}

# ------------------------------------------------------------------------------
# 3. Python 3.12
# ------------------------------------------------------------------------------
Write-Step "Ensuring Python 3.12 (managed by uv)"
& uv python install 3.12 | Out-Null
Write-OK "Python 3.12 ready."

# ------------------------------------------------------------------------------
# 4. Clone or update the repo
# ------------------------------------------------------------------------------
Write-Step "Setting up source at $InstallDir"
if (Test-Path (Join-Path $InstallDir '.git')) {
    Write-OK "Existing checkout found - pulling latest..."
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
            Write-Err "Target $InstallDir exists and is not empty. Move it or pick another -InstallDir."
            exit 1
        }
    } else {
        New-Item -ItemType Directory -Path $InstallDir | Out-Null
    }
    & git clone --branch $Branch --quiet $RepoUrl $InstallDir
    Write-OK "Repo cloned."
}

# ------------------------------------------------------------------------------
# 5. Icon
# ------------------------------------------------------------------------------
Write-Step "Generating application icon"
Push-Location $InstallDir
try {
    & uv run --python 3.12 python make_icon.py
    if (Test-Path (Join-Path $InstallDir 'tracker.ico')) {
        Write-OK "Icon generated: tracker.ico"
    } else {
        Write-Warn2 "Icon generation did not produce tracker.ico (continuing)."
    }
} finally { Pop-Location }

# ------------------------------------------------------------------------------
# 6. Desktop shortcut
# ------------------------------------------------------------------------------
if (-not $NoShortcut) {
    Write-Step "Creating Desktop shortcut"
    $shortcutScript = Join-Path $InstallDir 'create_shortcut.ps1'
    if (Test-Path $shortcutScript) {
        & powershell -ExecutionPolicy Bypass -File $shortcutScript | Out-Null
        Write-OK "Shortcut placed on Desktop ('Job Tracker')."
    } else {
        Write-Warn2 "create_shortcut.ps1 not found in repo - skipping shortcut."
    }
}

# ------------------------------------------------------------------------------
# Done
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "----------------------------------------------------------" -ForegroundColor Green
Write-Host "  Install complete." -ForegroundColor Green
Write-Host "----------------------------------------------------------" -ForegroundColor Green

if (-not $SkipCheck) {
    Write-Step "Post-install prerequisite verification"
    [void](Invoke-PrereqCheck -Dir $InstallDir -Fix:$false)
}

Write-Host ""
Write-Host "Launch options:"
Write-Host "  - Double-click 'Job Tracker' on your Desktop"
Write-Host "  - Or from PowerShell:"
Write-Host "      cd `"$InstallDir`""
Write-Host "      uv run --python 3.12 python tracker.py"
Write-Host ""
Write-Host "To update later, click the Update button in the app, or re-run this installer."
Write-Host "To re-verify prerequisites only:  install.ps1 -CheckOnly"
Write-Host ""
