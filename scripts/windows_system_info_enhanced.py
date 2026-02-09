# scripts\windows_system_info_enhanced.py
import platform
import psutil
import socket
from datetime import datetime, timedelta
import json
import yaml
import logging
import time
import schedule
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Add to imports
from notifications import NotificationManager

# In SystemMonitor.__init__():
class SystemMonitor:
    def __init__(self, config_file="monitor_config.yaml"):
        # ... existing code ...
        self.notification_manager = None
        self._setup_notifications()
    
    def _setup_notifications(self):
        """Setup notification channels"""
        notification_config = self.config.get('notifications', {})
        if any(channel.get('enabled', False) 
               for channel in notification_config.values()):
            self.notification_manager = NotificationManager(notification_config)
            self.logger.info("Notification system initialized")
    
    # Update monitor_services method
    def monitor_services(self):
        """Monitor critical services and send alerts if any are stopped"""
        info = self.get_windows_system_info()
        
        for service, status_info in info['services'].items():
            if status_info.get('status') == 'Stopped':
                message = f"Critical service {service} is stopped"
                self.logger.critical(message)
                
                # Send email alert (existing)
                self.send_alert("Service Stopped", message)
                
                # Send notifications (new)
                if self.notification_manager:
                    self.notification_manager.send_to_all(
                        message=message,
                        title="Critical Service Alert",
                        alert_type="critical"
                    )

