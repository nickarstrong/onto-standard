# ONTO Infrastructure Startup Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ONTO Infrastructure Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Убиваем старые процессы
Write-Host "`n[1/3] Cleaning up old processes..." -ForegroundColor Yellow
$ports = @(8081)
foreach ($port in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "  Killed process on port $port" -ForegroundColor Gray
    }
}
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# 2. Запускаем Signal Server
Write-Host "`n[2/3] Starting Signal Server..." -ForegroundColor Yellow
$signalJob = Start-Process -FilePath "python" -ArgumentList "server.py" -WorkingDirectory "C:\ONTO\onto-signal" -PassThru -WindowStyle Minimized
Write-Host "  Signal Server PID: $($signalJob.Id)" -ForegroundColor Green
Start-Sleep -Seconds 3

# 3. Запускаем Cloudflare Tunnel
Write-Host "`n[3/3] Starting Cloudflare Tunnel..." -ForegroundColor Yellow
$tunnelJob = Start-Process -FilePath "C:\Program Files (x86)\cloudflared\cloudflared.exe" -ArgumentList "tunnel run onto-signal" -PassThru -WindowStyle Minimized
Write-Host "  Cloudflare Tunnel PID: $($tunnelJob.Id)" -ForegroundColor Green
Start-Sleep -Seconds 5

# 4. Проверка
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Checking services..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    $local = Invoke-RestMethod -Uri "http://localhost:8081/signal/status" -TimeoutSec 5
    Write-Host "Local Signal:  ONLINE (sigma: $($local.sigma_id))" -ForegroundColor Green
} catch {
    Write-Host "Local Signal:  OFFLINE" -ForegroundColor Red
}

Start-Sleep -Seconds 3

try {
    $public = Invoke-RestMethod -Uri "https://signal.ontostandard.org/signal/status" -TimeoutSec 10
    Write-Host "Public Signal: ONLINE (sigma: $($public.sigma_id))" -ForegroundColor Green
} catch {
    Write-Host "Public Signal: OFFLINE (tunnel may need more time)" -ForegroundColor Yellow
}

try {
    $notary = Invoke-RestMethod -Uri "https://notary.ontostandard.org/health" -TimeoutSec 5
    Write-Host "Notary:        ONLINE (db: $($notary.database))" -ForegroundColor Green
} catch {
    Write-Host "Notary:        OFFLINE" -ForegroundColor Red
}

try {
    $api = Invoke-RestMethod -Uri "https://api.ontostandard.org/" -TimeoutSec 5
    Write-Host "Backend API:   ONLINE" -ForegroundColor Green
} catch {
    Write-Host "Backend API:   OFFLINE" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "ONTO Infrastructure Running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nTo stop: Stop-Process -Id $($signalJob.Id), $($tunnelJob.Id)"
