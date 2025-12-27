# scripts\windows_event_logs.py
import win32evtlog
import win32evtlogutil
import win32con
from datetime import datetime, timedelta
import json

class WindowsEventLogManager:
    """Monitor and analyze Windows Event Logs"""
    
    @staticmethod
    def read_event_log(log_name="Application", last_hours=24, event_types=None):
        """Read events from Windows Event Log"""
        if event_types is None:
            event_types = [win32con.EVENTLOG_ERROR_TYPE, win32con.EVENTLOG_WARNING_TYPE]
        
        hand = win32evtlog.OpenEventLog(None, log_name)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        
        events = []
        cutoff_time = datetime.now() - timedelta(hours=last_hours)
        
        try:
            while True:
                events_batch = win32evtlog.ReadEventLog(hand, flags, 0)
                if not events_batch:
                    break
                
                for event in events_batch:
                    # Check if event is within time range
                    event_time = event.TimeGenerated
                    if event_time < cutoff_time:
                        continue
                    
                    # Filter by event type
                    if event.EventType in event_types:
                        event_data = {
                            'time': event_time.strftime("%Y-%m-%d %H:%M:%S"),
                            'source': event.SourceName,
                            'event_id': event.EventID & 0xFFFF,  # Mask to get actual ID
                            'event_type': WindowsEventLogManager._get_event_type_name(event.EventType),
                            'computer': event.ComputerName,
                            'message': win32evtlogutil.SafeFormatMessage(event, log_name)
                        }
                        events.append(event_data)
                
                if len(events) >= 100:  # Limit to 100 events
                    break
                    
        finally:
            win32evtlog.CloseEventLog(hand)
        
        return events
    
    @staticmethod
    def _get_event_type_name(event_type):
        """Convert event type code to name"""
        event_types = {
            win32con.EVENTLOG_SUCCESS: "Success",
            win32con.EVENTLOG_ERROR_TYPE: "Error",
            win32con.EVENTLOG_WARNING_TYPE: "Warning",
            win32con.EVENTLOG_INFORMATION_TYPE: "Information",
            win32con.EVENTLOG_AUDIT_SUCCESS: "Audit Success",
            win32con.EVENTLOG_AUDIT_FAILURE: "Audit Failure"
        }
        return event_types.get(event_type, f"Unknown ({event_type})")
    
    @staticmethod
    def analyze_events(events):
        """Analyze event patterns"""
        analysis = {
            'total_events': len(events),
            'by_type': {},
            'by_source': {},
            'common_errors': [],
            'timeline': []
        }
        
        for event in events:
            # Count by type
            event_type = event['event_type']
            analysis['by_type'][event_type] = analysis['by_type'].get(event_type, 0) + 1
            
            # Count by source
            source = event['source']
            analysis['by_source'][source] = analysis['by_source'].get(source, 0) + 1
            
            # Track errors for analysis
            if event_type == "Error":
                error_info = {
                    'source': source,
                    'event_id': event['event_id'],
                    'message_preview': event['message'][:100] + "..." if len(event['message']) > 100 else event['message'],
                    'count': 1
                }
                
                # Check if similar error already exists
                existing = next((e for e in analysis['common_errors'] 
                               if e['source'] == source and e['event_id'] == event['event_id']), None)
                if existing:
                    existing['count'] += 1
                else:
                    analysis['common_errors'].append(error_info)
        
        # Sort common errors by count
        analysis['common_errors'].sort(key=lambda x: x['count'], reverse=True)
        
        return analysis
    
    @staticmethod
    def create_event_report(events, output_file="event_log_report.json"):
        """Create comprehensive event log report"""
        if not events:
            print("No events to report")
            return None
        
        analysis = WindowsEventLogManager.analyze_events(events)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'time_range_hours': 24,
            'summary': {
                'total_events': analysis['total_events'],
                'error_count': analysis['by_type'].get('Error', 0),
                'warning_count': analysis['by_type'].get('Warning', 0)
            },
            'analysis': analysis,
            'sample_events': events[:10]  # Include first 10 events as samples
        }
        
        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Event log report saved to: {output_file}")
        
        # Print summary
        print(f"\n📋 EVENT LOG SUMMARY:")
        print(f"   Total events: {report['summary']['total_events']}")
        print(f"   Errors: {report['summary']['error_count']}")
        print(f"   Warnings: {report['summary']['warning_count']}")
        
        if analysis['common_errors']:
            print(f"\n🔴 COMMON ERRORS:")
            for error in analysis['common_errors'][:3]:  # Top 3
                print(f"   {error['source']} (Event ID: {error['event_id']}): {error['count']} occurrences")
        
        return output_file

# Example usage
event_mgr = WindowsEventLogManager()

# Read recent Application log events
print("📖 Reading Application event logs (last 24 hours)...")
app_events = event_mgr.read_event_log("Application", last_hours=24)

if app_events:
    print(f"Found {len(app_events)} Application events")
    
    # Create report
    report_file = event_mgr.create_event_report(app_events)
    
    # Show some sample events
    print("\n📝 SAMPLE EVENTS:")
    for i, event in enumerate(app_events[:3], 1):
        print(f"  {i}. [{event['time']}] {event['source']} - {event['event_type']}")
        print(f"     Message: {event['message'][:100]}..." if len(event['message']) > 100 else f"     Message: {event['message']}")
        print()

# Also check System logs
print("📖 Reading System event logs...")
system_events = event_mgr.read_event_log("System", last_hours=12)
if system_events:
    print(f"Found {len(system_events)} System events")
    
    # Quick analysis
    analysis = event_mgr.analyze_events(system_events)
    print(f"  Errors: {analysis['by_type'].get('Error', 0)}")
    print(f"  Warnings: {analysis['by_type'].get('Warning', 0)}")