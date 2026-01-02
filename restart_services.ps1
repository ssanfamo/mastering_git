# Auto-generated service restart script
# Generated: 2026-01-02T08:27:55.350141

$ErrorActionPreference = "Stop"

function Restart-ServiceSafely {
    param([string]$ServiceName)
    
    Write-Host "Processing service: $ServiceName" -ForegroundColor Cyan
    
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction Stop
        
        if ($service.Status -eq 'Running') {
            Write-Host "  Stopping service..." -ForegroundColor Yellow
            Stop-Service -Name $ServiceName -Force
            Start-Sleep -Seconds 2
            
            # Wait for service to stop
            $timeout = 30
            $elapsed = 0
            while ((Get-Service -Name $ServiceName).Status -eq 'Running' -and $elapsed -lt $timeout) {
                Start-Sleep -Seconds 1
                $elapsed++
            }
        }
        
        Write-Host "  Starting service..." -ForegroundColor Green
        Start-Service -Name $ServiceName
        
        # Wait for service to start
        Start-Sleep -Seconds 5
        
        $finalStatus = (Get-Service -Name $ServiceName).Status
        if ($finalStatus -eq 'Running') {
            Write-Host "  ✅ Service restarted successfully" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Service is $finalStatus after restart" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "  ❌ Error: $_" -ForegroundColor Red
    }
}

# Restart services
Restart-ServiceSafely -ServiceName "AdobeARMservice"
Restart-ServiceSafely -ServiceName "ApHidMonitorService"
Restart-ServiceSafely -ServiceName "Appinfo"

Write-Host 'Service restart completed!' -ForegroundColor Green