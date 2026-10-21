$ErrorActionPreference = 'Stop'
$manifestPath = Join-Path $PSScriptRoot '..\artifacts\runtime\processes.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if (-not $manifest.processes) { throw 'Teslim süreç manifesti bulunamadı; PID otomatik seçilmeyecek.' }
foreach ($entry in $manifest.processes) {
    $running = Get-Process -Id $entry.id -ErrorAction SilentlyContinue
    if (-not $running) { Write-Output "$($entry.role): zaten kapalı"; continue }
    if ($running.StartTime.ToUniversalTime().ToString('o') -ne $entry.start_time_utc) {
        Write-Warning "$($entry.role): PID başka bir sürece ait; durdurulmadı."
        continue
    }
    Stop-Process -Id $running.Id
    Write-Output "$($entry.role): durduruldu (PID $($entry.id))"
}
