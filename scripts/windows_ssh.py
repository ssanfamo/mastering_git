# scripts\windows_ssh.py
import paramiko
import getpass
from pathlib import Path

class WindowsSSHManager:
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connected = False
    
    def connect_with_password(self, hostname, username, password, port=22):
        """Connect using password authentication"""
        try:
            self.ssh.connect(
                hostname=hostname,
                username=username,
                password=password,
                port=port,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            self.connected = True
            print(f"✅ Connected to {hostname}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def connect_with_key(self, hostname, username, key_path, port=22):
        """Connect using SSH key"""
        try:
            key = paramiko.RSAKey.from_private_key_file(key_path)
            self.ssh.connect(
                hostname=hostname,
                username=username,
                pkey=key,
                port=port,
                timeout=10
            )
            self.connected = True
            print(f"✅ Connected to {hostname} with key")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def execute_remote(self, command):
        """Execute command on remote server"""
        if not self.connected:
            print("Not connected")
            return None
        
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            exit_code = stdout.channel.recv_exit_status()
            
            return {
                "command": command,
                "output": output,
                "error": error,
                "exit_code": exit_code
            }
        except Exception as e:
            return {"command": command, "error": str(e), "exit_code": -1}
    
    def transfer_file(self, local_path, remote_path):
        """Transfer file using SFTP"""
        if not self.connected:
            print("Not connected")
            return False
        
        try:
            sftp = self.ssh.open_sftp()
            
            if Path(local_path).is_dir():
                # Directory transfer
                self._transfer_directory(sftp, local_path, remote_path)
            else:
                # File transfer
                sftp.put(local_path, remote_path)
            
            sftp.close()
            print(f"📁 Transferred {local_path} to {remote_path}")
            return True
        except Exception as e:
            print(f"❌ Transfer failed: {e}")
            return False
    
    def close(self):
        """Close connection"""
        if self.connected:
            self.ssh.close()
            self.connected = False
            print("Connection closed")

# Test with local VM (WSL2 or VirtualBox)
ssh_manager = WindowsSSHManager()

# For WSL2 Ubuntu (if installed)
if ssh_manager.connect_with_password("localhost", "your_wsl_username", "your_password", 2222):
    result = ssh_manager.execute_remote("uname -a")
    print("WSL Info:", result["output"])
    ssh_manager.close()

# For VirtualBox VM (NAT network)
# ssh_manager.connect_with_password("192.168.56.101", "vagrant", "vagrant")
