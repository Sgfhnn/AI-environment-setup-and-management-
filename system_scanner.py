import os
import subprocess
import re
import winreg
from pathlib import Path
import json

class SystemScanner:
    """
    Scans Windows system for Flutter development tools and their configurations.
    Detects installation status, versions, and paths for Flutter, Dart, Android Studio, and Java JDK.
    Enhanced with PATH refresh detection and fallback directory checking.
    """
    
    def __init__(self, logger):
        self.logger = logger
        # Common installation paths for development tools on Windows
        self.common_paths = {
            'Flutter': [
                r'C:\flutter',
                r'C:\src\flutter',
                r'C:\flutter\bin\flutter',
                r'C:\tools\flutter',
                r'C\flutter\src\flutter',
                os.path.expanduser(r'~\flutter'),
                os.path.expanduser(r'~\AppData\Local\flutter'),
            ],
            'Android Studio': [
                r'C:\Program Files\Android\Android Studio',
                r'C:\Program Files (x86)\Android\Android Studio',
                os.path.expanduser(r'~\AppData\Local\Android\Sdk'),
                os.path.expanduser(r'~\AppData\Roaming\Android Studio'),
            ],
            'Java JDK': [
                r'C:\Program Files\Java',
                r'C:\Program Files (x86)\Java',
                r'C:\Program Files\OpenJDK',
                r'C:\Program Files\Eclipse Adoptium',
                r'C:\Program Files\Microsoft\jdk',
            ]
        }
    
    def scan_system(self):
        """
        Perform comprehensive system scan for all Flutter development tools.
        Returns a dictionary with detailed information about each tool's status.
        """
        self.logger.log("Starting comprehensive system scan...")
        
        scan_results = {}
        
        # Scan each required development tool
        tools_to_scan = ['Flutter', 'Dart', 'Android Studio', 'Java JDK', 'Git']
        
        for tool in tools_to_scan:
            self.logger.log(f"Scanning for {tool}...")
            try:
                if tool == 'Flutter':
                    scan_resu
                    lts[tool] = self._scan_flutter()
                elif tool == 'Dart':
                    scan_results[tool] = self._scan_dart()
                elif tool == 'Android Studio':
                    scan_results[tool] = self._scan_android_studio()
                elif tool == 'Java JDK':
                    scan_results[tool] = self._scan_java_jdk()
                elif tool == 'Git':
                    scan_results[tool] = self._scan_git()
                
                status = "✅ Found" if scan_results[tool]['installed'] else "❌ Missing"
                self.logger.log(f"{tool} scan complete: {status}")
                
            except Exception as e:
                self.logger.log(f"Error scanning {tool}: {str(e)}", "ERROR")
                scan_results[tool] = {
                    'installed': False,
                    'version': 'Unknown',
                    'path': 'Error during scan',
                    'error': str(e)
                }
        
        self.logger.log("System scan completed")
        return scan_results
    
    def _scan_flutter(self):
        """
        Scan for Flutter SDK installation with enhanced detection.
        Checks PATH first, then fallback to default install directory.
        """
        flutter_info = {
            'installed': False,
            'version': 'Not Found',
            'path': 'Not Found',
            'dart_version': 'Not Found',
            'detection_method': 'none'  # 'path', 'fallback_directory', 'none'
        }
        
        self.logger.log("Scanning for Flutter SDK...")
        
        # Method 1: Check if flutter is available in PATH
        self.logger.log("Checking if 'flutter' is available in PATH...")
        try:
            # Use extended timeout for first-run setup (5-10 minutes)
            self.logger.log("Running 'flutter --version' (this may take several minutes on first run)...")
            result = subprocess.run(
                ['flutter', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=600,  # 10 minutes for first-run setup
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                output_text = result.stdout + result.stderr
                parsed_info = self._parse_flutter_output(output_text, 'PATH')
                if parsed_info and parsed_info['installed']:
                    flutter_info.update(parsed_info)
                    flutter_info['detection_method'] = 'path'
                    self.logger.log("✅ Flutter detected from PATH")
                    return flutter_info
            else:
                self.logger.log(f"Flutter PATH check failed with exit code: {result.returncode}")
                
        except subprocess.TimeoutExpired:
            self.logger.log("Flutter command timed out after 10 minutes - checking if first-run setup is in progress...")
            # Check if Flutter executable exists to determine if it's installed but doing first-run setup
            if self._check_flutter_executable_exists():
                flutter_info['installed'] = True
                flutter_info['version'] = 'First-run setup in progress'
                flutter_info['path'] = 'Found in PATH (first-run setup)'
                flutter_info['detection_method'] = 'path_first_run'
                self.logger.log("⏳ Flutter detected but first-run setup is in progress, please wait a few minutes", "WARNING")
                self.logger.log("Flutter is building tool snapshots and downloading dependencies on first use", "INFO")
                return flutter_info
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.log(f"Flutter not accessible from PATH: {str(e)}")
        
        # Method 2: Fallback to checking default install directory
        self.logger.log("Flutter not found in PATH, checking default install directory...")
        default_flutter_path = r'C:\flutter\bin\flutter.bat'
        
        if os.path.exists(default_flutter_path):
            self.logger.log(f"Found Flutter executable at: {default_flutter_path}")
            try:
                self.logger.log("Running Flutter from fallback directory (this may take several minutes on first run)...")
                result = subprocess.run(
                    [default_flutter_path, '--version'], 
                    capture_output=True, 
                    text=True, 
                    timeout=600  # 10 minutes for first-run setup
                )
                
                if result.returncode == 0:
                    output_text = result.stdout + result.stderr
                    parsed_info = self._parse_flutter_output(output_text, r'C:\flutter')
                    if parsed_info and parsed_info['installed']:
                        flutter_info.update(parsed_info)
                        flutter_info['detection_method'] = 'fallback_directory'
                        self.logger.log("✅ Flutter detected from fallback directory: C:\\flutter")
                        self.logger.log("⚠️ Flutter is installed but not accessible from PATH", "WARNING")
                        self.logger.log("PATH may need to be refreshed - restart terminal or system", "WARNING")
                        return flutter_info
                else:
                    self.logger.log(f"Flutter executable found but failed to run (exit code: {result.returncode})")
                    
            except subprocess.TimeoutExpired:
                self.logger.log("Flutter command timed out from fallback directory - first-run setup in progress...")
                flutter_info['installed'] = True
                flutter_info['version'] = 'First-run setup in progress'
                flutter_info['path'] = r'C:\flutter'
                flutter_info['detection_method'] = 'fallback_first_run'
                self.logger.log("⏳ Flutter detected but first-run setup is in progress, please wait a few minutes", "WARNING")
                self.logger.log("Flutter is building tool snapshots and downloading dependencies on first use", "INFO")
                return flutter_info
            except Exception as e:
                self.logger.log(f"Failed to run Flutter from fallback directory: {str(e)}")
        else:
            self.logger.log(f"Flutter executable not found at default location: {default_flutter_path}")
        
        # Method 3: Check other common installation directories
        self.logger.log("Checking other common Flutter installation directories...")
        other_paths = [
            r'C:\src\flutter\bin\flutter.bat',
            r'C:\tools\flutter\bin\flutter.bat',
            os.path.expanduser(r'~\flutter\bin\flutter.bat'),
            os.path.expanduser(r'~\AppData\Local\flutter\bin\flutter.bat'),
        ]
        
        for flutter_path in other_paths:
            if os.path.exists(flutter_path):
                self.logger.log(f"Found Flutter executable at: {flutter_path}")
                try:
                    result = subprocess.run(
                        [flutter_path, '--version'], 
                        capture_output=True, 
                        text=True, 
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        output_text = result.stdout + result.stderr
                        flutter_root = str(Path(flutter_path).parent.parent)
                        parsed_info = self._parse_flutter_output(output_text, flutter_root)
                        if parsed_info and parsed_info['installed']:
                            flutter_info.update(parsed_info)
                            flutter_info['detection_method'] = 'fallback_directory'
                            self.logger.log(f"✅ Flutter detected from directory: {flutter_root}")
                            self.logger.log("⚠️ Flutter is installed but not accessible from PATH", "WARNING")
                            self.logger.log("PATH may need to be refreshed - restart terminal or system", "WARNING")
                            return flutter_info
                            
                except subprocess.TimeoutExpired:
                    self.logger.log(f"Flutter command timed out from {flutter_path} - first-run setup in progress...")
                    flutter_root = str(Path(flutter_path).parent.parent)
                    flutter_info['installed'] = True
                    flutter_info['version'] = 'First-run setup in progress'
                    flutter_info['path'] = flutter_root
                    flutter_info['detection_method'] = 'fallback_first_run'
                    self.logger.log("⏳ Flutter detected but first-run setup is in progress, please wait a few minutes", "WARNING")
                    self.logger.log("Flutter is building tool snapshots and downloading dependencies on first use", "INFO")
                    return flutter_info
                except Exception as e:
                    self.logger.log(f"Failed to run Flutter from {flutter_path}: {str(e)}")
                    continue
        
        self.logger.log("❌ Flutter not found in PATH or any common install directories")
        flutter_info['detection_method'] = 'none'
        return flutter_info
    
    def _scan_dart(self):
        """
        Scan for Dart SDK installation with enhanced detection.
        Checks PATH, install directories, and Flutter bundled Dart.
        """
        dart_info = {
            'installed': False,
            'version': 'Not Found',
            'path': 'Not Found',
            'path_status': 'unknown'  # 'in_path', 'install_only', 'bundled', 'not_found'
        }
        
        self.logger.log("Scanning for Dart SDK...")
        
        # Method 1: Check if Dart is accessible from PATH (new process)
        path_success = self._check_tool_in_path('dart', 'Dart')
        if path_success:
            dart_info.update(path_success)
            dart_info['path_status'] = 'in_path'
            return dart_info
        
        # Method 2: Check if Dart is bundled with Flutter
        self.logger.log("Standalone Dart not found in PATH, checking Flutter bundled Dart...")
        
        bundled_success = self._check_dart_bundled_with_flutter()
        if bundled_success:
            dart_info.update(bundled_success)
            dart_info['path_status'] = 'bundled'
            return dart_info
        
        # Method 3: Check common installation directories as fallback
        self.logger.log("Dart not found with Flutter, checking install directories...")
        
        install_success = self._check_dart_in_directories()
        if install_success:
            dart_info.update(install_success)
            dart_info['path_status'] = 'install_only'
            self.logger.log("Dart found in install directory but not accessible from PATH", "WARNING")
            self.logger.log("PATH may need to be refreshed - restart terminal or system", "WARNING")
            return dart_info
        
        self.logger.log("Dart not found in any location")
        dart_info['path_status'] = 'not_found'
        return dart_info
    
    def _check_tool_in_path(self, command, tool_name):
        """
        Check if a tool is accessible from PATH using a new process.
        This ensures PATH updates are properly detected.
        """
        try:
            # Spawn new process to check PATH (ensures fresh environment)
            result = subprocess.run(
                [command, '--version'], 
                capture_output=True, 
                text=True, 
                timeout=30,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                output_text = result.stdout + result.stderr
                
                # Extract version information
                if tool_name.lower() == 'flutter':
                    return self._parse_flutter_output(output_text, 'PATH')
                elif tool_name.lower() == 'dart':
                    return self._parse_dart_output(output_text, 'PATH')
                    
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.log(f"{tool_name} not accessible from PATH: {str(e)}")
            
            # Fallback: try with shell=True for Windows compatibility
            try:
                result = subprocess.run(
                    f'{command} --version', 
                    capture_output=True, 
                    text=True, 
                    timeout=30, 
                    shell=True
                )
                
                if result.returncode == 0:
                    output_text = result.stdout + result.stderr
                    
                    if tool_name.lower() == 'flutter':
                        return self._parse_flutter_output(output_text, 'PATH (shell)')
                    elif tool_name.lower() == 'dart':
                        return self._parse_dart_output(output_text, 'PATH (shell)')
                        
            except Exception:
                pass
                
        return None
    
    def _check_flutter_in_directories(self):
        """
        Check for Flutter in common installation directories.
        """
        for search_path in self.common_paths['Flutter']:
            if os.path.exists(search_path):
                # Try both flutter.bat and flutter.cmd
                flutter_executables = [
                    os.path.join(search_path, 'bin', 'flutter.bat'),
                    os.path.join(search_path, 'bin', 'flutter.cmd'),
                    os.path.join(search_path, 'bin', 'flutter')
                ]
                
                for flutter_exe in flutter_executables:
                    if os.path.exists(flutter_exe):
                        try:
                            result = subprocess.run(
                                [flutter_exe, '--version'], 
                                capture_output=True, 
                                text=True, 
                                timeout=30
                            )
                            
                            if result.returncode == 0:
                                output_text = result.stdout + result.stderr
                                flutter_info = self._parse_flutter_output(output_text, search_path)
                                if flutter_info:
                                    return flutter_info
                                    
                        except Exception as e:
                            self.logger.log(f"Failed to run Flutter from {flutter_exe}: {str(e)}")
                            continue
        return None
    
    def _check_dart_bundled_with_flutter(self):
        """
        Check if Dart is bundled with Flutter installation.
        """
        try:
            # Try to get Flutter version which includes Dart info
            result = subprocess.run(
                ['flutter', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=30,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                output_text = result.stdout + result.stderr
                return self._parse_dart_output(output_text, 'Bundled with Flutter')
            
        except Exception:
            # Try shell command as fallback
            try:
                result = subprocess.run(
                    'flutter --version', 
                    capture_output=True, 
                    text=True, 
                    timeout=30, 
                    shell=True
                )
                
                if result.returncode == 0:
                    output_text = result.stdout + result.stderr
                    return self._parse_dart_output(output_text, 'Bundled with Flutter (shell)')
                    
            except Exception:
                pass
                
        return None
    
    def _check_dart_in_directories(self):
        """
        Check for Dart in common installation directories.
        """
        # Check Flutter directories for bundled Dart
        for flutter_path in self.common_paths['Flutter']:
            if os.path.exists(flutter_path):
                dart_exe = os.path.join(flutter_path, 'bin', 'cache', 'dart-sdk', 'bin', 'dart.exe')
                if os.path.exists(dart_exe):
                    try:
                        result = subprocess.run(
                            [dart_exe, '--version'], 
                            capture_output=True, 
                            text=True, 
                            timeout=15
                        )
                        
                        if result.returncode == 0:
                            output_text = result.stdout + result.stderr
                            dart_info = self._parse_dart_output(output_text, os.path.join(flutter_path, 'bin', 'cache', 'dart-sdk'))
                            if dart_info:
                                return dart_info
                                
                    except Exception as e:
                        self.logger.log(f"Failed to run Dart from {dart_exe}: {str(e)}")
                        continue
        
        return None
    
    def _parse_flutter_output(self, output_text, source_path):
        """
        Parse Flutter version output and extract information.
        """
        flutter_info = {
            'installed': False,
            'version': 'Not Found',
            'path': source_path,
            'dart_version': 'Not Found'
        }
        
        # Flutter version patterns
        version_patterns = [
            r'Flutter\s+(\d+\.\d+\.\d+)',
            r'Flutter\s+\(Channel\s+\w+,\s+(\d+\.\d+\.\d+)\)',
            r'Flutter\s+(\d+\.\d+\.\d+)-\w+',
            r'Flutter\s+version\s+(\d+\.\d+\.\d+)',
        ]
        
        for pattern in version_patterns:
            version_match = re.search(pattern, output_text, re.IGNORECASE)
            if version_match:
                flutter_info['installed'] = True
                flutter_info['version'] = version_match.group(1)
                
                # Get actual Flutter path if from PATH
                if source_path in ['PATH', 'PATH (shell)']:
                    try:
                        which_result = subprocess.run(['where', 'flutter'], capture_output=True, text=True)
                        if which_result.returncode == 0:
                            flutter_path = which_result.stdout.strip().split('\n')[0]
                            if flutter_path.endswith(('.bat', '.cmd')):
                                flutter_info['path'] = str(Path(flutter_path).parent.parent)
                            else:
                                flutter_info['path'] = str(Path(flutter_path).parent)
                    except Exception:
                        flutter_info['path'] = 'Found in PATH (location unknown)'
                
                # Extract Dart version
                dart_patterns = [
                    r'Dart\s+(\d+\.\d+\.\d+)',
                    r'Dart\s+SDK\s+version:\s*(\d+\.\d+\.\d+)',
                    r'Dart\s+version\s+(\d+\.\d+\.\d+)',
                ]
                
                for dart_pattern in dart_patterns:
                    dart_match = re.search(dart_pattern, output_text, re.IGNORECASE)
                    if dart_match:
                        flutter_info['dart_version'] = dart_match.group(1)
                        break
                
                self.logger.log(f"Flutter {flutter_info['version']} found at {flutter_info['path']}")
                return flutter_info
                
        return None
    
    def _parse_dart_output(self, output_text, source_path):
        """
        Parse Dart version output and extract information.
        """
        dart_info = {
            'installed': False,
            'version': 'Not Found',
            'path': source_path
        }
        
        # Dart version patterns
        version_patterns = [
            r'Dart\s+SDK\s+version:\s*(\d+\.\d+\.\d+)',
            r'Dart\s+(\d+\.\d+\.\d+)',
            r'Dart\s+version\s+(\d+\.\d+\.\d+)',
            r'version\s+(\d+\.\d+\.\d+)',
        ]
        
        for pattern in version_patterns:
            version_match = re.search(pattern, output_text, re.IGNORECASE)
            if version_match:
                dart_info['installed'] = True
                dart_info['version'] = version_match.group(1)
                
                # Get actual Dart path if from PATH
                if source_path in ['PATH', 'PATH (shell)']:
                    try:
                        which_result = subprocess.run(['where', 'dart'], capture_output=True, text=True)
                        if which_result.returncode == 0:
                            dart_path = which_result.stdout.strip().split('\n')[0]
                            if dart_path.endswith(('.bat', '.exe', '.cmd')):
                                dart_info['path'] = str(Path(dart_path).parent.parent)
                            else:
                                dart_info['path'] = str(Path(dart_path).parent)
                    except Exception:
                        dart_info['path'] = 'Found in PATH (location unknown)'
                
                self.logger.log(f"Dart {dart_info['version']} found at {dart_info['path']}")
                return dart_info
                
        return None
    
    def _check_flutter_executable_exists(self):
        """
        Check if Flutter executable exists in common locations.
        Used when Flutter command times out to determine if it's installed.
        """
        flutter_paths = [
            r'C:\flutter\bin\flutter.bat',
            r'C:\src\flutter\bin\flutter.bat',
            r'C:\tools\flutter\bin\flutter.bat',
            os.path.expanduser(r'~\flutter\bin\flutter.bat'),
            os.path.expanduser(r'~\AppData\Local\flutter\bin\flutter.bat'),
        ]
        
        for flutter_path in flutter_paths:
            if os.path.exists(flutter_path):
                self.logger.log(f"Flutter executable found at: {flutter_path}")
                return True
        
        return False
    
    def _scan_android_studio(self):
        """
        Scan for Android Studio installation.
        Checks registry entries, common installation paths, and validates installation.
        """
        studio_info = {
            'installed': False,
            'version': 'Not Found',
            'path': 'Not Found',
            'sdk_path': 'Not Found'
        }
        
        # Method 1: Check Windows Registry for Android Studio installation
        try:
            # Check HKEY_LOCAL_MACHINE for system-wide installation
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r'SOFTWARE\Android Studio') as key:
                install_path = winreg.QueryValueEx(key, 'Path')[0]
                if os.path.exists(install_path):
                    studio_info['path'] = install_path
                    studio_info['installed'] = True
                    
                    # Try to get version from build.txt
                    build_file = os.path.join(install_path, 'build.txt')
                    if os.path.exists(build_file):
                        with open(build_file, 'r') as f:
                            build_info = f.read().strip()
                            # Extract version from build info (format: AI-XXX.X.X.X)
                            version_match = re.search(r'AI-(\d+\.\d+)', build_info)
                            if version_match:
                                studio_info['version'] = version_match.group(1)
        
        except (WindowsError, FileNotFoundError):
            pass
        
        # Method 2: Search common installation directories
        if not studio_info['installed']:
            for search_path in self.common_paths['Android Studio']:
                if os.path.exists(search_path):
                    # Look for Android Studio executable
                    studio_exe = os.path.join(search_path, 'bin', 'studio64.exe')
                    if os.path.exists(studio_exe):
                        studio_info['installed'] = True
                        studio_info['path'] = search_path
                        
                        # Try to extract version from build.txt
                        build_file = os.path.join(search_path, 'build.txt')
                        if os.path.exists(build_file):
                            try:
                                with open(build_file, 'r') as f:
                                    build_info = f.read().strip()
                                    version_match = re.search(r'AI-(\d+\.\d+)', build_info)
                                    if version_match:
                                        studio_info['version'] = version_match.group(1)
                            except Exception:
                                pass
                        break
        
        # Method 3: Check for Android SDK (required for Flutter development)
        if studio_info['installed']:
            # Look for Android SDK in common locations
            sdk_locations = [
                os.path.expanduser(r'~\AppData\Local\Android\Sdk'),
                r'C:\Android\Sdk',
                os.path.join(studio_info['path'], 'sdk')
            ]
            
            for sdk_path in sdk_locations:
                if os.path.exists(sdk_path) and os.path.exists(os.path.join(sdk_path, 'platform-tools')):
                    studio_info['sdk_path'] = sdk_path
                    break
        
        return studio_info
    
    def _scan_java_jdk(self):
        """
        Scan for Java JDK installation with enhanced detection.
        Checks PATH, JAVA_HOME, and default installation directories.
        """
        jdk_info = {
            'installed': False,
            'version': 'Not Found',
            'path': 'Not Found',
            'java_home': 'Not Set',
            'detection_method': 'none'  # 'path', 'java_home', 'fallback_directory', 'none'
        }
        
        self.logger.log("Scanning for Java JDK...")
        
        # Method 1: Check if java and javac are available in PATH
        self.logger.log("Checking if Java is available in PATH...")
        path_success = self._check_java_in_path()
        if path_success:
            jdk_info.update(path_success)
            jdk_info['detection_method'] = 'path'
            self.logger.log("✅ Java JDK detected from PATH")
            return jdk_info
        
        # Method 2: Check JAVA_HOME environment variable
        self.logger.log("Java not found in PATH, checking JAVA_HOME...")
        java_home = os.environ.get('JAVA_HOME')
        if java_home and os.path.exists(java_home):
            self.logger.log(f"JAVA_HOME is set to: {java_home}")
            java_home_success = self._check_java_in_directory(java_home)
            if java_home_success:
                jdk_info.update(java_home_success)
                jdk_info['java_home'] = java_home
                jdk_info['detection_method'] = 'java_home'
                self.logger.log("✅ Java JDK detected from JAVA_HOME")
                self.logger.log("⚠️ Java is installed but not accessible from PATH", "WARNING")
                self.logger.log("PATH may need to be refreshed - restart terminal or system", "WARNING")
                return jdk_info
        else:
            self.logger.log("JAVA_HOME not set or directory doesn't exist")
        
        # Method 3: Check default installation directories
        self.logger.log("Checking default Java installation directories...")
        default_paths = [
            r'C:\Program Files\Java',
            r'C:\Program Files (x86)\Java',
            r'C:\Java',  # Our custom install location
        ]
        
        for base_path in default_paths:
            if os.path.exists(base_path):
                self.logger.log(f"Checking directory: {base_path}")
                try:
                    # Look for JDK subdirectories
                    for item in os.listdir(base_path):
                        jdk_path = os.path.join(base_path, item)
                        if os.path.isdir(jdk_path) and ('jdk' in item.lower() or 'java' in item.lower()):
                            self.logger.log(f"Found potential JDK directory: {jdk_path}")
                            
                            directory_success = self._check_java_in_directory(jdk_path)
                            if directory_success:
                                jdk_info.update(directory_success)
                                jdk_info['detection_method'] = 'fallback_directory'
                                self.logger.log(f"✅ Java JDK detected from directory: {jdk_path}")
                                self.logger.log("⚠️ Java is installed but not accessible from PATH", "WARNING")
                                self.logger.log("PATH may need to be refreshed - restart terminal or system", "WARNING")
                                return jdk_info
                except Exception as e:
                    self.logger.log(f"Error scanning {base_path}: {str(e)}")
                    continue
        
        self.logger.log("❌ Java JDK not found in PATH or any common install directories")
        jdk_info['detection_method'] = 'none'
        return jdk_info
    
    def _check_java_in_path(self):
        """
        Check if Java and Javac are accessible from PATH using new process.
        """
        try:
            # Test java command
            result = subprocess.run(
                ['java', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=30,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                # Test javac command
                javac_result = subprocess.run(
                    ['javac', '--version'], 
                    capture_output=True, 
                    text=True, 
                    timeout=30,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                )
                
                if javac_result.returncode == 0:
                    # Extract version information
                    version_output = result.stdout + result.stderr
                    version_info = self._parse_java_version(version_output)
                    if version_info:
                        version_info['path'] = 'Found in PATH'
                        return version_info
                else:
                    self.logger.log("Java found in PATH but javac not accessible")
            else:
                self.logger.log("Java not accessible from PATH")
                
        except Exception as e:
            self.logger.log(f"Java PATH test failed: {str(e)}")
        
        return None
    
    def _check_java_in_directory(self, jdk_path):
        """
        Check if Java installation exists in a specific directory.
        """
        java_exe = os.path.join(jdk_path, 'bin', 'java.exe')
        javac_exe = os.path.join(jdk_path, 'bin', 'javac.exe')
        
        if os.path.exists(java_exe) and os.path.exists(javac_exe):
            try:
                # Test java command
                result = subprocess.run(
                    [java_exe, '--version'], 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Test javac command
                    javac_result = subprocess.run(
                        [javac_exe, '--version'], 
                        capture_output=True, 
                        text=True, 
                        timeout=30
                    )
                    
                    if javac_result.returncode == 0:
                        # Extract version information
                        version_output = result.stdout + result.stderr
                        version_info = self._parse_java_version(version_output)
                        if version_info:
                            version_info['path'] = jdk_path
                            return version_info
                    else:
                        self.logger.log(f"Java found but javac failed in {jdk_path}")
                else:
                    self.logger.log(f"Java executable found but failed to run in {jdk_path}")
                    
            except Exception as e:
                self.logger.log(f"Failed to test Java in {jdk_path}: {str(e)}")
        
        return None
    
    def _parse_java_version(self, version_output):
        """
        Parse Java version output and extract information.
        """
        # Java version patterns for different formats
        version_patterns = [
            r'java (\d+\.\d+\.\d+)',  # java 17.0.1
            r'openjdk (\d+\.\d+\.\d+)',  # openjdk 17.0.1
            r'version "(\d+\.\d+)',  # version "17.0"
            r'(\d+\.\d+\.\d+)',  # Just the version number
        ]
        
        for pattern in version_patterns:
            version_match = re.search(pattern, version_output, re.IGNORECASE)
            if version_match:
                return {
                    'installed': True,
                    'version': version_match.group(1)
                }
        
        # If no specific version found but output exists, mark as installed
        if version_output.strip():
            return {
                'installed': True,
                'version': 'Detected (version parsing failed)'
            }
        
        return None
    
    def _scan_git(self):
        """
        Scan for Git installation.
        Checks PATH and common installation directories.
        """
        git_info = {
            'installed': False,
            'version': 'Not Found',
            'path': 'Not Found'
        }
        
        # Method 1: Check if git is in PATH
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_output = result.stdout + result.stderr
                version_match = re.search(r'git version (\d+\.\d+\.\d+)', version_output)
                if version_match:
                    git_info['version'] = version_match.group(1)
                    git_info['installed'] = True
                    git_info['path'] = 'Found in PATH'
                    return git_info
        except Exception:
            pass
        
        # Method 2: Check common installation directories
        git_paths = [
            r'C:\Program Files\Git',
            r'C:\Program Files (x86)\Git',
            r'C:\Git'
        ]
        
        for git_path in git_paths:
            git_exe = os.path.join(git_path, 'bin', 'git.exe')
            if os.path.exists(git_exe):
                try:
                    result = subprocess.run([git_exe, '--version'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        version_output = result.stdout + result.stderr
                        version_match = re.search(r'git version (\d+\.\d+\.\d+)', version_output)
                        if version_match:
                            git_info['version'] = version_match.group(1)
                            git_info['installed'] = True
                            git_info['path'] = git_path
                            return git_info
                except Exception:
                    continue
        
        return git_info
