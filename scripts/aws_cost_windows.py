# scripts\aws_cost_windows.py
import boto3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

class WindowsAWSCostManager:
    def __init__(self, profile_name='automation'):
        self.session = boto3.Session(profile_name=profile_name)
        self.ce = self.session.client('ce')
        self.reports_dir = Path("C:/Career_Transition/reports/aws-costs")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cost_and_usage(self, days=7):
        """Get AWS cost and usage data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'REGION'}
                ]
            )
            
            return self._parse_cost_data(response)
            
        except Exception as e:
            print(f"❌ Error getting cost data: {e}")
            # Check if Cost Explorer is enabled
            if "not subscribed to AWS Cost Explorer" in str(e):
                print("💡 Enable Cost Explorer in AWS Billing Console first")
            return None
    
    def _parse_cost_data(self, response):
        """Parse Cost Explorer response into structured data"""
        daily_costs = {}
        service_totals = {}
        region_totals = {}
        
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            daily_total = 0
            
            for group in result['Groups']:
                service = group['Keys'][0]
                region = group['Keys'][1] if len(group['Keys']) > 1 else 'N/A'
                amount = float(group['Metrics']['UnblendedCost']['Amount'])
                
                daily_total += amount
                
                # Track service totals
                service_totals[service] = service_totals.get(service, 0) + amount
                
                # Track region totals
                region_totals[region] = region_totals.get(region, 0) + amount
            
            daily_costs[date] = {
                'total': round(daily_total, 2),
                'date': date
            }
        
        # Sort services by cost
        top_services = dict(sorted(
            service_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])  # Top 10 services
        
        return {
            'daily_costs': daily_costs,
            'top_services': top_services,
            'region_totals': region_totals,
            'total_cost': sum(service_totals.values())
        }
    
    def create_cost_report_excel(self, cost_data, filename=None):
        """Create Excel cost report (Windows-friendly)"""
        if not cost_data:
            print("❌ No cost data to report")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"aws_cost_report_{timestamp}.xlsx"
        
        filepath = self.reports_dir / filename
        
        # Create Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Daily costs sheet
            daily_df = pd.DataFrame([
                {'Date': date, 'Cost ($)': data['total']}
                for date, data in cost_data['daily_costs'].items()
            ])
            daily_df.to_excel(writer, sheet_name='Daily Costs', index=False)
            
            # Top services sheet
            services_df = pd.DataFrame([
                {'Service': service, 'Cost ($)': round(cost, 2)}
                for service, cost in cost_data['top_services'].items()
            ])
            services_df.to_excel(writer, sheet_name='Top Services', index=False)
            
            # Region costs sheet
            regions_df = pd.DataFrame([
                {'Region': region, 'Cost ($)': round(cost, 2)}
                for region, cost in cost_data['region_totals'].items()
            ])
            regions_df.to_excel(writer, sheet_name='Region Costs', index=False)
            
            # Summary sheet
            summary_data = {
                'Metric': ['Total Cost', 'Days Analyzed', 'Average Daily Cost', 'Report Generated'],
                'Value': [
                    f"${round(cost_data['total_cost'], 2)}",
                    len(cost_data['daily_costs']),
                    f"${round(cost_data['total_cost'] / len(cost_data['daily_costs']), 2)}",
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        print(f"📊 Excel report saved to: {filepath}")
        return filepath
    
    def create_cost_alert(self, daily_threshold=10, weekly_threshold=50):
        """Check if costs exceed thresholds and alert"""
        cost_data = self.get_cost_and_usage(days=7)
        
        if not cost_data:
            return
        
        # Check daily threshold
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_cost = cost_data['daily_costs'].get(yesterday, {}).get('total', 0)
        
        if yesterday_cost > daily_threshold:
            print(f"⚠️  ALERT: Yesterday's cost (${yesterday_cost}) exceeded daily threshold (${daily_threshold})")
            
            # Windows notification
            try:
                import win10toast
                toaster = win10toast.ToastNotifier()
                toaster.show_toast(
                    "AWS Cost Alert",
                    f"Yesterday's cost: ${yesterday_cost} (Threshold: ${daily_threshold})",
                    duration=10
                )
            except:
                pass
        
        # Check weekly threshold
        if cost_data['total_cost'] > weekly_threshold:
            print(f"⚠️  ALERT: Weekly cost (${cost_data['total_cost']:.2f}) exceeded weekly threshold (${weekly_threshold})")
        
        return {
            'yesterday_cost': yesterday_cost,
            'weekly_cost': cost_data['total_cost'],
            'daily_alert': yesterday_cost > daily_threshold,
            'weekly_alert': cost_data['total_cost'] > weekly_threshold
        }

# Example usage
cost_manager = WindowsAWSCostManager()

# Get last 7 days of costs
cost_data = cost_manager.get_cost_and_usage(days=7)

if cost_data:
    print(f"\n💰 AWS Cost Report (Last 7 days)")
    print(f"Total Cost: ${cost_data['total_cost']:.2f}")
    print(f"Average Daily: ${cost_data['total_cost'] / 7:.2f}")
    
    print("\nTop 5 Services by Cost:")
    for i, (service, cost) in enumerate(list(cost_data['top_services'].items())[:5], 1):
        print(f"  {i}. {service}: ${cost:.2f}")
    
    # Create Excel report
    excel_file = cost_manager.create_cost_report_excel(cost_data)
    
    # Check for cost alerts
    alerts = cost_manager.create_cost_alert(daily_threshold=5, weekly_threshold=30)
