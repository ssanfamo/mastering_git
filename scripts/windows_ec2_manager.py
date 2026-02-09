# scripts\windows_ec2_manager.py
import boto3
import time
from datetime import datetime, timedelta

class WindowsEC2Manager:
    def __init__(self, profile_name='automation'):
        self.session = boto3.Session(profile_name=profile_name)
        self.ec2 = self.session.client('ec2')
        self.ssm = self.session.client('ssm')  # For managing Windows instances
    
    def manage_windows_instances(self):
        """Manage Windows EC2 instances"""
        instances = self.list_windows_instances()
        
        print(f"Found {len(instances)} Windows instances:")
        print("=" * 80)
        
        for instance in instances:
            print(f"🪟 {instance['InstanceId']}")
            print(f"   Name: {instance.get('Name', 'N/A')}")
            print(f"   State: {instance['State']}")
            print(f"   Type: {instance['InstanceType']}")
            print(f"   Launch Time: {instance['LaunchTime']}")
            print(f"   Public IP: {instance.get('PublicIpAddress', 'N/A')}")
            print(f"   Private IP: {instance.get('PrivateIpAddress', 'N/A')}")
            print()
        
        return instances
    
    def list_windows_instances(self):
        """List only Windows instances"""
        try:
            response = self.ec2.describe_instances(
                Filters=[
                    {'Name': 'platform', 'Values': ['windows']}
                ]
            )
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    # Extract name tag
                    name = 'N/A'
                    for tag in instance.get('Tags', []):
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                    
                    instance_info = {
                        'InstanceId': instance['InstanceId'],
                        'Name': name,
                        'State': instance['State']['Name'],
                        'InstanceType': instance['InstanceType'],
                        'LaunchTime': instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S'),
                        'PublicIpAddress': instance.get('PublicIpAddress'),
                        'PrivateIpAddress': instance.get('PrivateIpAddress'),
                        'VpcId': instance.get('VpcId'),
                        'SubnetId': instance.get('SubnetId')
                    }
                    instances.append(instance_info)
            
            return instances
            
        except Exception as e:
            print(f"❌ Error listing Windows instances: {e}")
            return []
    
    def run_ssm_command_on_windows(self, instance_id, command):
        """Run PowerShell command on Windows instance via SSM"""
        try:
            # Check if instance has SSM agent
            response = self.ssm.describe_instance_information(
                Filters=[
                    {'Key': 'InstanceIds', 'Values': [instance_id]}
                ]
            )
            
            if not response['InstanceInformationList']:
                print(f"❌ SSM agent not running on {instance_id}")
                return None
            
            # Run command
            response = self.ssm.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunPowerShellScript",
                Parameters={'commands': [command]},
                TimeoutSeconds=30
            )
            
            command_id = response['Command']['CommandId']
            print(f"✅ Command sent. Command ID: {command_id}")
            
            # Wait for command to complete
            time.sleep(5)
            
            # Get command output
            output = self.ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )
            
            print(f"Command Status: {output['Status']}")
            print(f"Output:\n{output.get('StandardOutputContent', 'No output')}")
            
            if output.get('StandardErrorContent'):
                print(f"Errors:\n{output['StandardErrorContent']}")
            
            return output
            
        except Exception as e:
            print(f"❌ SSM command failed: {e}")
            return None
    
    def create_scheduled_shutdown(self, instance_ids, shutdown_time):
        """Schedule automatic shutdown for Windows instances"""
        # This is a simplified example
        # In production, you'd use EventBridge rules or Lambda
        
        print(f"Scheduling shutdown for {len(instance_ids)} instances at {shutdown_time}")
        
        for instance_id in instance_ids:
            # Example PowerShell command to schedule shutdown
            command = f'schtasks /create /tn "AutoShutdown" /tr "shutdown /s /f" /sc once /st {shutdown_time} /ru SYSTEM'
            
            result = self.run_ssm_command_on_windows(instance_id, command)
            if result and result['Status'] == 'Success':
                print(f"✅ Scheduled shutdown for {instance_id}")
            else:
                print(f"❌ Failed to schedule shutdown for {instance_id}")
    
    def get_windows_performance_metrics(self, instance_id, duration_hours=24):
        """Get CloudWatch metrics for Windows instance"""
        cloudwatch = self.session.client('cloudwatch')
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=duration_hours)
        
        metrics_to_get = [
            {'Name': 'CPUUtilization', 'Unit': 'Percent'},
            {'Name': 'MemoryAvailable', 'Unit': 'Bytes'},
            {'Name': 'DiskReadBytes', 'Unit': 'Bytes'},
            {'Name': 'DiskWriteBytes', 'Unit': 'Bytes'},
            {'Name': 'NetworkIn', 'Unit': 'Bytes'},
            {'Name': 'NetworkOut', 'Unit': 'Bytes'}
        ]
        
        all_metrics = {}
        
        for metric in metrics_to_get:
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName=metric['Name'],
                    Dimensions=[
                        {'Name': 'InstanceId', 'Value': instance_id}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,  # 5 minutes
                    Statistics=['Average'],
                    Unit=metric['Unit']
                )
                
                datapoints = response['Datapoints']
                if datapoints:
                    # Sort by time and get latest
                    datapoints.sort(key=lambda x: x['Timestamp'])
                    latest = datapoints[-1]
                    
                    # Convert bytes to MB for readability
                    value = latest['Average']
                    if 'Bytes' in metric['Unit']:
                        value = value / (1024 * 1024)  # Convert to MB
                        unit = 'MB'
                    else:
                        unit = metric['Unit']
                    
                    all_metrics[metric['Name']] = {
                        'value': round(value, 2),
                        'unit': unit,
                        'timestamp': latest['Timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
            except Exception as e:
                print(f"⚠️  Could not get metric {metric['Name']}: {e}")
        
        return all_metrics

# Example usage
ec2_manager = WindowsEC2Manager()

# List Windows instances
windows_instances = ec2_manager.manage_windows_instances()

if windows_instances:
    # Get metrics for first Windows instance
    first_instance = windows_instances[0]['InstanceId']
    metrics = ec2_manager.get_windows_performance_metrics(first_instance, 1)
    
    print(f"\nPerformance metrics for {first_instance}:")
    for metric_name, data in metrics.items():
        print(f"  {metric_name}: {data['value']} {data['unit']} at {data['timestamp']}")
