# test_simple.py
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    # Import the module
    from windows_system_info_enhanced import SystemMonitor
    
    print("Testing System Monitor...")
    
    # Create monitor instance
    monitor = SystemMonitor("monitor_config.yaml")
    
    # Run monitoring cycle
    print("Running monitoring cycle...")
    info = monitor.run_monitoring_cycle()
    
    # Display results
    print(f"\n✓ Monitoring complete!")
    print(f"Timestamp: {info['timestamp']}")
    print(f"Hostname: {info['system']['hostname']}")
    print(f"CPU: {info['hardware']['cpu_percent']}%")
    print(f"Memory: {info['hardware']['memory_percent']}%")
    
    print("\nCritical Services:")
    for service, status in info['services'].items():
        print(f"  {service}: {status['status']}")
        
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure 'windows_system_info_enhanced.py' is in the same directory")
except Exception as e:
    print(f"✗ Error: {e}")