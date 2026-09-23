# Builds ClawTray.exe (single file, no console) and a release zip.
#   powershell -ExecutionPolicy Bypass -File build.ps1            -> build_out\dist\ClawTray.exe
#   powershell -ExecutionPolicy Bypass -File build.ps1 -Version 1.0.0  -> also build_out\ClawTray-1.0.0-win64.zip
param([string]$Version = "")

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here
python -m pip install --quiet pyinstaller -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host 'pip failed' -ForegroundColor Red; exit 1 }

if (Test-Path build_out) { Remove-Item build_out -Recurse -Force }
python -m PyInstaller --noconfirm --onefile --noconsole --name ClawTray `
    --icon (Join-Path $here 'claw.ico') `
    --hidden-import pystray._win32 --hidden-import PIL.ImageDraw --hidden-import PIL.ImageFont `
    --distpath build_out\dist --workpath build_out\work --specpath build_out claw_tray.py
if ($LASTEXITCODE -ne 0 -or -not (Test-Path build_out\dist\ClawTray.exe)) { Write-Host 'PyInstaller failed' -ForegroundColor Red; exit 1 }
Write-Host ('Built: ' + (Get-Item build_out\dist\ClawTray.exe).Length + ' bytes') -ForegroundColor Green

if ($Version) {
    $pkg = Join-Path build_out "ClawTray-$Version-win64"
    New-Item -ItemType Directory -Force $pkg | Out-Null
    Copy-Item build_out\dist\ClawTray.exe, kurulum.ps1, claw.ico, README.md, README.tr.md, LICENSE $pkg
    $zip = "$pkg.zip"
    if (Test-Path $zip) { Remove-Item $zip }
    Compress-Archive -Path "$pkg\*" -DestinationPath $zip
    Write-Host "Package: $zip" -ForegroundColor Green
}
