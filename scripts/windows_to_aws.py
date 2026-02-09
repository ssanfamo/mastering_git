# scripts\windows_to_aws.py
import boto3
from pathlib import Path
import os
from datetime import datetime

class WindowsAWSTransfer:
    def __init__(self, profile_name='automation'):
        self.session = boto3.Session(profile_name=profile_name)
        self.s3 = self.session.client('s3')
    
    def upload_windows_file_to_s3(self, local_path, bucket_name, s3_key=None):
        """Upload file from Windows to S3"""
        local_path = Path(local_path)
        
        if not local_path.exists():
            print(f"❌ File does not exist: {local_path}")
            return False
        
        if not s3_key:
            # Create S3 key with Windows path information
            s3_key = f"windows-uploads/{datetime.now().strftime('%Y/%m/%d')}/{local_path.name}"
        
        try:
            # For large files, consider multipart upload
            file_size = local_path.stat().st_size
            
            if file_size > 100 * 1024 * 1024:  # 100MB
                print(f"📦 Large file detected ({file_size/1024/1024:.2f}MB), using multipart upload")
                self._multipart_upload(local_path, bucket_name, s3_key)
            else:
                print(f"⬆️  Uploading {local_path.name} ({file_size/1024:.2f}KB) to S3...")
                self.s3.upload_file(str(local_path), bucket_name, s3_key)
            
            # Generate URL (valid for 1 hour)
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': s3_key},
                ExpiresIn=3600
            )
            
            print(f"✅ Uploaded to: s3://{bucket_name}/{s3_key}")
            print(f"📎 Temporary URL: {url}")
            
            return True
            
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return False
    
    def _multipart_upload(self, file_path, bucket, key):
        """Handle multipart upload for large files"""
        from boto3.s3.transfer import TransferConfig
        
        config = TransferConfig(
            multipart_threshold=1024 * 25,  # 25MB
            max_concurrency=10,
            multipart_chunksize=1024 * 25,  # 25MB
            use_threads=True
        )
        
        self.s3.upload_file(
            str(file_path), bucket, key,
            Config=config,
            Callback=self._upload_progress_callback(file_path)
        )
    
    def _upload_progress_callback(self, file_path):
        """Progress callback for uploads"""
        file_size = file_path.stat().st_size
        
        def callback(bytes_transferred):
            percent = (bytes_transferred / file_size) * 100
            print(f"  Progress: {percent:.1f}% ({bytes_transferred/1024/1024:.1f}MB/{file_size/1024/1024:.1f}MB)", end='\r')
        
        return callback
    
    def download_from_s3_to_windows(self, bucket_name, s3_key, local_dir):
        """Download file from S3 to Windows"""
        local_dir = Path(local_dir)
        local_dir.mkdir(parents=True, exist_ok=True)
        
        local_path = local_dir / Path(s3_key).name
        
        try:
            print(f"⬇️  Downloading s3://{bucket_name}/{s3_key} to {local_path}...")
            
            self.s3.download_file(
                bucket_name, s3_key, str(local_path)
            )
            
            print(f"✅ Downloaded: {local_path}")
            return str(local_path)
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def sync_windows_dir_to_s3(self, local_dir, bucket_name, s3_prefix):
        """Sync Windows directory to S3 (like rsync)"""
        local_dir = Path(local_dir)
        
        if not local_dir.exists() or not local_dir.is_dir():
            print(f"❌ Directory does not exist: {local_dir}")
            return False
        
        uploaded_count = 0
        
        for file_path in local_dir.rglob('*'):
            if file_path.is_file():
                # Preserve directory structure
                relative_path = file_path.relative_to(local_dir)
                s3_key = f"{s3_prefix}/{relative_path}".replace('\\', '/')  # Windows to S3 path
                
                if self.upload_windows_file_to_s3(file_path, bucket_name, s3_key):
                    uploaded_count += 1
        
        print(f"✅ Synced {uploaded_count} files to S3")
        return uploaded_count

# Example usage
transfer = WindowsAWSTransfer()

# Upload a file
# transfer.upload_windows_file_to_s3(
#     r"C:\Career_Transition\learning\journal.md",
#     "your-bucket-name",
#     "journals/windows-journal.md"
# )

# Sync a directory
# transfer.sync_windows_dir_to_s3(
#     r"C:\Career_Transition\scripts",
#     "your-bucket-name",
#     "automation-scripts/windows"
# )
