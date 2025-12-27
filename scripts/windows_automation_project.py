# scripts\windows_automation_project.py
"""
Windows System Health Monitor
Combines all Windows automation techniques learned today
"""
import json
from datetime import datetime
from pathlib import Path
import sys

class WindowsSystemHealthMonitor:
    """Comprehensive Windows system health monitoring"""
    
    def __init__(self):
        self.report_dir = Path("C:/Career_Transition/reports/system_health")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Import our modules
        sys.path.append(str(Path.cwd()))
        
        # We'll use the classes we created earlier
        self.services = None
        self.events = None
        self.registry = None
        self.ps = None
        
        # Try to import them
        try:
            from windows_services import WindowsServiceManager
            from windows_event_logs import WindowsEventLogManager
            from windows_registry import WindowsRegistryManager
            from powershell_integration import PowerShellManager
            
            self.services = WindowsServiceManager()
            self.events = WindowsEventLogManager()
            self.registry = WindowsRegistryManager()
            self.ps = PowerShellManager()
            
        except ImportError as e:
            print(f"⚠️  Some modules not available: {e}")
            print("   Running with limited functionality")
    
    def collect_all_metrics(self):
        """Collect all system metrics"""
        print("="*70)
        print("WINDOWS SYSTEM HEALTH MONITOR")
        print("="*70)
        print(f"Scan started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {},
            "services": {},
            "event_logs": {},
            "disk_space": {},
            "performance": {},
            "security": {}
        }
        
        # 1. Get system information via PowerShell
        print("📊 Collecting System Information...")
        if self.ps:
            try:
                # Get basic info
                system_info = self.ps.get_system_info()
                if system_info:
                    metrics["system_info"] = system_info
            except:
                pass
        
        # 2. Get service status
        print("🔧 Checking Critical Services...")
        critical_services = ["WinRM", "Spooler", "Dhcp", "Dnscache", "EventLog", "Schedule"]
        service_status = {}
        
        for service in critical_services:
            if self.services:
                status = self.services.get_service_status(service)
                service_status[service] = status
            else:
                # Fallback to PowerShell
                if self.ps:
                    result = self.ps.execute_ps(f"Get-Service -Name {service} | Select-Object Status")
                    if result["success"]:
                        service_status[service] = result["stdout"].strip()
        
        metrics["services"] = service_status
        
        # 3. Check disk space
        print("💾 Checking Disk Space...")
        if self.ps:
            disk_result = self.ps.get_disk_info_simple()
            if disk_result:
                metrics["disk_space"] = disk_result
        
        # 4. Check performance
        print("⚡ Checking System Performance...")
        if self.ps:
            processes = self.ps.get_running_processes(5)
            if processes:
                metrics["performance"]["top_processes"] = processes
            
            # Get memory info
            memory_cmd = """
$os = Get-WmiObject Win32_OperatingSystem
$used = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1MB, 2)
$total = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
$percent = [math]::Round(($used / $total) * 100, 1)

@{
    UsedGB = $used
    TotalGB = $total
    PercentUsed = $percent
} | ConvertTo-Json
"""
            memory_result = self.ps.execute_ps(memory_cmd)
            if memory_result["success"] and memory_result["stdout"]:
                try:
                    memory_info = json.loads(memory_result["stdout"])
                    metrics["performance"]["memory"] = memory_info
                except:
                    pass
        
        # 5. Check security (event logs for errors)
        print("🛡️  Checking Security Events...")
        if self.events:
            security_events = self.events.read_event_log("Security", last_hours=24)
            if security_events:
                metrics["security"]["event_count"] = len(security_events)
                metrics["security"]["sample_events"] = security_events[:3]
        
        # 6. Check network connectivity
        print("🌐 Testing Network Connectivity...")
        if self.ps:
            # Test internet
            internet_test = self.ps.execute_ps('Test-NetConnection -ComputerName "8.8.8.8" -InformationLevel Quiet')
            metrics["network"] = {
                "internet_available": internet_test["returncode"] == 0,
                "test_time": datetime.now().isoformat()
            }
        
        return metrics
    
    def generate_health_report(self, metrics):
        """Generate health report from collected metrics"""
        print("\n" + "="*70)
        print("GENERATING HEALTH REPORT")
        print("="*70)
        
        # Calculate health score (0-100)
        health_score = 100
        issues = []
        
        # Check services
        failed_services = []
        for service, status in metrics.get("services", {}).items():
            if status != "Running" and "Running" not in str(status):
                failed_services.append(service)
                health_score -= 5
        
        if failed_services:
            issues.append(f"Services not running: {', '.join(failed_services)}")
        
        # Check disk space
        disk_info = metrics.get("disk_space")
        if disk_info:
            if isinstance(disk_info, list):
                for disk in disk_info:
                    if disk.get("PercentUsed", 0) > 90:
                        issues.append(f"Drive {disk.get('Drive')} is {disk.get('PercentUsed')}% full")
                        health_score -= 10
            elif disk_info.get("PercentUsed", 0) > 90:
                issues.append(f"Disk is {disk_info.get('PercentUsed')}% full")
                health_score -= 10
        
        # Check memory
        memory_info = metrics.get("performance", {}).get("memory")
        if memory_info and memory_info.get("PercentUsed", 0) > 90:
            issues.append(f"Memory usage is {memory_info.get('PercentUsed')}%")
            health_score -= 10
        
        # Prepare report
        report = {
            "report_generated": datetime.now().isoformat(),
            "health_score": max(0, health_score),  # Don't go below 0
            "health_status": self._get_health_status(health_score),
            "issues_found": issues,
            "issues_count": len(issues),
            "metrics_summary": {
                "services_checked": len(metrics.get("services", {})),
                "disks_checked": len(disk_info) if isinstance(disk_info, list) else (1 if disk_info else 0),
                "performance_metrics": len(metrics.get("performance", {})),
                "security_events": metrics.get("security", {}).get("event_count", 0)
            },
            "detailed_metrics": metrics
        }
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.report_dir / f"system_health_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"\n📋 HEALTH REPORT SUMMARY:")
        print(f"   Health Score: {report['health_score']}/100 - {report['health_status']}")
        print(f"   Issues Found: {report['issues_count']}")
        
        if issues:
            print(f"\n🔴 ISSUES IDENTIFIED:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print(f"\n✅ No critical issues found!")
        
        print(f"\n📊 METRICS COLLECTED:")
        for category, count in report["metrics_summary"].items():
            friendly_name = category.replace("_", " ").title()
            print(f"   {friendly_name}: {count}")
        
        print(f"\n📄 Full report saved to: {report_file}")
        
        return report
    
    def _get_health_status(self, score):
        """Convert score to status"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Critical"
    
    def create_daily_monitor_script(self):
        """Create a daily monitoring PowerShell script"""
        script_content = """# Daily System Health Monitor
# Auto-generated by Python
# Run this script daily to monitor system health

$ErrorActionPreference = "Continue"
$ReportDate = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportPath = "C:\\Career_Transition\\reports\\system_health\\daily_$ReportDate.txt"

function Write-Report {
    param([string]$Message)
    Add-Content -Path $ReportPath -Value $Message
    Write-Host $Message
}

Write-Report "=========================================="
Write-Report "DAILY SYSTEM HEALTH CHECK"
Write-Report "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Report "=========================================="

# 1. System Information
Write-Report "`n1. SYSTEM INFORMATION:"
$computerInfo = Get-ComputerInfo
Write-Report "   Computer: $($computerInfo.CsName)"
Write-Report "   Windows: $($computerInfo.WindowsProductName)"
Write-Report "   Version: $($computerInfo.WindowsVersion)"

# 2. Disk Space
Write-Report "`n2. DISK SPACE:"
Get-PSDrive -PSProvider FileSystem | Where-Object {$_.Used -gt 0} | ForEach-Object {
    $usedGB = [math]::Round($_.Used / 1GB, 2)
    $freeGB = [math]::Round($_.Free / 1GB, 2)
    $totalGB = [math]::Round(($_.Used + $_.Free) / 1GB, 2)
    $percentUsed = [math]::Round(($usedGB / $totalGB) * 100, 1)
    
    $status = if ($percentUsed -gt 90) { "CRITICAL" } elseif ($percentUsed -gt 80) { "WARNING" } else { "OK" }
    Write-Report "   Drive $($_.Name): $usedGB/$totalGB GB ($percentUsed%) - $status"
}

# 3. Services
Write-Report "`n3. CRITICAL SERVICES:"
$criticalServices = @("WinRM", "Spooler", "Dhcp", "Dnscache", "EventLog", "Schedule")
foreach ($service in $criticalServices) {
    $svc = Get-Service -Name $service -ErrorAction SilentlyContinue
    if ($svc) {
        $status = if ($svc.Status -eq 'Running') { "RUNNING" } else { "STOPPED" }
        Write-Report "   $service: $status"
    } else {
        Write-Report "   $service: NOT FOUND"
    }
}

# 4. Memory Usage
Write-Report "`n4. MEMORY USAGE:"
$os = Get-WmiObject Win32_OperatingSystem
$usedGB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1GB, 2)
$totalGB = [math]::Round($os.TotalVisibleMemorySize / 1GB, 2)
$percent = [math]::Round(($usedGB / $totalGB) * 100, 1)
$memStatus = if ($percent -gt 90) { "CRITICAL" } elseif ($percent -gt 80) { "WARNING" } else { "OK" }
Write-Report "   Memory: $usedGB/$totalGB GB ($percent%) - $memStatus"

