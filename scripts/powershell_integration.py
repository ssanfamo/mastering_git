# scripts\powershell_integration_fixed.py
import subprocess
import json
import platform
import os

class PowerShellManager:
    def __init__(self):
        # Correct path to PowerShell executable on Windows
        self.powershell_path = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        print(f"🔧 PowerShell path: {self.powershell_path}")
        
        # Verify PowerShell is available
        if not os.path.exists(self.powershell_path):
            print("❌ PowerShell not found at expected location")
            print("   Trying alternative path...")
            self.powershell_path = "powershell.exe"  # Try PATH
    
    def execute_ps(self, command, capture_output=True):
        """Execute PowerShell command and print results"""
        print(f"\n🚀 Executing PowerShell command:")
        print(f"   Command: {command[:100]}..." if len(command) > 100 else f"   Command: {command}")
        
        try:
            # Don't use shell=True for PowerShell commands
            result = subprocess.run(
                [self.powershell_path, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                capture_output=capture_output,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='ignore'
            )
            
            print(f"   Return Code: {result.returncode}")
            
            if capture_output:
                if result.stdout and result.stdout.strip():
                    print(f"   Output:\n{'-'*40}")
                    print(result.stdout.strip())
                if result.stderr and result.stderr.strip():
                    print(f"   Errors:\n{'-'*40}")
                    print(result.stderr.strip())
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout.strip() if capture_output and result.stdout else "",
                "stderr": result.stderr.strip() if capture_output and result.stderr else "",
                "command": command
            }
        except subprocess.TimeoutExpired:
            error_msg = "❌ Command timed out after 30 seconds"
            print(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"❌ Command failed: {str(e)}"
            print(error_msg)
            return {"success": False, "error": str(e)}
    
    def test_basic_commands(self):
        """Test basic PowerShell commands"""
        print("\n" + "="*60)
        print("TESTING BASIC POWERSHELL COMMANDS")
        print("="*60)
        
        test_cases = [
            ("Get current date", "Get-Date"),
            ("Get computer name", "$env:COMPUTERNAME"),
            ("Get PowerShell version", "$PSVersionTable.PSVersion"),
            ("Simple calculation", "2 + 2"),
            ("Get Windows version", "[System.Environment]::OSVersion.Version")
        ]
        
        for description, command in test_cases:
            print(f"\n📝 {description}:")
            result = self.execute_ps(command)
            if result["success"] and result["stdout"]:
                print(f"   Result: {result['stdout']}")
    
    def get_system_info(self):
        """Get system information using WMI"""
        print("\n" + "="*60)
        print("GETTING SYSTEM INFORMATION")
        print("="*60)
        
        # Using WMI which is more reliable than Get-ComputerInfo
        command = """
$computer = Get-WmiObject Win32_ComputerSystem
$os = Get-WmiObject Win32_OperatingSystem
$cpu = Get-WmiObject Win32_Processor | Select-Object -First 1

$info = @{
    ComputerName = $computer.Name
    Manufacturer = $computer.Manufacturer
    Model = $computer.Model
    TotalMemoryGB = [math]::Round($computer.TotalPhysicalMemory / 1GB, 2)
    OSName = $os.Caption
    OSVersion = $os.Version
    Architecture = $os.OSArchitecture
    CPUName = $cpu.Name
    CPUCount = $cpu.NumberOfCores
}

$info | ConvertTo-Json
"""
        
        result = self.execute_ps(command)
        
        if result["success"] and result["stdout"]:
            try:
                info = json.loads(result["stdout"])
                print("\n💻 SYSTEM INFORMATION:")
                for key, value in info.items():
                    print(f"   {key}: {value}")
                return info
            except json.JSONDecodeError:
                print("   Could not parse JSON. Raw output:")
                print(result["stdout"])
        return None
    
    def get_disk_info(self):
        """Get disk information"""
        print("\n" + "="*60)
        print("GETTING DISK INFORMATION")
        print("="*60)
        
        command = """
Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    $usedGB = [math]::Round(($_.Size - $_.FreeSpace) / 1GB, 2)
    $totalGB = [math]::Round($_.Size / 1GB, 2)
    $freeGB = [math]::Round($_.FreeSpace / 1GB, 2)
    $percentUsed = [math]::Round(($usedGB / $totalGB) * 100, 1)
    
    [PSCustomObject]@{
        Drive = $_.DeviceID
        UsedGB = $usedGB
        FreeGB = $freeGB
        TotalGB = $totalGB
        PercentUsed = $percentUsed
    }
} | ConvertTo-Json
"""
        
        result = self.execute_ps(command)
        
        if result["success"] and result["stdout"]:
            try:
                disks = json.loads(result["stdout"])
                print("\n💾 DISK INFORMATION:")
                if isinstance(disks, list):
                    for disk in disks:
                        print(f"   Drive {disk['Drive']}: {disk['UsedGB']}GB used of {disk['TotalGB']}GB ({disk['PercentUsed']}%)")
                elif disks:
                    print(f"   Drive {disks['Drive']}: {disks['UsedGB']}GB used of {disks['TotalGB']}GB ({disks['PercentUsed']}%)")
                return disks
            except:
                print("   Raw output:", result["stdout"])
        return None
    
    def get_process_info(self, count=3):
        """Get top processes by CPU usage"""
        print("\n" + "="*60)
        print("GETTING PROCESS INFORMATION")
        print("="*60)
        
        command = f"""
Get-Process | Sort-Object CPU -Descending | Select-Object -First {count} | ForEach-Object {{
    [PSCustomObject]@{{
        Name = $_.ProcessName
        CPU = [math]::Round($_.CPU, 2)
        MemoryMB = [math]::Round($_.WorkingSet / 1MB, 2)
        Id = $_.Id
    }}
}} | ConvertTo-Json
"""
        
        result = self.execute_ps(command)
        
        if result["success"] and result["stdout"]:
            try:
                processes = json.loads(result["stdout"])
                print(f"\n🔥 TOP {count} PROCESSES BY CPU:")
                if isinstance(processes, list):
                    for proc in processes:
                        print(f"   {proc['Name']} (PID: {proc['Id']}): CPU={proc['CPU']}%, Memory={proc['MemoryMB']}MB")
                elif processes:
                    print(f"   {processes['Name']} (PID: {processes['Id']}): CPU={processes['CPU']}%, Memory={processes['MemoryMB']}MB")
                return processes
            except:
                print("   Raw output:", result["stdout"])
        return None
    
    def get_network_info(self):
        """Get network information"""
        print("\n" + "="*60)
        print("GETTING NETWORK INFORMATION")
        print("="*60)
        
        command = """
$adapters = Get-NetAdapter | Where-Object {$_.Status -eq 'Up'}
$results = @()

foreach ($adapter in $adapters) {
    $config = Get-NetIPConfiguration -InterfaceIndex $adapter.InterfaceIndex
    $results += [PSCustomObject]@{
        Interface = $adapter.Name
        Status = $adapter.Status
        MAC = $adapter.MacAddress
        IPv4 = if ($config.IPv4Address) { $config.IPv4Address.IPAddress } else { "N/A" }
        Gateway = if ($config.IPv4DefaultGateway) { $config.IPv4DefaultGateway.NextHop } else { "N/A" }
    }
}

$results | ConvertTo-Json
"""
        
        result = self.execute_ps(command)
        
        if result["success"] and result["stdout"]:
            try:
                networks = json.loads(result["stdout"])
                print("\n🌐 NETWORK INFORMATION:")
                if isinstance(networks, list):
                    for net in networks:
                        print(f"   Interface: {net['Interface']}")
                        print(f"     Status: {net['Status']}")
                        print(f"     MAC: {net['MAC']}")
                        print(f"     IPv4: {net['IPv4']}")
                        if net['Gateway'] != "N/A":
                            print(f"     Gateway: {net['Gateway']}")
                        print()
                elif networks:
                    print(f"   Interface: {networks['Interface']}")
                    print(f"     IPv4: {networks['IPv4']}")
                return networks
            except:
                print("   Raw output:", result["stdout"])
        return None

def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("POWERSHELL INTEGRATION DEMO")
    print("="*60)
    print(f"Running on: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print("="*60)
    
    # Create PowerShell manager
    ps = PowerShellManager()
    
    # Test basic commands first
    ps.test_basic_commands()
    
    # Get system info
    ps.get_system_info()
    
    # Get disk info
    ps.get_disk_info()
    
    # Get process info
    ps.get_process_info(3)
    
    # Get network info
    ps.get_network_info()
    
    print("\n" + "="*60)
    print("DEMO COMPLETED!")
    print("="*60)

if __name__ == "__main__":
    main()