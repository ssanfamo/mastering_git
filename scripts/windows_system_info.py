# scripts\windows_system_info.py
import platform
import psutil
import socket
from datetime import datetime
import wmi  # Windows Management Instrumentation

def get_windows_system_info():
    """Get detailed Windows system information"""
    info = {
        "system": {
            "os": platform.system(),
            "version": platform.version(),
            "release": platform.release(),
            "architecture": platform.architecture()[0],
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn()
        },
        "hardware": {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "disk_partitions": []
        },
        "network": {
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "interfaces": []
        }
    }
    
    # Disk information
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            info["hardware"]["disk_partitions"].append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent_used": usage.percent
            })
        except:
            continue
    
    # Network interfaces
    for iface, addrs in psutil.net_if_addrs().items():
        interface_info = {"name": iface, "addresses": []}
        for addr in addrs:
            interface_info["addresses"].append({
                "family": str(addr.family),
                "address": addr.address,
                "netmask": addr.netmask
            })
        info["network"]["interfaces"].append(interface_info)
    
    return info

# Windows-specific monitoring
def check_windows_services(service_names=None):
    """Check status of Windows services"""
    import win32serviceutil
    
    services_status = {}
    if not service_names:
        service_names = ["WinRM", "Spooler", "Dhcp", "Dnscache"]
    
    for service in service_names:
        try:
            status = win32serviceutil.QueryServiceStatus(service)[1]
            status_map = {
                1: "Stopped",
                2: "Start Pending",
                3: "Stop Pending",
                4: "Running",
                5: "Continue Pending",
                6: "Pause Pending",
                7: "Paused"
            }
            services_status[service] = status_map.get(status, "Unknown")
        except:
            services_status[service] = "Not Found"
    
    return services_status

if __name__ == "__main__":
    print("Windows System Information:")
    print("=" * 50)
    info = get_windows_system_info()
    print(f"OS: {info['system']['os']} {info['system']['release']}")
    print(f"Hostname: {info['system']['hostname']}")
    print(f"CPU Cores: {info['hardware']['cpu_count']}")
    print(f"Memory: {info['hardware']['memory_available_gb']}GB available of {info['hardware']['memory_total_gb']}GB")
    
    services = check_windows_services()
    print("\nWindows Services Status:")
    for service, status in services.items():
        print(f"  {service}: {status}")