# 5. Recent Errors
Write-Report "`n5. RECENT ERRORS (Last 24h):"
$errorCount = (Get-EventLog -LogName Application -EntryType Error -After (Get-Date).AddHours(-24)).Count
Write-Report "   Application Errors: $errorCount"

$systemErrors = (Get-EventLog -LogName System -EntryType Error -After (Get-Date).AddHours(-24)).Count
Write-Report "   System Errors: $systemErrors"

# 6. Internet Connectivity
Write-Report "`n6. INTERNET CONNECTIVITY:"
try {
    $test = Test-NetConnection -ComputerName "8.8.8.8" -InformationLevel Quiet -ErrorAction Stop
    if ($test) {
        Write-Report "   Status: CONNECTED"
    } else {
        Write-Report "   Status: DISCONNECTED"
    }
} catch {
    Write-Report "   Status: TEST FAILED"
}

Write-Report "`n=========================================="
Write-Report "CHECK COMPLETED"
Write-Report "Report saved to: $ReportPath"
Write-Report "=========================================="

Write-Host "`nReport generated: $ReportPath" -ForegroundColor Green
"""
        
        script_file = Path("C:/Career_Transition/scripts/daily_health_check.ps1")
        script_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"\n📝 Daily monitoring script created: {script_file}")
        print(f"   To run manually: powershell.exe -ExecutionPolicy Bypass -File {script_file}")
        
        # Create batch file for easy execution
        batch_content = f"""@echo off
echo Running Daily System Health Check...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{script_file}"
pause
"""
        
        batch_file = Path("C:/Career_Transition/scripts/run_health_check.bat")
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        
        print(f"   Batch file: {batch_file}")
        
        return script_file

def main():
    """Main execution"""
    print("Starting Windows System Health Monitor...")
    
    monitor = WindowsSystemHealthMonitor()
    
    # Collect metrics
    metrics = monitor.collect_all_metrics()
    
    # Generate report
    report = monitor.generate_health_report(metrics)
    
    # Create daily monitoring script
    monitor.create_daily_monitor_script()
    
    print("\n" + "="*70)
    print("WINDOWS AUTOMATION DAY 2 - COMPLETED!")
    print("="*70)
    print("\n✅ What you've accomplished today:")
    print("   1. PowerShell integration from Python")
    print("   2. Windows service management")
    print("   3. Event log monitoring and analysis")
    print("   4. Safe registry operations (read-only)")
    print("   5. Comprehensive system health monitoring")
    print("   6. Automated report generation")
    print("\n📁 All reports saved to: C:\\Career_Transition\\reports\\")
    print("📝 Scripts saved to: C:\\Career_Transition\\scripts\\")

if __name__ == "__main__":
    main()