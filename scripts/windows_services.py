# scripts\windows_services.py
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import time
from datetime import datetime, timedelta
import json

class WindowsServiceManager:
    """Manage Windows services programmatically"""
    
    @staticmethod
    def get_service_status(service_name):
        """Get current status of a Windows service"""
        try:
            status = win32serviceutil.QueryServiceStatus(service_name)
            status_codes = {
                1: "Stopped",
                2: "Start Pending", 
                3: "Stop Pending",
                4: "Running",
                5: "Continue Pending",
                6: "Pause Pending",
                7: "Paused"
            }
            return status_codes.get(status[1], "Unknown")
        except Exception as e:
            return f"Error: {str(e)}"
    
    @staticmethod
    def list_services(status_filter=None):
        """List Windows services with optional filtering"""
        import wmi
        
        c = wmi.WMI()
        services = []
        
        for service in c.Win32_Service():
            if status_filter and service.State != status_filter:
                continue
                
            services.append({
                'name': service.Name,
                'display_name': service.DisplayName,
                'state': service.State,
                'start_mode': service.StartMode,
                'path': service.PathName,
                'start_name': service.StartName,
                'description': service.Description
            })
        
        return services
    
    @staticmethod
    def monitor_service(service_name, check_interval=60, max_checks=10):
        """Monitor a service and alert if it stops"""
        print(f"🔍 Monitoring service: {service_name}")
        
        for i in range(max_checks):
            status = WindowsServiceManager.get_service_status(service_name)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"  Check {i+1}/{max_checks} at {timestamp}: {status}")
            
            if status != "Running":
                print(f"  ⚠️  Alert: {service_name} is not running!")
                # Could add email/notification here
                return False
            
            if i < max_checks - 1:  # Don't sleep on last iteration
                time.sleep(check_interval)
        
        print(f"  ✅ Service remained running for {max_checks} checks")
        return True
    
    @staticmethod
    def create_service_restart_script(service_names, output_file="restart_services.ps1"):
        """Create PowerShell script to restart services"""
        script_content = """# Auto-generated service restart script
# Generated: {timestamp}

$ErrorActionPreference = "Stop"

function Restart-ServiceSafely {{
    param([string]$ServiceName)
    
    Write-Host "Processing service: $ServiceName" -ForegroundColor Cyan
    
    try {{
        $service = Get-Service -Name $ServiceName -ErrorAction Stop
        
        if ($service.Status -eq 'Running') {{
            Write-Host "  Stopping service..." -ForegroundColor Yellow
            Stop-Service -Name $ServiceName -Force
            Start-Sleep -Seconds 2
            
            # Wait for service to stop
            $timeout = 30
            $elapsed = 0
            while ((Get-Service -Name $ServiceName).Status -eq 'Running' -and $elapsed -lt $timeout) {{
                Start-Sleep -Seconds 1
                $elapsed++
            }}
        }}
        
        Write-Host "  Starting service..." -ForegroundColor Green
        Start-Service -Name $ServiceName
        
        # Wait for service to start
        Start-Sleep -Seconds 5
        
        $finalStatus = (Get-Service -Name $ServiceName).Status
        if ($finalStatus -eq 'Running') {{
            Write-Host "  ✅ Service restarted successfully" -ForegroundColor Green
        }} else {{
            Write-Host "  ⚠️  Service is $finalStatus after restart" -ForegroundColor Yellow
        }}
        
    }} catch {{
        Write-Host "  ❌ Error: $_" -ForegroundColor Red
    }}
}}

# Restart services
"""
        
        for service in service_names:
            script_content += f'Restart-ServiceSafely -ServiceName "{service}"\n'
        
        script_content += "\nWrite-Host 'Service restart completed!' -ForegroundColor Green"
        
        # Save script
        script_content = script_content.format(timestamp=datetime.now().isoformat())
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"📝 PowerShell script created: {output_file}")
        print(f"   To run: powershell.exe -ExecutionPolicy Bypass -File {output_file}")
        
        return output_file

# Example usage
service_mgr = WindowsServiceManager()

# List all running services
print("🏃 RUNNING SERVICES:")
running_services = service_mgr.list_services(status_filter="Running")
for i, service in enumerate(running_services[:5], 1):  # Show first 5
    print(f"  {i}. {service['display_name']} ({service['name']})")

# Check specific service status
services_to_check = ["WinRM", "Spooler", "Dhcp", "Dnscache"]
print("\n🔧 SPECIFIC SERVICE STATUS:")
for service in services_to_check:
    status = service_mgr.get_service_status(service)
    print(f"  {service}: {status}")

# Create restart script
if running_services:
    service_names = [s['name'] for s in running_services[:3]]  # First 3 running services
    script_file = service_mgr.create_service_restart_script(service_names)