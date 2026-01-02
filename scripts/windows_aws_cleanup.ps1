# scripts\windows_aws_cleanup.ps1
<#
.SYNOPSIS
Clean up AWS resources created during testing on Windows

.DESCRIPTION
This script helps clean up AWS resources to avoid unexpected charges.
Run with -WhatIf first to see what would be deleted.

.PARAMETER ProfileName
AWS profile to use (default: automation)

.PARAMETER WhatIf
Show what would be deleted without actually deleting

.EXAMPLE
.\windows_aws_cleanup.ps1 -WhatIf
.\windows_aws_cleanup.ps1
#>

param(
    [string]$ProfileName = "automation",
    [switch]$WhatIf
)

# Import AWS Tools if available
try {
    Import-Module AWSPowerShell -ErrorAction Stop
} catch {
    Write-Host "AWS Tools for PowerShell not installed." -ForegroundColor Yellow
    Write-Host "Install with: Install-Module -Name AWSPowerShell -Force" -ForegroundColor Yellow
    exit 1
}

# Set AWS profile
Set-AWSCredential -ProfileName $ProfileName

Write-Host "AWS Cleanup Script for Windows" -ForegroundColor Cyan
Write-Host "Profile: $ProfileName" -ForegroundColor Cyan
Write-Host "WhatIf Mode: $($WhatIf.IsPresent)" -ForegroundColor Cyan
Write-Host "=" * 80

if ($WhatIf) {
    Write-Host "RUNNING IN WHATIF MODE - Nothing will be deleted" -ForegroundColor Yellow
}

# 1. Find and stop test EC2 instances
Write-Host "`n1. Checking EC2 instances..." -ForegroundColor Green

$instances = Get-EC2Instance -Filter @(
    @{Name="tag:Environment";Values="Test"},
    @{Name="tag:CreatedBy";Values="Python-Automation"}
)

if ($instances.Instances) {
    foreach ($instance in $instances.Instances) {
        $instanceId = $instance.InstanceId
        $name = ($instance.Tags | Where-Object {$_.Key -eq "Name"}).Value
        
        Write-Host "   Found: $instanceId ($name)" -ForegroundColor White
        
        if (-not $WhatIf) {
            if ($instance.State.Name -eq "running") {
                Write-Host "   Stopping instance..." -ForegroundColor Yellow
                Stop-EC2Instance -InstanceId $instanceId -Force
            }
            
            # Optionally terminate	
            # Write-Host "   Terminating instance..." -ForegroundColor Red
            # Remove-EC2Instance -InstanceId $instanceId -Force
        }
    }
} else {
    Write-Host "   No test instances found" -ForegroundColor Gray
}

# 2. Clean up old snapshots
Write-Host "`n2. Checking old snapshots..." -ForegroundColor Green

$oldDate = (Get-Date).AddDays(-7)  # Snapshots older than 7 days
$snapshots = Get-EC2Snapshot -Filter @(
    @{Name="tag:CreatedBy";Values="Automation"}
)

foreach ($snapshot in $snapshots) {
    if ($snapshot.StartTime -lt $oldDate) {
        Write-Host "   Found old snapshot: $($snapshot.SnapshotId) from $($snapshot.StartTime)" -ForegroundColor White
        
        if (-not $WhatIf) {
            Write-Host "   Deleting snapshot..." -ForegroundColor Red
            Remove-EC2Snapshot -SnapshotId $snapshot.SnapshotId -Force
        }
    }
}

# 3. Clean up S3 test buckets
Write-Host "`n3. Checking S3 test buckets..." -ForegroundColor Green

$buckets = Get-S3Bucket | Where-Object {
    $_.BucketName -like "*-test-*" -or 
    $_.BucketName -like "test-*" -or
    ($_.Tags | Where-Object {$_.Key -eq "Environment" -and $_.Value -eq "Test"})
}

foreach ($bucket in $buckets) {
    Write-Host "   Found test bucket: $($bucket.BucketName)" -ForegroundColor White
    
    if (-not $WhatIf) {
        # Empty bucket first
        Write-Host "   Emptying bucket..." -ForegroundColor Yellow
        Get-S3Object -BucketName $bucket.BucketName | Remove-S3Object -Force
        
        # Then delete bucket
        Write-Host "   Deleting bucket..." -ForegroundColor Red
        Remove-S3Bucket -BucketName $bucket.BucketName -Force
    }
}

Write-Host "`n" + ("=" * 80) -ForegroundColor Cyan

if ($WhatIf) {
    Write-Host "WHATIF COMPLETE" -ForegroundColor Yellow
    Write-Host "Run without -WhatIf to actually delete resources" -ForegroundColor Yellow
} else {
    Write-Host "CLEANUP COMPLETE" -ForegroundColor Green
    Write-Host "Resources have been cleaned up" -ForegroundColor Green
}

Write-Host "`nRemember to check AWS Console for any remaining resources" -ForegroundColor Cyan
