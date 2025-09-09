"""
Resource path helper for PyInstaller compatibility.
Ensures file paths work correctly in both development and packaged .exe environments.
"""

import sys
import os
from pathlib import Path

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    
    Args:
        relative_path (str): Relative path to the resource file
        
    Returns:
        str: Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Development environment - use script directory
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_app_data_dir():
    """
    Get application data directory for storing logs and config files.
    Creates directory if it doesn't exist.
    
    Returns:
        str: Path to application data directory
    """
    if os.name == 'nt':  # Windows
        app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
        app_dir = os.path.join(app_data, 'FlutterDevSetup')
    else:
        app_dir = os.path.expanduser('~/.flutterdevsetup')
    
    # Create directory if it doesn't exist
    Path(app_dir).mkdir(parents=True, exist_ok=True)
    return app_dir

def get_temp_dir():
    """
    Get temporary directory for downloads and extractions.
    
    Returns:
        str: Path to temporary directory
    """
    import tempfile
    return tempfile.gettempdir()
