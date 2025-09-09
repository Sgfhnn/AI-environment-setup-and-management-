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
    """
    
    def __init__(self, logger):
        self.logger = logger
        # Common installation paths for development tools on Windows
        self.common_paths = {
            'Flutter': [
                r'C:\flutter',
                r'C:\src\flutter',
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
                    scan_results[tool] = self._scan_flutter()
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
        Checks PATH, install directories, and provides fallback detection for PATH refresh issues.
        """
        flutter_info = {
            'installed': False,
            'version': 'Not Found',
            'path': 'Not Found',
            'dart_version': 'Not Found',
            'path_status': 'unknown'  # 'in_path', 'install_only', 'not_found'
        }
        
        self.logger.log("Scanning for Flutter SDK...")
        
        # Method 1: Check if Flutter is accessible from PATH (new process)
        path_success = self._check_tool_in_path('flutter', 'Flutter')
        if path_success:
            flutter_info.update(path_success)
            flutter_info['path_status'] = 'in_path'
            return flutter_info
        
        # Method 2: Check common installation directories as fallback
        self.logger.log("Flutter not found in PATH, checking install directories...")
        
        install_success = self._check_flutter_in_directories()
        if install_success:
            flutter_info.update(install_success)
            flutter_info['path_status'] = 'install_only'
            self.logger.log("Flutter found in install directory but not accessible from PATH", "WARNING")
            self.logger.log("PATH may need to be refreshed - restart terminal or system", "WARNING")
            return flutter_info
        
        self.logger.log("Flutter not found in any location")
        flutter_info['path_status'] = 'not_found'
        return flutter_info
    
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
    
    def _scan_android_studio(self):
        """
        Scan for Android Studio installation.
        """
        android_info = {
            'installed': False,
            'version': 'Not Found',
            'path': 'Not Found'
        }
        
        # Check common installation paths
        for search_path in self.common_paths['Android Studio']:
            if os.path.exists(search_path):
                android_info['installed'] = True
                android_info['path'] = search_path
                android_info['version'] = 'Installed'
                break
        
        return android_info
    
    def _scan_java_jdk(self):
        """
        Scan for Java JDK installation.
        """
        java_info = {
            'installed': False,
            'version': 'Not Found',
            'path': 'Not Found'
        }
        
        try:
            result = subprocess.run(['java', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                output_text = result.stdout + result.stderr
                version_match = re.search(r'version\s+"(\d+\.\d+\.\d+)', output_text)
                if version_match:
                    java_info['installed'] = True
                    java_info['version'] = version_match.group(1)
                    java_info['path'] = 'Found in PATH'
        except Exception:
            pass
        
        return java_info
    
    def _scan_git(self):
        """
        Scan for Git installation.
        """
        git_info = {
            'installed': False,
            'version': 'Not Found',
            'path': 'Not Found'
        }
        
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                output_text = result.stdout + result.stderr
                version_match = re.search(r'git version (\d+\.\d+\.\d+)', output_text)
                if version_match:
                    git_info['installed'] = True
                    git_info['version'] = version_match.group(1)
                    git_info['path'] = 'Found in PATH'
        except Exception:
            pass
        
        return git_info
    
    def check_environment_variables(self):
        """
        Check critical environment variables for Flutter development.
        Returns a dictionary with environment variable status and recommendations.
        """
        env_status = {}
        
        # Check JAVA_HOME
        java_home = os.environ.get('JAVA_HOME')
        env_status['JAVA_HOME'] = {
            'set': java_home is not None,
            'value': java_home,
            'valid': False
        }
        
        if java_home and os.path.exists(java_home):
            java_exe = os.path.join(java_home, 'bin', 'java.exe')
            env_status['JAVA_HOME']['valid'] = os.path.exists(java_exe)
        
        # Check ANDROID_HOME or ANDROID_SDK_ROOT
        android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
        env_status['ANDROID_HOME'] = {
            'set': android_home is not None,
            'value': android_home,
            'valid': False
        }
        
        if android_home and os.path.exists(android_home):
            platform_tools = os.path.join(android_home, 'platform-tools')
            env_status['ANDROID_HOME']['valid'] = os.path.exists(platform_tools)
        
        # Check PATH for Flutter
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        flutter_in_path = any('flutter' in path_dir.lower() for path_dir in path_dirs)
        env_status['FLUTTER_PATH'] = {
            'set': flutter_in_path,
            'value': 'Found in PATH' if flutter_in_path else 'Not in PATH',
            'valid': flutter_in_path
        }
        
        return env_status
    
    def get_system_info(self):
        """
        Gather additional system information relevant to Flutter development.
        Includes Windows version, architecture, and available disk space.
        """
        system_info = {}
        
        try:
            # Windows version
            import platform
            system_info['os'] = platform.system()
            system_info['os_version'] = platform.version()
            system_info['architecture'] = platform.architecture()[0]
            
            # Available disk space on C: drive
            import shutil
            total, used, free = shutil.disk_usage('C:')
            system_info['disk_space'] = {
                'total_gb': round(total / (1024**3), 2),
                'free_gb': round(free / (1024**3), 2),
                'used_gb': round(used / (1024**3), 2)
            }
            
            # Check if virtualization is enabled (for Android emulator)
            try:
                result = subprocess.run(['systeminfo'], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    hyper_v_match = re.search(r'Hyper-V Requirements.*?VM Monitor Mode Extensions: (Yes|No)', 
                                            result.stdout, re.DOTALL)
                    if hyper_v_match:
                        system_info['virtualization'] = hyper_v_match.group(1) == 'Yes'
            except:
                system_info['virtualization'] = 'Unknown'
        
        except Exception as e:
            self.logger.log(f"Error gathering system info: {str(e)}", "ERROR")
            system_info['error'] = str(e)
        
        return system_info
    
    def _scan_git(self):
        """
        Scan for Git installation on Windows.
        Checks PATH, common installation directories, and validates Git installation.
        """
        git_info = {
            'installed': False,
            'version': 'Not Found',
            'path': 'Not Found'
        }
        
        # Debug logging to show what we're detecting
        self.logger.log("=== GIT DETECTION DEBUG ===", "DEBUG")
        self.logger.log(f"Current PATH: {os.environ.get('PATH', 'NOT SET')[:200]}...", "DEBUG")
        
        try:
            # Method 1: Check if Git is in PATH by running git --version
            self.logger.log("DEBUG: Attempting to run 'git --version' from PATH", "DEBUG")
            
            # Try without shell first (more secure)
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, timeout=15)
            
            self.logger.log(f"DEBUG: Git command return code: {result.returncode}", "DEBUG")
            self.logger.log(f"DEBUG: Git stdout: {result.stdout[:200]}", "DEBUG")
            self.logger.log(f"DEBUG: Git stderr: {result.stderr[:200]}", "DEBUG")
            
            if result.returncode == 0:
                # Git version output is typically in stdout
                output_text = result.stdout + result.stderr
                self.logger.log(f"DEBUG: Combined Git output: {output_text[:300]}", "DEBUG")
                
                # Multiple regex patterns to handle different Git version formats
                # Pattern examples:
                # "git version 2.42.0.windows.2"
                # "git version 2.42.0"
                version_patterns = [
                    r'git\s+version\s+(\d+\.\d+\.\d+)',  # Standard format
                    r'git\s+version\s+(\d+\.\d+\.\d+)\.windows\.\d+',  # Windows format
                    r'version\s+(\d+\.\d+\.\d+)',  # Just version number
                ]
                
                version_found = False
                for i, pattern in enumerate(version_patterns):
                    version_match = re.search(pattern, output_text, re.IGNORECASE)
                    if version_match:
                        git_info['version'] = version_match.group(1)
                        git_info['installed'] = True
                        version_found = True
                        self.logger.log(f"DEBUG: Git version found with pattern {i+1}: {version_match.group(1)}", "DEBUG")
                        break
                
                if version_found:
                    # Get Git installation path using 'where' command
                    try:
                        self.logger.log("DEBUG: Attempting to find Git path with 'where' command", "DEBUG")
                        which_result = subprocess.run(['where', 'git'], 
                                                    capture_output=True, text=True)
                        self.logger.log(f"DEBUG: 'where git' return code: {which_result.returncode}", "DEBUG")
                        self.logger.log(f"DEBUG: 'where git' output: {which_result.stdout}", "DEBUG")
                        
                        if which_result.returncode == 0:
                            git_path = which_result.stdout.strip().split('\n')[0]
                            self.logger.log(f"DEBUG: Raw Git path: {git_path}", "DEBUG")
                            
                            # Handle both git.exe and git.cmd
                            if git_path.endswith(('.exe', '.cmd')):
                                # Get the installation root directory (remove \bin\git.exe)
                                git_info['path'] = str(Path(git_path).parent.parent)
                            else:
                                git_info['path'] = str(Path(git_path).parent)
                            
                            self.logger.log(f"DEBUG: Resolved Git installation path: {git_info['path']}", "DEBUG")
                    except Exception as e:
                        self.logger.log(f"DEBUG: 'where' command failed: {str(e)}", "DEBUG")
                        git_info['path'] = 'Found in PATH (location unknown)'
                    
                    self.logger.log("DEBUG: Git detected successfully via PATH", "DEBUG")
                    return git_info
                else:
                    self.logger.log("DEBUG: Git command succeeded but no version pattern matched", "DEBUG")
            else:
                self.logger.log(f"DEBUG: Git command failed with return code {result.returncode}", "DEBUG")
        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            self.logger.log(f"DEBUG: Git PATH detection failed with exception: {type(e).__name__}: {str(e)}", "DEBUG")
            
            # Try with shell=True as fallback for Windows compatibility
            try:
                self.logger.log("DEBUG: Retrying Git detection with shell=True", "DEBUG")
                result = subprocess.run('git --version', 
                                      capture_output=True, text=True, timeout=15, shell=True)
                
                self.logger.log(f"DEBUG: Shell Git command return code: {result.returncode}", "DEBUG")
                
                if result.returncode == 0:
                    output_text = result.stdout + result.stderr
                    self.logger.log(f"DEBUG: Shell Git output: {output_text[:300]}", "DEBUG")
                    
                    # Use same version patterns
                    version_patterns = [
                        r'git\s+version\s+(\d+\.\d+\.\d+)',
                        r'git\s+version\s+(\d+\.\d+\.\d+)\.windows\.\d+',
                        r'version\s+(\d+\.\d+\.\d+)',
                    ]
                    
                    for pattern in version_patterns:
                        version_match = re.search(pattern, output_text, re.IGNORECASE)
                        if version_match:
                            git_info['version'] = version_match.group(1)
                            git_info['installed'] = True
                            
                            # Try to get path
                            try:
                                which_result = subprocess.run('where git', 
                                                            capture_output=True, text=True, shell=True)
                                if which_result.returncode == 0:
                                    git_path = which_result.stdout.strip().split('\n')[0]
                                    if git_path.endswith(('.exe', '.cmd')):
                                        git_info['path'] = str(Path(git_path).parent.parent)
                                    else:
                                        git_info['path'] = str(Path(git_path).parent)
                            except Exception:
                                git_info['path'] = 'Found in PATH (location unknown)'
                            
                            self.logger.log("DEBUG: Git detected successfully via shell command", "DEBUG")
                            return git_info
                            
            except Exception as shell_e:
                self.logger.log(f"DEBUG: Shell Git detection also failed: {str(shell_e)}", "DEBUG")
        
        # Method 2: Search common Git installation directories on Windows
        self.logger.log("DEBUG: Git not found in PATH, checking common directories", "DEBUG")
        
        common_git_paths = [
            r'C:\Program Files\Git',
            r'C:\Program Files (x86)\Git',
            r'C:\Git',
            os.path.expanduser(r'~\AppData\Local\Programs\Git'),
            os.path.expanduser(r'~\scoop\apps\git'),
            r'C:\tools\git',
        ]
        
        for search_path in common_git_paths:
            self.logger.log(f"DEBUG: Checking directory: {search_path}", "DEBUG")
            
            if os.path.exists(search_path):
                self.logger.log(f"DEBUG: Directory exists: {search_path}", "DEBUG")
                
                # Try different Git executable locations
                git_executables = [
                    os.path.join(search_path, 'bin', 'git.exe'),
                    os.path.join(search_path, 'cmd', 'git.exe'),
                    os.path.join(search_path, 'git.exe'),
                ]
                
                for git_exe in git_executables:
                    self.logger.log(f"DEBUG: Checking executable: {git_exe}", "DEBUG")
                    
                    if os.path.exists(git_exe):
                        self.logger.log(f"DEBUG: Executable found: {git_exe}", "DEBUG")
                        
                        try:
                            result = subprocess.run([git_exe, '--version'], 
                                                  capture_output=True, text=True, timeout=15)
                            
                            self.logger.log(f"DEBUG: Direct exe return code: {result.returncode}", "DEBUG")
                            
                            if result.returncode == 0:
                                output_text = result.stdout + result.stderr
                                self.logger.log(f"DEBUG: Direct exe output: {output_text[:200]}", "DEBUG")
                                
                                # Use same version patterns
                                version_patterns = [
                                    r'git\s+version\s+(\d+\.\d+\.\d+)',
                                    r'git\s+version\s+(\d+\.\d+\.\d+)\.windows\.\d+',
                                    r'version\s+(\d+\.\d+\.\d+)',
                                ]
                                
                                for pattern in version_patterns:
                                    version_match = re.search(pattern, output_text, re.IGNORECASE)
                                    if version_match:
                                        git_info['installed'] = True
                                        git_info['version'] = version_match.group(1)
                                        git_info['path'] = search_path
                                        
                                        self.logger.log(f"DEBUG: Git detected in directory: {search_path}", "DEBUG")
                                        return git_info
                        
                        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
                            self.logger.log(f"DEBUG: Direct exe failed for {git_exe}: {str(e)}", "DEBUG")
                            continue
            else:
                self.logger.log(f"DEBUG: Directory does not exist: {search_path}", "DEBUG")
        
        self.logger.log("DEBUG: Git not found in any location", "DEBUG")
        self.logger.log("=== END GIT DETECTION DEBUG ===", "DEBUG")
        return git_info
