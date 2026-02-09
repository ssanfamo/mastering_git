# service_wrapper.py
import os
import sys
import time
from pathlib import Path
import traceback

# Set working directory to script location
SCRIPT_DIR = Path(__file__).parent
os.chdir(SCRIPT_DIR)

# Log file paths
RUNTIME_LOG = SCRIPT_DIR / "service_runtime.log"
ERROR_LOG = SCRIPT_DIR / "service_errors.log"

def log_message(message, is_error=False):
    """Log message to appropriate file"""
    log_file = ERROR_LOG if is_error else RUNTIME_LOG
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

try:
    # Initial log
    log_message(f"Service starting. Python: {sys.executable}")
    log_message(f"Working directory: {os.getcwd()}")
    
    # Import and run monitor
    sys.path.insert(0, str(SCRIPT_DIR))
    from windows_system_info_enhanced import SystemMonitor
    
    log_message("Import successful, creating monitor...")
    
    # Create monitor
    monitor = SystemMonitor()
    log_message(f"Monitor created. Interval: {monitor.config['monitoring']['interval_minutes']} minutes")
    
    # Run one initial cycle to verify
    log_message("Running initial monitoring cycle...")
    info = monitor.run_monitoring_cycle()
    log_message(f"Initial cycle complete: {info['system']['hostname']}")
    
    # Start continuous monitoring
    log_message("Starting continuous monitoring...")
    monitor.start_continuous_monitoring()
    
except KeyboardInterrupt:
    log_message("Service stopped by user request")
    sys.exit(0)
except Exception as e:
    error_msg = f"FATAL ERROR: {type(e).__name__}: {str(e)}"
    log_message(error_msg, is_error=True)
    
    # Write full traceback to error log
    with open(ERROR_LOG, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Full traceback at {time.ctime()}:\n")
        traceback.print_exc(file=f)
        f.write(f"{'='*60}\n")
    
    # Exit with error code (NSSM will restart if configured)
    time.sleep(5)
    sys.exit(1)
