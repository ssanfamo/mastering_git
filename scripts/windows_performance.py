# scripts\windows_performance.py
import psutil
import pandas as pd
from datetime import datetime

class WindowsPerformanceMonitor:
    def __init__(self):
        self.metrics = []
    
    def collect_metrics(self):
        """Collect comprehensive Windows performance metrics"""
        timestamp = datetime.now()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk metrics
        disk_io = psutil.disk_io_counters()
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        # Process metrics
        process_count = len(psutil.pids())
        
        metrics = {
            "timestamp": timestamp,
            "cpu": {
                "percent_total": psutil.cpu_percent(interval=None),
                "percent_per_core": cpu_percent,
                "cores": psutil.cpu_count(),
                "frequency_current": cpu_freq.current if cpu_freq else None,
                "frequency_max": cpu_freq.max if cpu_freq else None
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
                "swap_total_gb": round(swap.total / (1024**3), 2),
                "swap_used_gb": round(swap.used / (1024**3), 2)
            },
            "disk": {
                "read_mb": round(disk_io.read_bytes / (1024**2), 2),
                "write_mb": round(disk_io.write_bytes / (1024**2), 2),
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count
            },
            "network": {
                "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            },
            "system": {
                "process_count": process_count,
                "boot_time": datetime.fromtimestamp(psutil.boot_time())
            }
        }
        
        self.metrics.append(metrics)
        return metrics
    
    def collect_over_time(self, duration_seconds=60, interval_seconds=5):
        """Collect metrics over time period"""
        import time
        
        end_time = time.time() + duration_seconds
        
        print(f"Collecting metrics for {duration_seconds} seconds...")
        
        while time.time() < end_time:
            self.collect_metrics()
            time.sleep(interval_seconds)
        
        print(f"Collected {len(self.metrics)} samples")
        return self.metrics
    
    def save_to_excel(self, filename="windows_performance"):
        """Save metrics to Excel file (Windows-friendly)"""
        if not self.metrics:
            print("No metrics to save")
            return
        
        # Flatten metrics for Excel
        flat_data = []
        for metric in self.metrics:
            flat_entry = {
                "timestamp": metric["timestamp"],
                "cpu_percent": metric["cpu"]["percent_total"],
                "memory_percent": metric["memory"]["percent"],
                "memory_available_gb": metric["memory"]["available_gb"],
                "disk_read_mb": metric["disk"]["read_mb"],
                "disk_write_mb": metric["disk"]["write_mb"],
                "network_sent_mb": metric["network"]["bytes_sent_mb"],
                "network_recv_mb": metric["network"]["bytes_recv_mb"],
                "process_count": metric["system"]["process_count"]
            }
            flat_data.append(flat_entry)
        
        df = pd.DataFrame(flat_data)
        filepath = Path(f"C:\\Career_Transition\\data\\{filename}.xlsx")
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_excel(filepath, index=False)
        print(f"📊 Saved performance data to {filepath}")
        
        # Create simple analysis
        if len(df) > 1:
            analysis = {
                "cpu_avg": df["cpu_percent"].mean(),
                "cpu_max": df["cpu_percent"].max(),
                "memory_avg": df["memory_percent"].mean(),
                "memory_min_gb": df["memory_available_gb"].min()
            }
            print("\nPerformance Analysis:")
            for key, value in analysis.items():
                print(f"  {key}: {value:.2f}")
        
        return filepath

# Run performance monitor
monitor = WindowsPerformanceMonitor()
monitor.collect_over_time(duration_seconds=30, interval_seconds=5)
monitor.save_to_excel()
