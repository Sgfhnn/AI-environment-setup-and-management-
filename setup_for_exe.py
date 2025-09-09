"""
Setup script to prepare the Flutter Dev Setup Tool for PyInstaller packaging.
This script ensures all dependencies are properly configured for .exe creation.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Ensure Python version is compatible."""
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required")
        return False
    print(f"OK Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_dependencies():
    """Install required dependencies for building exe."""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("OK Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        return False

def verify_modules():
    """Verify all required modules can be imported."""
    modules = [
        'tkinter', 'requests', 'PyInstaller',
        'system_scanner', 'installer_manager', 'logger'
    ]
    
    print("Verifying module imports...")
    for module in modules:
        try:
            __import__(module)
            print(f"OK {module}")
        except ImportError as e:
            print(f"ERROR {module}: {e}")
            return False
    return True

def create_build_directories():
    """Create necessary build directories."""
    dirs = ['build', 'dist']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"OK Created {dir_name}/ directory")

def main():
    """Main setup function."""
    print("=== Flutter Dev Setup Tool - PyInstaller Preparation ===\n")
    
    if not check_python_version():
        return False
    
    if not install_dependencies():
        return False
    
    if not verify_modules():
        return False
    
    create_build_directories()
    
    print("\nOK Setup completed successfully!")
    print("\nNext steps:")
    print("1. Run: python build_exe.py")
    print("2. Or run: pyinstaller FlutterDevSetup.spec")
    print("3. Find executable in: dist/FlutterDevSetup.exe")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
