# Claw CrossFire AIR tray - kisayol kurulumu (Baslat menusu, masaustu, Windows ile baslatma).
# Kaldirmak icin:  powershell -ExecutionPolicy Bypass -File kurulum.ps1 -Kaldir
param([switch]$Kaldir)

$here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $here 'claw_tray.py'
$ico    = Join-Path $here 'claw.ico'
$targets = @(
    @{ Dir = [Environment]::GetFolderPath('Programs'); Name = 'Claw Fare.lnk' },
    @{ Dir = [Environment]::GetFolderPath('Desktop');  Name = 'Claw Fare.lnk' },
    @{ Dir = [Environment]::GetFolderPath('Startup');  Name = 'Claw Fare Pili.lnk' }
)

if ($Kaldir) {
    foreach ($t in $targets) {
        $p = Join-Path $t.Dir $t.Name
        if (Test-Path $p) { Remove-Item $p -Force; Write-Host "Silindi: $p" }
    }
    Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object {
        (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -like '*claw_tray.py*'
    } | Stop-Process -Force
    Write-Host 'Kisayollar kaldirildi. Klasoru silebilirsiniz.'
    exit 0
}

$pyw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $pyw) { Write-Host 'pythonw bulunamadi. Python 3.10+ kurulu ve PATH icinde olmali.' -ForegroundColor Red; exit 1 }
if (-not (Test-Path $script)) { Write-Host "claw_tray.py bulunamadi: $script" -ForegroundColor Red; exit 1 }

$ws = New-Object -ComObject WScript.Shell
foreach ($t in $targets) {
    $sc = $ws.CreateShortcut((Join-Path $t.Dir $t.Name))
    $sc.TargetPath = $pyw
    $sc.Arguments = '"' + $script + '"'
    $sc.WorkingDirectory = $here
    if (Test-Path $ico) { $sc.IconLocation = $ico }
    $sc.Description = 'Claw CrossFire AIR fare denetimi (tepsi)'
    $sc.Save()
    Write-Host ('Kisayol: ' + (Join-Path $t.Dir $t.Name))
}
Start-Process -FilePath $pyw -ArgumentList ('"' + $script + '"') -WorkingDirectory $here
Write-Host 'Kuruldu ve baslatildi. Simge sistem tepsisinde (^ altinda olabilir).' -ForegroundColor Green
