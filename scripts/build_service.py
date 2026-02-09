# build_service.py
import sys
import os
from pathlib import Path

def create_spec_file():
    """Create PyInstaller spec file for the service"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['service_wrapper.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('monitor_config.yaml', '.'),
        ('templates', 'templates'),
    ],
    hiddenimports=[
        'flask',
        'psutil',
        'pywin32',
        'yaml',
        'schedule',
        'slack_sdk',
        'pymsteams',
        'jinja2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SystemMonitorService',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Run as background service (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
'''
    
    with open('system_monitor.spec', 'w') as f:
        f.write(spec_content)
    
    print("Created system_monitor.spec")

def build_executable():
    """Build the executable using PyInstaller"""
    import PyInstaller.__main__
    
    args = [
        'service_wrapper.py',
        '--name=SystemMonitorService',
        '--onefile',
        '--windowed',  # No console window
        '--add-data=monitor_config.yaml:.',
        '--add-data=templates;templates',
        '--hidden-import=flask',
        '--hidden-import=psutil',
        '--hidden-import=pywin32',
        '--hidden-import=yaml',
        '--hidden-import=schedule',
        '--hidden-import=slack_sdk',
        '--hidden-import=pymsteams',
        '--clean',
        '--distpath=dist',
        '--workpath=build',
    ]
    
    print(f"Running PyInstaller with args: {args}")
    PyInstaller.__main__.run(args)
    
    print("\nBuild complete! Executable created in dist/ folder")
    print("To install as service:")
    print("1. Run as Administrator")
    print("2. Use NSSM: nssm.exe install SystemMonitorService dist\\SystemMonitorService.exe")
    print("3. nssm.exe start SystemMonitorService")

if __name__ == '__main__':
    print("Building Windows Service Executable")
    print("=" * 50)
    
    # Install PyInstaller if needed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        os.system(f"{sys.executable} -m pip install pyinstaller")
    
    # Create icon if doesn't exist
    icon_path = Path('icon.ico')
    if not icon_path.exists():
        print("\nNote: Create an icon.ico file for better service appearance")
    
    build_executable()