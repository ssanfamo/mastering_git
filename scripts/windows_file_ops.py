# scripts\windows_file_ops.py
import os
import json
import csv
import shutil
from pathlib import Path, PureWindowsPath
from datetime import datetime
import win32file  # For Windows-specific file operations

class WindowsFileManager:
    def __init__(self, base_dir="C:\\Career_Transition\\data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_inventory_json(self, data, filename):
        """Save inventory data as JSON with Windows path handling"""
        filepath = self.base_dir / f"{filename}.json"
        
        enhanced_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generated_on": platform.node(),
                "windows_path": str(filepath)
            },
            "data": data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Saved to {filepath}")
        return str(filepath)
    
    def save_windows_csv(self, data, filename, fieldnames):
        """Save data as CSV with Windows line endings"""
        filepath = self.base_dir / f"{filename}.csv"
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        print(f"📁 Saved CSV to {filepath}")
        return str(filepath)
    
    def create_windows_backup(self, source_path, backup_prefix="backup"):
        """Create timestamped backup of a file/directory"""
        source = Path(source_path)
        if not source.exists():
            print(f"❌ Source path does not exist: {source_path}")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if source.is_file():
            backup_name = f"{source.stem}_{backup_prefix}_{timestamp}{source.suffix}"
            backup_path = self.base_dir / "backups" / backup_name
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, backup_path)
        
        elif source.is_dir():
            backup_name = f"{source.name}_{backup_prefix}_{timestamp}"
            backup_path = self.base_dir / "backups" / backup_name
            shutil.copytree(source, backup_path)
        
        print(f"💾 Backup created: {backup_path}")
        return str(backup_path)
    
    def get_windows_drives_info(self):
        """Get information about Windows drives"""
        import win32api
        
        drives = []
        for drive in win32api.GetLogicalDriveStrings().split('\000'):
            if drive:
                drive_type = win32file.GetDriveType(drive)
                type_map = {
                    0: "Unknown",
                    1: "No Root",
                    2: "Removable",
                    3: "Local Disk",
                    4: "Network",
                    5: "CD-ROM",
                    6: "RAM Disk"
                }
                
                try:
                    free_bytes = win32file.GetDiskFreeSpaceEx(drive)
                    total_gb = free_bytes[1] / (1024**3)
                    free_gb = free_bytes[0] / (1024**3)
                    used_gb = total_gb - free_gb
                    percent_used = (used_gb / total_gb) * 100 if total_gb > 0 else 0
                    
                    drives.append({
                        "drive": drive.strip('\\'),
                        "type": type_map.get(drive_type, "Unknown"),
                        "total_gb": round(total_gb, 2),
                        "free_gb": round(free_gb, 2),
                        "used_gb": round(used_gb, 2),
                        "percent_used": round(percent_used, 2)
                    })
                except:
                    continue
        
        return drives

# Example usage
file_mgr = WindowsFileManager()

# Save system info
system_info = {
    "hostname": platform.node(),
    "windows_version": platform.version(),
    "python_version": platform.python_version()
}
file_mgr.save_inventory_json(system_info, "system_info")

# Get Windows drives info
drives = file_mgr.get_windows_drives_info()
print("Windows Drives:")
for drive in drives:
    print(f"  {drive['drive']}: {drive['type']} - {drive['used_gb']}GB used of {drive['total_gb']}GB ({drive['percent_used']}%)")
