# scripts\windows_task_automation.py
import schedule
import time
from datetime import datetime
import winsound  # Windows sound alerts
import win10toast  # Windows 10 notifications

class WindowsTaskScheduler:
    def __init__(self):
        self.toaster = win10toast.ToastNotifier()
        self.tasks = {}
    
    def add_daily_task(self, name, time_str, function, *args, **kwargs):
        """Schedule a daily task"""
        schedule.every().day.at(time_str).do(
            self._execute_task, name, function, *args, **kwargs
        )
        self.tasks[name] = {"schedule": f"Daily at {time_str}", "last_run": None}
        print(f"✅ Scheduled task '{name}' daily at {time_str}")
    
    def add_hourly_task(self, name, function, *args, **kwargs):
        """Schedule an hourly task"""
        schedule.every().hour.do(
            self._execute_task, name, function, *args, **kwargs
        )
        self.tasks[name] = {"schedule": "Hourly", "last_run": None}
        print(f"✅ Scheduled task '{name}' hourly")
    
    def _execute_task(self, name, function, *args, **kwargs):
        """Execute task with notification"""
        try:
            print(f"\n[{datetime.now()}] Running task: {name}")
            result = function(*args, **kwargs)
            self.tasks[name]["last_run"] = datetime.now()
            
            # Show Windows notification
            self.toaster.show_toast(
                f"Task Completed: {name}",
                f"Ran successfully at {datetime.now().strftime('%H:%M')}",
                duration=5
            )
            
            # Play sound alert
            winsound.Beep(1000, 200)  # Frequency, Duration
            
            return result
        except Exception as e:
            print(f"❌ Task '{name}' failed: {e}")
            self.toaster.show_toast(
                f"Task Failed: {name}",
                str(e),
                duration=10
            )
            winsound.Beep(500, 500)  # Error tone
    
    def run_pending(self):
        """Run all pending tasks"""
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                print("\nTask scheduler stopped")
                break
            except Exception as e:
                print(f"Scheduler error: {e}")

# Example tasks
def check_disk_space():
    """Check disk space and alert if low"""
    import psutil
    import shutil
    
    for partition in psutil.disk_partitions():
        if 'cdrom' in partition.opts or partition.fstype == '':
            continue
        
        usage = psutil.disk_usage(partition.mountpoint)
        if usage.percent > 85:
            print(f"⚠️  Low disk space on {partition.device}: {usage.percent}% used")
            return f"Low disk space on {partition.device}"
    
    return "Disk space OK"

def check_internet_connection():
    """Check internet connectivity"""
    import urllib.request
    import socket
    
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        urllib.request.urlopen("http://google.com", timeout=3)
        return "Internet connection OK"
    except:
        return "No internet connection"

def backup_important_files():
    """Backup important files"""
    file_mgr = WindowsFileManager()
    
    important_paths = [
        r"C:\Career-Transition\learning\journal.md",
        r"C:\Career-Transition\scripts"
    ]
    
    for path in important_paths:
        if Path(path).exists():
            file_mgr.create_windows_backup(path)
    
    return "Backup completed"

# Create scheduler
scheduler = WindowsTaskScheduler()

# Schedule tasks
scheduler.add_daily_task("Morning Check", "08:00", check_disk_space)
scheduler.add_daily_task("Backup Files", "18:00", backup_important_files)
scheduler.add_hourly_task("Internet Check", check_internet_connection)

print("\nTask Scheduler Started. Press Ctrl+C to stop.")
print("Running tasks:")
for name, info in scheduler.tasks.items():
    print(f"  {name}: {info['schedule']}")

# Run in background thread
import threading
scheduler_thread = threading.Thread(target=scheduler.run_pending, daemon=True)
scheduler_thread.start()
