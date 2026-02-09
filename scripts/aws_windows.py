# scripts\aws_windows.py
import boto3
from botocore.exceptions import ClientError, ProfileNotFound
import os

class WindowsAWSManager:
    def __init__(self, profile_name='automation', region='us-east-1'):
        """Initialize AWS session with Windows considerations"""
        try:
            # On Windows, we can use named profiles
            self.session = boto3.Session(
                profile_name=profile_name,
                region_name=region
            )
            self.ec2 = self.session.client('ec2')
            self.s3 = self.session.client('s3')
            print(f"✅ AWS session created with profile: {profile_name}")
        except ProfileNotFound:
            print("❌ AWS profile not found. Please run 'aws configure --profile automation'")
            raise
    
    def test_windows_connection(self):
        """Test AWS connection with Windows-specific checks"""
        try:
            # Test with a simple call
            response = self.ec2.describe_regions()
            regions = [region['RegionName'] for region in response['Regions']]
            
            print(f"✅ Connected to AWS. Available regions: {len(regions)}")
            
            # Check if we're running on Windows
            if os.name == 'nt':
                print("🌐 Running on Windows - using Windows-specific configurations")
                
                # Windows-specific: Check for proxy settings
                proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
                if proxy:
                    print(f"⚠️  Proxy detected: {proxy}. This may affect AWS connectivity.")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'AuthFailure':
                print("❌ Authentication failed. Check your AWS credentials.")
                print("   Run: aws configure --profile automation")
            elif error_code == 'RequestExpired':
                print("❌ AWS credentials have expired.")
            elif error_code == 'AccessDenied':
                print("❌ Access denied. Check IAM permissions.")
            else:
                print(f"❌ AWS connection failed: {e}")
            
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def list_ec2_instances_windows(self):
        """List EC2 instances with Windows-friendly output"""
        try:
            response = self.ec2.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    # Get Windows-specific tags if available
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    
                    instance_info = {
                        'InstanceId': instance['InstanceId'],
                        'InstanceType': instance['InstanceType'],
                        'State': instance['State']['Name'],
                        'LaunchTime': instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S'),
                        'Platform': instance.get('Platform', 'Linux/Unix'),
                        'PublicIp': instance.get('PublicIpAddress', 'N/A'),
                        'PrivateIp': instance.get('PrivateIpAddress', 'N/A'),
                        'Tags': tags,
                        'IsWindows': instance.get('Platform', '').lower() == 'windows'
                    }
                    instances.append(instance_info)
            
            return instances
            
        except ClientError as e:
            print(f"❌ Error listing instances: {e}")
            return []
    
    def create_windows_ec2_instance(self):
        """Example: Create a Windows EC2 instance"""
        print("Note: Creating actual instances will incur costs.")
        print("This is example code - modify before use.")
        
        # Example parameters for Windows Server
        windows_ami = 'ami-0ff8a91507f77f867'  # Windows Server 2019 in us-east-1
        # Find current AMI IDs: https://cloud-images.ubuntu.com/locator/ec2/
        
        return None  # Safety - remove this line when ready to use
        
        try:
            response = self.ec2.run_instances(
                ImageId=windows_ami,
                InstanceType='t2.micro',
                MinCount=1,
                MaxCount=1,
                KeyName='your-key-pair',  # Create in AWS Console first
                SecurityGroupIds=['sg-xxxxxxx'],  # Your security group
                SubnetId='subnet-xxxxxxx',  # Your subnet
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': 'Windows-Test-Server'},
                            {'Key': 'Environment', 'Value': 'Test'},
                            {'Key': 'CreatedBy', 'Value': 'Python-Automation'}
                        ]
                    }
                ],
                UserData='''<powershell>
                    # PowerShell script to run on first boot
                    Write-Host "Windows instance configured by Python automation"
                </powershell>'''
            )
            
            instance_id = response['Instances'][0]['InstanceId']
            print(f"✅ Created Windows instance: {instance_id}")
            return instance_id
            
        except ClientError as e:
            print(f"❌ Failed to create instance: {e}")
            return None

if __name__ == "__main__":
    # Test AWS connection
    aws = WindowsAWSManager()
    
    if aws.test_windows_connection():
        instances = aws.list_ec2_instances_windows()
        
        print(f"\nFound {len(instances)} EC2 instances:")
        print("=" * 80)
        
        for instance in instances:
            platform = "🪟 Windows" if instance['IsWindows'] else "🐧 Linux/Unix"
            print(f"{platform} | {instance['InstanceId']:20} | {instance['InstanceType']:12} | {instance['State']:12}")
            if instance['Tags'].get('Name'):
                print(f"   Name: {instance['Tags']['Name']}")

