# Claw CrossFire AIR tray: shortcut installer (Start menu, desktop, Windows startup).
# Uses ClawTray.exe when it sits next to this script, otherwise pythonw + claw_tray.py.
# Remove:  powershell -ExecutionPolicy Bypass -File kurulum.ps1 -Kaldir
param([switch]$Kaldir)

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$exe  = Join-Path $here 'ClawTray.exe'
$py   = Join-Path $here 'claw_tray.py'
$ico  = Join-Path $here 'claw.ico'
$targets = @(
    @{ Dir = [Environment]::GetFolderPath('Programs'); Name = 'Claw Fare.lnk' },
    @{ Dir = [Environment]::GetFolderPath('Desktop');  Name = 'Claw Fare.lnk' },
    @{ Dir = [Environment]::GetFolderPath('Startup');  Name = 'Claw Fare Pili.lnk' }
)

if ($Kaldir) {
    foreach ($t in $targets) {
        $p = Join-Path $t.Dir $t.Name
        if (Test-Path $p) { Remove-Item $p -Force; Write-Host "Silindi / removed: $p" }
    }
    Get-Process ClawTray -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object {
        (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -like '*claw_tray.py*'
    } | Stop-Process -Force
    Write-Host 'Kisayollar kaldirildi, klasoru silebilirsiniz. / Shortcuts removed, you can delete the folder.'
    exit 0
}

if (Test-Path $exe) {
    $target = $exe; $args = ''
} else {
    $pyw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
    if (-not $pyw) { Write-Host 'ClawTray.exe yok ve pythonw bulunamadi. / No ClawTray.exe and no pythonw on PATH.' -ForegroundColor Red; exit 1 }
    if (-not (Test-Path $py)) { Write-Host "claw_tray.py bulunamadi / not found: $py" -ForegroundColor Red; exit 1 }
    $target = $pyw; $args = '"' + $py + '"'
}

$ws = New-Object -ComObject WScript.Shell
foreach ($t in $targets) {
    $sc = $ws.CreateShortcut((Join-Path $t.Dir $t.Name))
    $sc.TargetPath = $target
    $sc.Arguments = $args
    $sc.WorkingDirectory = $here
    if (Test-Path $ico) { $sc.IconLocation = $ico }
    $sc.Description = 'Claw CrossFire AIR tray'
    $sc.Save()
    Write-Host ('Kisayol / shortcut: ' + (Join-Path $t.Dir $t.Name))
}
if ($args) { Start-Process -FilePath $target -ArgumentList $args -WorkingDirectory $here } else { Start-Process -FilePath $target -WorkingDirectory $here }
Write-Host 'Kuruldu ve baslatildi. / Installed and started. Simge tepside (^ altinda olabilir).' -ForegroundColor Green
