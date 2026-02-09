# scripts\aws_security_windows.py
import boto3
import json
from datetime import datetime

class WindowsAWSSecurity:
    def __init__(self, profile_name='automation'):
        self.session = boto3.Session(profile_name=profile_name)
        self.iam = self.session.client('iam')
        self.securityhub = self.session.client('securityhub')
        self.guardduty = self.session.client('guardduty')
    
    def audit_iam_users(self):
        """Audit IAM users for security best practices"""
        try:
            users = self.iam.list_users()
            findings = []
            
            for user in users['Users']:
                user_name = user['UserName']
                user_findings = {
                    'UserName': user_name,
                    'CreateDate': user['CreateDate'].strftime('%Y-%m-%d'),
                    'Issues': []
                }
                
                # Check for MFA
                mfa_devices = self.iam.list_mfa_devices(UserName=user_name)
                if not mfa_devices['MFADevices']:
                    user_findings['Issues'].append('MFA_NOT_ENABLED')
                
                # Check access keys
                access_keys = self.iam.list_access_keys(UserName=user_name)
                for key in access_keys['AccessKeyMetadata']:
                    key_age = (datetime.now(key['CreateDate'].tzinfo) - key['CreateDate']).days
                    if key_age > 90:  # Keys older than 90 days
                        user_findings['Issues'].append(f'ACCESS_KEY_OLD_{key_age}_DAYS')
                
                # Check for inline policies (generally not recommended)
                inline_policies = self.iam.list_user_policies(UserName=user_name)
                if inline_policies['PolicyNames']:
                    user_findings['Issues'].append('HAS_INLINE_POLICIES')
                
                if user_findings['Issues']:
                    findings.append(user_findings)
            
            return findings
            
        except Exception as e:
            print(f"❌ IAM audit failed: {e}")
            return []
    
    def check_security_hub_findings(self):
        """Check AWS Security Hub findings"""
        try:
            findings = []
            
            # Get recent findings
            response = self.securityhub.get_findings(
                Filters={
                    'RecordState': [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}],
                    'SeverityLabel': [
                        {'Value': 'CRITICAL', 'Comparison': 'EQUALS'},
                        {'Value': 'HIGH', 'Comparison': 'EQUALS'}
                    ]
                },
                MaxResults=10
            )
            
            for finding in response['Findings']:
                findings.append({
                    'Title': finding.get('Title', 'N/A'),
                    'Severity': finding.get('Severity', {}).get('Label', 'N/A'),
                    'ResourceType': finding.get('Resources', [{}])[0].get('Type', 'N/A'),
                    'Description': finding.get('Description', 'N/A')[:200] + '...',
                    'FirstObserved': finding.get('FirstObservedAt', 'N/A')
                })
            
            return findings
            
        except Exception as e:
            print(f"⚠️  Security Hub not available or not configured: {e}")
            return []
    
    def generate_security_report(self):
        """Generate comprehensive security report"""
        print("🔒 Running AWS Security Audit...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'iam_audit': self.audit_iam_users(),
            'security_hub_findings': self.check_security_hub_findings(),
            'summary': {}
        }
        
        # Generate summary
        report['summary']['users_with_issues'] = len(report['iam_audit'])
        report['summary']['critical_findings'] = len([
            f for f in report['security_hub_findings']
            if f['Severity'] in ['CRITICAL', 'HIGH']
        ])
        
        # Save report
        import json
        report_file = Path("C:/Career_Transition/reports/security/aws_security_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Security report saved to: {report_file}")
        
        # Print summary
        print(f"\n📋 Security Report Summary:")
        print(f"   Users needing attention: {report['summary']['users_with_issues']}")
        print(f"   Critical/High findings: {report['summary']['critical_findings']}")
        
        if report['iam_audit']:
            print("\n👥 IAM Users with Issues:")
            for user in report['iam_audit']:
                print(f"   {user['UserName']}: {', '.join(user['Issues'])}")
        
        return report_file

# Run security audit
security = WindowsAWSSecurity()
report_file = security.generate_security_report()
