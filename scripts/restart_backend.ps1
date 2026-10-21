$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$runtimePath=Join-Path $projectRoot 'artifacts/runtime/processes.json'
$state=Get-Content -LiteralPath $runtimePath -Raw | ConvertFrom-Json
foreach($entry in $state.processes | Where-Object {$_.role -like 'backend-*'}) {
    $running=Get-Process -Id $entry.id -ErrorAction SilentlyContinue
    if($running -and $running.StartTime.ToUniversalTime().ToString('o') -eq $entry.start_time_utc) {Stop-Process -Id $entry.id -Force}
}
$listeners=Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
for($i=0;$listeners -and $i -lt 20;$i++){Start-Sleep -Milliseconds 250;$listeners=Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue}
if($listeners){throw '8000 portunda kimliği doğrulanmamış süreç var; ikinci backend başlatılmadı.'}
$launcher=Start-Process -FilePath (Join-Path $projectRoot '.venv/Scripts/python.exe') -ArgumentList 'backend/run.py' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot 'artifacts/runtime/backend-improvements.out.log') -RedirectStandardError (Join-Path $projectRoot 'artifacts/runtime/backend-improvements.err.log')
$listener=$null
for($i=0;$i -lt 40;$i++){Start-Sleep -Milliseconds 250;$listener=Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue;if($listener){break}}
if(-not $listener){throw 'Backend başlamadı; hata günlüğünü kontrol edin.'}
$kept=@($state.processes | Where-Object {$_.role -notlike 'backend-*'})
$new=@(@{id=$launcher.Id;start_time_utc=$launcher.StartTime.ToUniversalTime().ToString('o');role='backend-launcher'})
if($listener.OwningProcess -ne $launcher.Id){$p=Get-Process -Id $listener.OwningProcess;$new+=@{id=$p.Id;start_time_utc=$p.StartTime.ToUniversalTime().ToString('o');role='backend-listener'}}
$state | Add-Member -NotePropertyName backend_pid -NotePropertyValue $launcher.Id -Force
$state.processes=@($kept)+@($new)
$state | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $runtimePath -Encoding UTF8
Write-Output 'Backend aynı 8000 portunda yeniden başlatıldı; frontend korundu.'
