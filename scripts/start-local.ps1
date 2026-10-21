$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$runtime=Join-Path $projectRoot 'artifacts/runtime'
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
$entries=@()
foreach($port in @(8000,5173)) {
    $listener=Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if($listener) {Write-Output "Port $port already listening; no second server started.";continue}
    if($port -eq 8000) {
        $process=Start-Process -FilePath (Join-Path $projectRoot '.venv/Scripts/python.exe') -ArgumentList 'backend/run.py' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtime 'backend-ui.out.log') -RedirectStandardError (Join-Path $runtime 'backend-ui.err.log')
        $role='backend-launcher'
    } else {
        $node=(Get-Command node.exe).Source
        $process=Start-Process -FilePath $node -ArgumentList 'node_modules/vite/bin/vite.js' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtime 'frontend-ui.out.log') -RedirectStandardError (Join-Path $runtime 'frontend-ui.err.log')
        $role='frontend'
    }
    $entries+=@{id=$process.Id;start_time_utc=$process.StartTime.ToUniversalTime().ToString('o');role=$role}
    $listener=$null
    for($i=0;$i -lt 60;$i++) {Start-Sleep -Milliseconds 300;$listener=Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue;if($listener){break}}
    if(-not $listener){throw "Server did not bind port $port. Inspect artifacts/runtime logs."}
    if($listener.OwningProcess -ne $process.Id){$child=Get-Process -Id $listener.OwningProcess;$entries+=@{id=$child.Id;start_time_utc=$child.StartTime.ToUniversalTime().ToString('o');role='backend-listener'}}
    Write-Output "Started local server on port $port."
}
$stateFile=Join-Path $runtime 'processes.json'
if(Test-Path -LiteralPath $stateFile){$previous=Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json;foreach($entry in $previous.processes){$running=Get-Process -Id $entry.id -ErrorAction SilentlyContinue;if($running -and $running.StartTime.ToUniversalTime().ToString('o') -eq $entry.start_time_utc){$entries+=$entry}}}
@{processes=@($entries | ForEach-Object {[pscustomobject]$_} | Sort-Object -Property id -Unique)} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $stateFile -Encoding UTF8
