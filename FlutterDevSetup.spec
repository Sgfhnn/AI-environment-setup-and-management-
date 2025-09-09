# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Firs-windsurf-project\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('README.md', '.')],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.scrolledtext', 'threading', 'subprocess', 'urllib.request', 'tempfile', 'shutil', 'json', 'pathlib', 'ctypes', 'datetime', 'zipfile', 'tarfile', 'logging', 're', 'requests', 'winreg', 'platform', 'system_scanner', 'installer_manager', 'logger', 'resource_path'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'PIL', 'cv2', 'tensorflow', 'torch'],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('O', None, 'OPTION'), ('O', None, 'OPTION')],
    name='FlutterDevSetup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    uac_admin=True,
)
