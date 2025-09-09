# Flutter Development Environment Setup Tool

A **complete Windows executable** that automatically scans, downloads, and installs Flutter development tools with a user-friendly GUI. No Python installation required!

## 🚀 Features

- **System Scanning**: Automatically detects installed Flutter, Dart, Android Studio, and Java JDK
- **One-Click Installation**: Downloads and installs missing development tools automatically
- **Environment Configuration**: Configures PATH and environment variables (JAVA_HOME, ANDROID_HOME)
- **UAC Integration**: Handles administrator privileges with Windows UAC prompts
- **Real-time Progress**: Shows installation progress with detailed status updates
- **Rollback Functionality**: Can undo installation changes if something goes wrong
- **Comprehensive Logging**: Detailed logs for troubleshooting and audit trail
- **Modern GUI**: Clean, intuitive interface
- **Single Executable**: No installation required - just download and run!

## 📋 System Requirements

- **Operating System**: Windows 10 or later (64-bit recommended)
- **Permissions**: Administrator privileges (required for installing software)
- **Internet**: Active connection for downloading development tools
- **Disk Space**: Minimum 8GB free space on C: drive
- **Memory**: 4GB RAM minimum (8GB recommended)

## 📥 How to Use

### Quick Start (Recommended)
1. **Download** the executable: [`FlutterDevSetup.exe`](dist/FlutterDevSetup.exe) (14.5 MB)
2. **Run** the downloaded file (double-click `FlutterDevSetup.exe`)
3. **Allow** administrator privileges when Windows UAC prompt appears
4. **Click "Scan System"** to detect installed/missing tools
5. **Click "Start Installation"** to install missing components
6. **Wait** for completion and restart your system

### Alternative: Run from Source
```bash
git clone https://github.com/Sgfhnn/AI-environment-setup-and-management-.git
cd AI-environment-setup-and-management-
python main.py
```

## 📖 Detailed Usage Guide

### 1. Launch the Application
- **Executable**: Double-click `FlutterDevSetup.exe` (no installation needed) Or 
- **From Source**: if You clone it from the GitHub repo git clone https://github.com/Sgfhnn/AI-environment-setup-and-management-.git 
change the PATH to 
-cd AI-environment-setup-and-management-
then Run
python main.py
- The GUI will open showing the Flutter Development Environment Setup interface

### 2. Scan Your System
- Click **"Scan System"** to detect currently installed development tools
- The scan checks for:
  - Flutter SDK
  - Dart SDK (bundled with Flutter)
  - Android Studio
  - Java JDK
- Results are displayed in the status table with ✅/❌ indicators

### 3. Install Missing Tools
- If missing tools are detected, the **"Start Installation"** button becomes enabled
- Click **"Start Installation"** to begin automatic installation
- **UAC Prompt**: Windows will ask for administrator privileges - click "Yes"
- **Progress Tracking**: Watch real-time progress and status updates
- **Completion**: System will notify when installation is complete

### 4. View Logs
- Click **"View Logs"** to see detailed installation logs
- Logs include system information, scan results, and installation steps
- Useful for troubleshooting if issues occur

### 5. Rollback (If Needed)
- If installation fails or causes issues, click **"Rollback Changes"**
- This will attempt to undo all changes made during installation
- Restores previous system state including PATH and environment variables

## 🔧 What Gets Installed

### Flutter SDK
- **Location**: `C:\flutter`
- **PATH Addition**: `C:\flutter\bin`
- **Includes**: Dart SDK (bundled)

### Android Studio
- **Location**: `C:\Program Files\Android\Android Studio`
- **Environment Variables**: 
  - `ANDROID_HOME` → `%USERPROFILE%\AppData\Local\Android\Sdk`
  - `ANDROID_SDK_ROOT` → `%USERPROFILE%\AppData\Local\Android\Sdk`
- **PATH Addition**: Android SDK platform-tools

