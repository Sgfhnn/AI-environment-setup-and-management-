# Flutter Dev Setup Tool - Build Instructions

## Building Windows .exe with PyInstaller

### Prerequisites
1. Python 3.8 or higher
2. All dependencies installed: `pip install -r requirements.txt`

### Quick Build
```bash
# Method 1: Use the build script
python build_exe.py

# Method 2: Use PyInstaller directly with spec file
pyinstaller FlutterDevSetup.spec

# Method 3: Setup and build in one go
python setup_for_exe.py
python build_exe.py
```

### Output
- Executable will be created in: `dist/FlutterDevSetup.exe`
- Build files in: `build/` directory
- Logs during build process will show any issues

### Features Included in .exe
✅ Single file executable (no external dependencies)
✅ Windows UAC admin privilege requests
✅ All GUI functionality preserved
✅ Proper resource path handling for packaged environment
✅ Application data directory for logs (in %APPDATA%/FlutterDevSetup/)
✅ Version information embedded in executable
✅ Optimized size with unnecessary modules excluded

### Testing the .exe
1. Run `dist/FlutterDevSetup.exe`
2. Test admin privilege elevation (UAC prompt should appear)
3. Verify all GUI functions work correctly
4. Check that logs are created in `%APPDATA%/FlutterDevSetup/logs/`

### Troubleshooting
- If build fails, check Python version and dependencies
- For import errors, verify all custom modules are in hiddenimports
- For path issues, ensure resource_path.py is being used correctly
- For UAC issues, test on Windows 10/11 with standard user account