# Configure logging
def setup_logging(log_level=logging.INFO, log_file="system_monitor.log"):
    """Setup comprehensive logging configuration"""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class SystemMonitor:
    """Enhanced system monitoring with logging, export, alerts, and historical tracking"""
    
    def __init__(self, config_file="monitor_config.yaml"):
        self.logger = logger
        self.config = self._load_config(config_file)
        self.db_path = Path(self.config.get('database_path', 'system_metrics.db'))
        self._init_database()
        
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from YAML file"""
        default_config = {
            'monitoring': {
                'interval_minutes': 5,
                'critical_services': ['WinRM', 'Dhcp', 'Dnscache', 'EventLog'],
                'cpu_threshold': 90,
                'memory_threshold': 85
            },
            'alerting': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'email_from': 'your_email@gmail.com',
                'email_to': 'admin@example.com',
                'email_subject': 'System Alert'
            },
            'export': {
                'json_path': 'system_info.json',
                'yaml_path': 'system_info.yaml',
                'auto_export': True
            },
            'database_path': 'system_metrics.db'
        }
        
        try:
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f) or {}
            # Merge with default config
            default_config.update(user_config)
            self.logger.info(f"Configuration loaded from {config_file}")
        except FileNotFoundError:
            self.logger.warning(f"Config file {config_file} not found, using defaults")
        
        return default_config
    
    def get_windows_system_info(self) -> Dict:
        """Get detailed Windows system information with enhanced logging"""
        self.logger.info("Collecting system information...")
        
        info = {
            "timestamp": datetime.now().isoformat(),
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
                "memory_percent": psutil.virtual_memory().percent,
                "disk_partitions": []
            },
            "network": {
                "ip_address": socket.gethostbyname(socket.gethostname()),
                "interfaces": []
            },
            "services": {}
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
            except Exception as e:
                self.logger.warning(f"Could not read partition {partition.mountpoint}: {e}")
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
        
        # Check services
        info["services"] = self.check_windows_services(
            self.config['monitoring']['critical_services']
        )
        
        # Check thresholds and log warnings
        self._check_thresholds(info)
        
        self.logger.info("System information collected successfully")
        return info
    
    def check_windows_services(self, service_names: List[str]) -> Dict:
        """Check status of Windows services with improved error handling"""
        services_status = {}
        
        for service in service_names:
            try:
                # Using WMI for more reliable service checking
                import wmi
                c = wmi.WMI()
                svc = c.Win32_Service(Name=service)[0]
                services_status[service] = {
                    "status": svc.State,
                    "start_mode": svc.StartMode,
                    "started": svc.Started
                }
            except Exception as e:
                services_status[service] = {
                    "status": "Not Found",
                    "error": str(e)
                }
                self.logger.error(f"Error checking service {service}: {e}")
        
        return services_status
    
    def _check_thresholds(self, info: Dict):
        """Check system metrics against configured thresholds"""
        cpu_percent = info['hardware']['cpu_percent']
        memory_percent = info['hardware']['memory_percent']
        
        cpu_threshold = self.config['monitoring']['cpu_threshold']
        memory_threshold = self.config['monitoring']['memory_threshold']
        
        if cpu_percent > cpu_threshold:
            self.logger.warning(f"High CPU usage: {cpu_percent}% (threshold: {cpu_threshold}%)")
        
        if memory_percent > memory_threshold:
            self.logger.warning(f"High memory usage: {memory_percent}% (threshold: {memory_threshold}%)")
    
    def export_to_file(self, info: Dict, format_type: str = "json") -> bool:
        """Export system information to JSON or YAML file"""
        export_config = self.config['export']
        
        try:
            if format_type == "json":
                filepath = export_config['json_path']
                with open(filepath, 'w') as f:
                    json.dump(info, f, indent=2, default=str)
            elif format_type == "yaml":
                filepath = export_config['yaml_path']
                with open(filepath, 'w') as f:
                    yaml.dump(info, f, default_flow_style=False)
            else:
                self.logger.error(f"Unsupported format: {format_type}")
                return False
            
            self.logger.info(f"System info exported to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return False
    
    def _init_database(self):
        """Initialize SQLite database for historical tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_available_gb REAL,
                    disk_usage_percent REAL,
                    service_status TEXT
                )
            ''')
            
            # Create alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    alert_type TEXT,
                    message TEXT,
                    resolved BOOLEAN DEFAULT 0
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
    
    def store_metrics(self, info: Dict):
        """Store current metrics in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate average disk usage
            disk_usages = [p['percent_used'] for p in info['hardware']['disk_partitions']]
            avg_disk_usage = sum(disk_usages) / len(disk_usages) if disk_usages else 0
            
            # Convert service status to JSON string
            service_status = json.dumps(info['services'])
            
            cursor.execute('''
                INSERT INTO system_metrics 
                (timestamp, cpu_percent, memory_percent, memory_available_gb, disk_usage_percent, service_status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                info['timestamp'],
                info['hardware']['cpu_percent'],
                info['hardware']['memory_percent'],
                info['hardware']['memory_available_gb'],
                avg_disk_usage,
                service_status
            ))
            
            conn.commit()
            conn.close()
            self.logger.debug("Metrics stored in database")
            
        except Exception as e:
            self.logger.error(f"Failed to store metrics: {e}")
    
    def send_alert(self, alert_type: str, message: str):
        """Send email alert for critical events"""
        alert_config = self.config['alerting']
        
        if not alert_config['enabled']:
            self.logger.debug("Alerting is disabled")
            return False
        
        try:
            # Store alert in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO alerts (timestamp, alert_type, message) VALUES (?, ?, ?)",
                (datetime.now().isoformat(), alert_type, message)
            )
            conn.commit()
            conn.close()
            
            # Send email
            msg = MIMEMultipart()
            msg['From'] = alert_config['email_from']
            msg['To'] = alert_config['email_to']
            msg['Subject'] = f"{alert_config['email_subject']}: {alert_type}"
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Note: You'll need to configure SMTP credentials properly
            # This is a template - implement your SMTP authentication
            self.logger.warning("Email alerting requires SMTP configuration")
            
            # Example SMTP send (commented out for safety):
            # with smtplib.SMTP(alert_config['smtp_server'], alert_config['smtp_port']) as server:
            #     server.starttls()
            #     server.login(alert_config['email_from'], 'your_password')
            #     server.send_message(msg)
            
            self.logger.info(f"Alert generated: {alert_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")
            return False
    
    def monitor_services(self):
        """Monitor critical services and send alerts if any are stopped"""
        info = self.get_windows_system_info()
        
        for service, status_info in info['services'].items():
            if status_info.get('status') == 'Stopped':
                message = f"Critical service {service} is stopped"
                self.logger.critical(message)
                self.send_alert("Service Stopped", message)
    
    def generate_report(self, hours: int = 24) -> Dict:
        """Generate historical report from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get metrics from last X hours
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute('''
                SELECT 
                    timestamp,
                    AVG(cpu_percent) as avg_cpu,
                    MAX(cpu_percent) as max_cpu,
                    AVG(memory_percent) as avg_memory,
                    MAX(memory_percent) as max_memory,
                    COUNT(*) as samples
                FROM system_metrics 
                WHERE timestamp > ?
                GROUP BY strftime('%Y-%m-%d %H', timestamp)
            ''', (cutoff_time,))
            
            rows = cursor.fetchall()
            
            # Get recent alerts
            cursor.execute('''
                SELECT alert_type, COUNT(*) as count
                FROM alerts 
                WHERE timestamp > ? AND resolved = 0
                GROUP BY alert_type
            ''', (cutoff_time,))
            
            alerts = cursor.fetchall()
            
            conn.close()
            
            report = {
                "period_hours": hours,
                "metrics_timeline": [
                    {
                        "hour": row[0],
                        "avg_cpu": row[1],
                        "max_cpu": row[2],
                        "avg_memory": row[3],
                        "max_memory": row[4],
                        "samples": row[5]
                    } for row in rows
                ],
                "active_alerts": [
                    {"type": alert[0], "count": alert[1]} for alert in alerts
                ],
                "generated_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Generated {hours}-hour report with {len(rows)} data points")
            return report
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return {}
    
    def run_monitoring_cycle(self):
        """Execute one complete monitoring cycle"""
        self.logger.info("Starting monitoring cycle...")
        
        # Collect system info
        info = self.get_windows_system_info()
        
        # Store metrics
        self.store_metrics(info)
        
        # Auto-export if configured
        if self.config['export']['auto_export']:
            self.export_to_file(info, "json")
            self.export_to_file(info, "yaml")
        
        # Monitor services
        self.monitor_services()
        
        self.logger.info("Monitoring cycle completed")
        return info
    
    def start_continuous_monitoring(self):
        """Start continuous monitoring with scheduled intervals"""
        interval = self.config['monitoring']['interval_minutes']
        
        schedule.every(interval).minutes.do(self.run_monitoring_cycle)
        
        self.logger.info(f"Continuous monitoring started (interval: {interval} minutes)")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")


# Example configuration file (monitor_config.yaml)
CONFIG_TEMPLATE = """
monitoring:
  interval_minutes: 5
  critical_services: ['WinRM', 'Dhcp', 'Dnscache', 'EventLog']
  cpu_threshold: 90
  memory_threshold: 85