### Java JDK
- **Location**: `C:\Program Files\Java\jdk-17`
- **Environment Variable**: `JAVA_HOME` → JDK installation path
- **PATH Addition**: `%JAVA_HOME%\bin`

## 🚨 Troubleshooting

### Common Issues

#### "Administrator privileges required"
- **Solution**: Right-click `main.py` → "Run as administrator"
- **Alternative**: Accept UAC prompt when it appears

#### "Download failed" or "Network error"
- **Check**: Internet connection is active
- **Check**: Firewall/antivirus isn't blocking downloads
- **Try**: Running scan again after network issues are resolved

#### "Installation failed" 
- **Check Logs**: Click "View Logs" for detailed error information
- **Disk Space**: Ensure at least 8GB free space on C: drive
- **Try Rollback**: Use "Rollback Changes" to undo partial installation
- **Manual Cleanup**: Remove partially installed tools manually if needed

#### "Flutter doctor shows issues"
- **Normal**: Some warnings are expected on first install
- **Android Licenses**: Run `flutter doctor --android-licenses` and accept all
- **IDE Setup**: Configure Android Studio Flutter plugin manually if needed

### Log Locations
- **Application Logs**: `%APPDATA%\FlutterDevSetup\logs\`
- **Rollback Data**: Temporary directory (cleaned up automatically)

### Getting Help
1. **Check Logs**: Always check the application logs first
2. **System Scan**: Run a new system scan after resolving issues
3. **Clean Install**: Use rollback feature and try installation again
4. **Manual Verification**: Verify tools work by running commands:
   ```bash
   flutter --version
   dart --version  
   java -version
   ```

## 🔒 Security & Safety

### Administrator Privileges
- **Required For**: Installing software and modifying system environment variables
- **UAC Integration**: Uses Windows UAC for secure privilege elevation
- **Scope**: Only requests admin rights when actually needed

### Rollback Protection
- **Automatic Backup**: Existing installations are backed up before replacement
- **Change Tracking**: All system modifications are logged for rollback
- **Safe Recovery**: Rollback feature can restore previous system state

### Download Security
- **Official Sources**: Downloads only from official vendor URLs
- **HTTPS**: All downloads use secure HTTPS connections
- **Verification**: Installation files are verified after download

## 📁 Project Structure

```
AI-environment-setup-and-management-/
├── dist/
│   └── FlutterDevSetup.exe    # Ready-to-use Windows executable (14.5 MB)
├── main.py                    # Main GUI application
├── system_scanner.py          # System scanning functionality  
├── installer_manager.py       # Installation and rollback logic
├── logger.py                  # Logging system
├── resource_path.py           # PyInstaller resource path handling
├── build_exe.py               # Build script for creating executable
├── FlutterDevSetup.spec       # PyInstaller specification file
├── version_info.txt           # Windows executable metadata
├── BUILD_INSTRUCTIONS.md     # Instructions for building from source
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔄 Development Notes

### Code Architecture
- **Modular Design**: Separated concerns across multiple files
- **Thread Safety**: GUI operations use proper threading for responsiveness
- **Error Handling**: Comprehensive exception handling and logging
- **Windows Integration**: Native Windows APIs for registry and UAC

### Key Classes
- **`FlutterDevSetupGUI`**: Main application interface and control logic
- **`SystemScanner`**: Detects installed development tools and versions
- **`InstallerManager`**: Handles downloads, installations, and rollbacks
- **`Logger`**: Centralized logging with multiple output levels

### Future Enhancements (Phase 2)
- Multi-stack support (React Native, Xamarin, etc.)
- AI-powered recommendations
- Team management features
- Cloud synchronization
- Custom installation paths

## 📄 License

This project is created as a Phase 1 MVP for Flutter development environment setup on Windows also issued with [MIT License](LICENSE).

## 🤝 Contributing

This is a Phase 1 MVP focusing specifically on Windows Flutter development setup. Future phases will expand functionality and platform support Any One who Wanna Contribute to This Open source Project You're WELCOME
