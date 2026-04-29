# Creates a Desktop shortcut "Job Tracker" that launches the tracker silently with the custom icon.
# Run once:  powershell -ExecutionPolicy Bypass -File create_shortcut.ps1

$here       = Split-Path -Parent $MyInvocation.MyCommand.Path
$target     = Join-Path $here 'launch.vbs'
$icon       = Join-Path $here 'tracker.ico'
$desktop    = [Environment]::GetFolderPath('Desktop')
$lnk        = Join-Path $desktop 'Job Tracker.lnk'

if (-not (Test-Path $target)) { Write-Error "Missing $target"; exit 1 }
if (-not (Test-Path $icon))   { Write-Error "Missing $icon (run: python make_icon.py)"; exit 1 }

$shell    = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($lnk)
$shortcut.TargetPath       = 'wscript.exe'
$shortcut.Arguments        = '"' + $target + '"'
$shortcut.WorkingDirectory = $here
$shortcut.IconLocation     = $icon
$shortcut.Description      = 'Job Application Tracker'
$shortcut.Save()

Write-Host "Created shortcut: $lnk" -ForegroundColor Green
Write-Host "Double-click it on your desktop to launch the tracker."