alerting:
  enabled: false
  smtp_server: 'smtp.gmail.com'
  smtp_port: 587
  email_from: 'your_email@gmail.com'
  email_to: 'admin@example.com'
  email_subject: 'System Alert'

export:
  json_path: 'system_info.json'
  yaml_path: 'system_info.yaml'
  auto_export: true

database_path: 'system_metrics.db'
"""


if __name__ == "__main__":
    # Create sample config file if it doesn't exist
    config_path = "monitor_config.yaml"
    if not Path(config_path).exists():
        with open(config_path, 'w') as f:
            f.write(CONFIG_TEMPLATE)
        logger.info(f"Created sample config file: {config_path}")
    
    # Initialize monitor
    monitor = SystemMonitor(config_path)
    
    # Run once
    print("=" * 60)
    print("Windows System Monitor - Enhanced Version")
    print("=" * 60)
    
    info = monitor.run_monitoring_cycle()
    
    print(f"\nSystem Summary:")
    print(f"  Hostname: {info['system']['hostname']}")
    print(f"  OS: {info['system']['os']} {info['system']['release']}")
    print(f"  CPU: {info['hardware']['cpu_percent']}% used")
    print(f"  Memory: {info['hardware']['memory_percent']}% used")
    
    # Generate report
    report = monitor.generate_report(24)
    if report:
        print(f"\n24-Hour Report:")
        print(f"  Data points: {len(report['metrics_timeline'])}")
        print(f"  Active alerts: {len(report['active_alerts'])}")
    
    # Uncomment to start continuous monitoring:
    # print("\nStarting continuous monitoring... (Ctrl+C to stop)")
    # monitor.start_continuous_monitoring()