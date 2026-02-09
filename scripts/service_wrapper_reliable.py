# service_wrapper_reliable.py
import os
import sys
import time
from pathlib import Path
import traceback

def setup_environment():
    """Setup proper environment for service"""
    # Set working directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Log startup
    log_file = script_dir / "service_runtime.log"
    with open(log_file, 'a') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Service started: {time.ctime()}\n")
        f.write(f"Python: {sys.version}\n")
        f.write(f"Current dir: {os.getcwd()}\n")
        f.write(f"Python path: {sys.executable}\n")
        f.write(f"Sys.path: {sys.path[:3]}\n")
    
    return script_dir, log_file

def run_monitor():
    """Run the system monitor"""
    script_dir, log_file = setup_environment()
    
    try:
        # Add to path
        sys.path.insert(0, str(script_dir))
        
        # Try to import
        with open(log_file, 'a') as f:
            f.write("Attempting import...\n")
        
        from windows_system_info_enhanced import SystemMonitor
        
        with open(log_file, 'a') as f:
            f.write("Import successful\n")
        
        # Create monitor
        monitor = SystemMonitor()
        
        with open(log_file, 'a') as f:
            f.write(f"Monitor created. Config: {monitor.config['monitoring']['interval_minutes']} min interval\n")
        
        # Run continuously
        monitor.start_continuous_monitoring()
        
    except Exception as e:
        error_msg = f"ERROR: {type(e).__name__}: {e}"
        with open(log_file, 'a') as f:
            f.write(f"{error_msg}\n")
            traceback.print_exc(file=f)
        
        # Also write to separate error log
        error_log = script_dir / "service_errors.log"
        with open(error_log, 'a') as f:
            f.write(f"{time.ctime()}: {error_msg}\n")
            traceback.print_exc(file=f)
        
        # Wait and exit (NSSM will restart if configured)
        time.sleep(10)
        sys.exit(1)

if __name__ == '__main__':
    run_monitor()
