# scripts\windows_registry.py
import winreg
import json
from pathlib import Path
from datetime import datetime

class WindowsRegistryManager:
    """Safely interact with Windows Registry"""
    
    # Registry hive constants
    HIVES = {
        'HKCR': winreg.HKEY_CLASSES_ROOT,
        'HKCU': winreg.HKEY_CURRENT_USER,
        'HKLM': winreg.HKEY_LOCAL_MACHINE,
        'HKU': winreg.HKEY_USERS,
        'HKCC': winreg.HKEY_CURRENT_CONFIG
    }
    
    @staticmethod
    def read_registry_value(hive_name, key_path, value_name):
        """Read a value from Windows Registry"""
        try:
            hive = WindowsRegistryManager.HIVES.get(hive_name.upper())
            if hive is None:
                return {"error": f"Invalid hive: {hive_name}"}
            
            # Open the key
            key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
            
            try:
                # Read the value
                value, value_type = winreg.QueryValueEx(key, value_name)
                
                # Convert value type to string
                type_names = {
                    winreg.REG_SZ: "REG_SZ",
                    winreg.REG_EXPAND_SZ: "REG_EXPAND_SZ",
                    winreg.REG_BINARY: "REG_BINARY",
                    winreg.REG_DWORD: "REG_DWORD",
                    winreg.REG_MULTI_SZ: "REG_MULTI_SZ",
                    winreg.REG_QWORD: "REG_QWORD"
                }
                
                return {
                    "success": True,
                    "value": value,
                    "type": type_names.get(value_type, f"UNKNOWN ({value_type})"),
                    "type_code": value_type
                }
            finally:
                winreg.CloseKey(key)
                
        except FileNotFoundError:
            return {"error": f"Registry path not found: {hive_name}\\{key_path}\\{value_name}"}
        except PermissionError:
            return {"error": "Permission denied. Try running as Administrator."}
        except Exception as e:
            return {"error": f"Error reading registry: {str(e)}"}
    
    @staticmethod
    def list_registry_keys(hive_name, key_path):
        """List subkeys and values in a registry path"""
        try:
            hive = WindowsRegistryManager.HIVES.get(hive_name.upper())
            if hive is None:
                return {"error": f"Invalid hive: {hive_name}"}
            
            key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
            
            try:
                result = {
                    "path": f"{hive_name}\\{key_path}",
                    "subkeys": [],
                    "values": []
                }
                
                # Get subkey count
                try:
                    subkey_count = winreg.QueryInfoKey(key)[0]
                    
                    # List subkeys
                    for i in range(subkey_count):
                        subkey_name = winreg.EnumKey(key, i)
                        result["subkeys"].append(subkey_name)
                
                except OSError:
                    pass  # No subkeys or can't read them
                
                # Get value count
                try:
                    value_count = winreg.QueryInfoKey(key)[1]
                    
                    # List values
                    for i in range(value_count):
                        value_name, value_data, value_type = winreg.EnumValue(key, i)
                        
                        # Convert value type to string
                        type_names = {
                            winreg.REG_SZ: "REG_SZ",
                            winreg.REG_EXPAND_SZ: "REG_EXPAND_SZ",
                            winreg.REG_BINARY: "REG_BINARY",
                            winreg.REG_DWORD: "REG_DWORD",
                            winreg.REG_MULTI_SZ: "REG_MULTI_SZ",
                            winreg.REG_QWORD: "REG_QWORD"
                        }
                        
                        result["values"].append({
                            "name": value_name,
                            "type": type_names.get(value_type, f"UNKNOWN ({value_type})"),
                            "data": str(value_data)[:100] + "..." if len(str(value_data)) > 100 else str(value_data)
                        })
                
                except OSError:
                    pass  # No values or can't read them
                
                return {"success": True, "data": result}
                
            finally:
                winreg.CloseKey(key)
                
        except FileNotFoundError:
            return {"error": f"Registry path not found: {hive_name}\\{key_path}"}
        except PermissionError:
            return {"error": "Permission denied. Try running as Administrator."}
        except Exception as e:
            return {"error": f"Error listing registry: {str(e)}"}
    
    @staticmethod
    def get_windows_info_from_registry():
        """Get Windows information from registry"""
        info = {}
        
        # Windows version info
        version_paths = [
            ("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "ProductName"),
            ("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "CurrentVersion"),
            ("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "CurrentBuild"),
            ("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "InstallDate"),
            ("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "RegisteredOwner")
        ]
        
        print("🪟 WINDOWS REGISTRY INFORMATION:")
        print("=" * 60)
        
        for hive, path, value in version_paths:
            result = WindowsRegistryManager.read_registry_value(hive, path, value)
            if result.get("success"):
                friendly_name = value.replace("ProductName", "Windows Edition").replace("CurrentVersion", "Version").replace("CurrentBuild", "Build").replace("InstallDate", "Install Date").replace("RegisteredOwner", "Registered Owner")
                
                # Format the value
                display_value = result["value"]
                if value == "InstallDate":
                    # Convert Unix timestamp to readable date
                    from datetime import datetime
                    try:
                        install_date = datetime.fromtimestamp(int(display_value))
                        display_value = install_date.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                
                print(f"  {friendly_name}: {display_value}")
                info[friendly_name] = display_value
        
        return info
    
    @staticmethod
    def backup_registry_key(hive_name, key_path, output_file="registry_backup.json"):
        """Backup a registry key to JSON file"""
        print(f"💾 Backing up registry: {hive_name}\\{key_path}")
        
        result = WindowsRegistryManager.list_registry_keys(hive_name, key_path)
        
        if result.get("success"):
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "hive": hive_name,
                "path": key_path,
                "data": result["data"]
            }
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ Backup saved to: {output_file}")
            print(f"  📊 Subkeys: {len(result['data']['subkeys'])}")
            print(f"  📊 Values: {len(result['data']['values'])}")
            
            return output_file
        else:
            print(f"  ❌ Backup failed: {result.get('error', 'Unknown error')}")
            return None

# Example usage - SAFE READ-ONLY OPERATIONS ONLY
registry_mgr = WindowsRegistryManager()

# Get Windows info from registry
windows_info = registry_mgr.get_windows_info_from_registry()

# List some common registry locations
common_paths = [
    ("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    ("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    ("HKLM", r"SYSTEM\CurrentControlSet\Services"),
]

print("\n🔍 COMMON REGISTRY LOCATIONS:")
for hive, path in common_paths:
    print(f"\n{hive}\\{path}:")
    result = registry_mgr.list_registry_keys(hive, path)
    
    if result.get("success"):
        data = result["data"]
        print(f"  Subkeys: {len(data['subkeys'])}")
        print(f"  Values: {len(data['values'])}")
        
        # Show first few items
        if data['subkeys']:
            print(f"  First 3 subkeys: {', '.join(data['subkeys'][:3])}")
        if data['values']:
            print(f"  Values found: {', '.join([v['name'] for v in data['values'][:3]])}")
    else:
        print(f"  Error: {result.get('error', 'Unknown')}")

# Backup a registry key (read-only, safe)
print("\n" + "="*60)
backup_file = registry_mgr.backup_registry_key(
    "HKLM", 
    r"SOFTWARE\Microsoft\Windows\CurrentVersion", 
    "windows_current_version_backup.json"
)