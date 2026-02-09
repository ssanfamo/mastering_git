# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['service_wrapper.py'],
    pathex=[],
    binaries=[],
    datas=[('monitor_config.yaml', '.'), ('templates', 'templates')],
    hiddenimports=['flask', 'psutil', 'pywin32', 'yaml', 'schedule', 'slack_sdk', 'pymsteams'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
