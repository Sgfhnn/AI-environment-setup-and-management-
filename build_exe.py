"""
PyInstaller build script for Flutter Development Environment Setup Tool
Creates a single Windows .exe file with all dependencies bundled.
"""

import PyInstaller.__main__
import os
import sys
from pathlib import Path

def build_exe():
    """Build the executable using PyInstaller with optimized settings."""
    
    # Get the current directory
    current_dir = Path(__file__).parent
    
    # Define paths
    main_script = current_dir / "main.py"
    icon_path = current_dir / "app_icon.ico"  # Optional icon file
    
    # PyInstaller arguments
    args = [
        str(main_script),
        '--onefile',  # Create single executable
        '--windowed',  # No console window (GUI app)
        '--name=FlutterDevSetup',
        '--distpath=dist',
        '--workpath=build',
        '--specpath=.',
        
        # Include all Python modules
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.scrolledtext',
        '--hidden-import=threading',
        '--hidden-import=subprocess',
        '--hidden-import=urllib.request',
        '--hidden-import=tempfile',
        '--hidden-import=shutil',
        '--hidden-import=json',
        '--hidden-import=pathlib',
        '--hidden-import=ctypes',
        '--hidden-import=datetime',
        '--hidden-import=zipfile',
        '--hidden-import=tarfile',
        '--hidden-import=logging',
        '--hidden-import=re',
        '--hidden-import=requests',
        '--hidden-import=winreg',
        '--hidden-import=platform',
        
        # Include custom modules
        '--hidden-import=system_scanner',
        '--hidden-import=installer_manager',
        '--hidden-import=logger',
        '--hidden-import=resource_path',
        
        # Add data files if needed
        '--add-data=README.md;.',
        
        # Windows specific options
        '--uac-admin',  # Request admin privileges
        '--version-file=version_info.txt',  # Version information
        
        # Optimization
        '--optimize=2',
        '--strip',
        '--clean',
        
        # Exclude unnecessary modules to reduce size
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=PIL',
        '--exclude-module=cv2',
        '--exclude-module=tensorflow',
        '--exclude-module=torch',
    ]
    
    # Add icon if it exists
    if icon_path.exists():
        args.extend(['--icon', str(icon_path)])
    
    print("Building executable with PyInstaller...")
    print(f"Main script: {main_script}")
    print("Arguments:", ' '.join(args))
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print("\nBuild completed!")
    print(f"Executable location: {current_dir / 'dist' / 'FlutterDevSetup.exe'}")

if __name__ == "__main__":
    build_exe()
