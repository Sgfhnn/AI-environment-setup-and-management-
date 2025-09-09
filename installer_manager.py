import os
import subprocess
import urllib.request
import tempfile
import shutil
import json
from pathlib import Path
import zipfile
import tarfile
from resource_path import get_temp_dir, get_app_data_dir
import sys
from datetime import datetime
import zipfile
import tarfile

class InstallerManager:
    """
    Manages installation of Flutter development tools on Windows.
    Handles downloads, installations, environment configuration, and rollback functionality.
    """
    
    def __init__(self, logger):
        self.logger = logger
        self.temp_dir = tempfile.mkdtemp(prefix="flutter_setup_")
        self.rollback_file = os.path.join(self.temp_dir, "rollback_info.json")
        self.rollback_data = []
        
        # Download URLs for development tools (latest stable versions)
        self.download_urls = {
            'Flutter': {
                'url': 'https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.35.3-stable.zip',
                'filename': 'flutter_windows_stable.zip',
                'install_dir': r'C:\flutter'
            },
            'Android Studio': {
                'url': 'https://redirector.gvt1.com/edgedl/android/studio/install/2025.1.3.7/android-studio-2025.1.3.7-windows.exe',
                'filename': 'android-studio-installer.exe',
                'install_dir': r'C:\Program Files\Android\Android Studio'
            },
            'Java JDK': {
                'url': 'https://download.oracle.com/java/24/latest/jdk-24_windows-x64_bin.zip',
                'filename': 'jdk-24-installer.zip',
                'install_dir': r'C:\Program Files\Java\jdk-24'
            },
            'Git': {
                'url': 'https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe',
                'filename': 'git-installer.exe',
                'install_dir': r'C:\Program Files\Git'
            }
        }
    
    def is_admin(self):
        """
        Check if the current process has administrator privileges.
        Required for installing software and modifying system environment variables.
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def request_admin_privileges(self):
        """
        Request administrator privileges using UAC (User Account Control).
        Restarts the application with elevated permissions if needed.
        """
        if not self.is_admin():
            self.logger.log("Requesting administrator privileges...")
            try:
                # Re-run the program with admin privileges
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                return True
            except Exception as e:
                self.logger.log(f"Failed to request admin privileges: {str(e)}", "ERROR")
                return False
        return True
    
    def install_tool(self, tool_name, tool_info, progress_callback=None):
        """
        Install a specific development tool with unified installer handling.
        Handles download, installation, and environment configuration for all installer types.
        """
        self.logger.log(f"Starting installation of {tool_name}...")
        
        try:
            if tool_name == 'Dart':
                # Dart is bundled with Flutter, so install Flutter instead
                self.logger.log("Dart is bundled with Flutter. Installing Flutter...")
                return self._install_unified('Flutter', progress_callback)
            else:
                return self._install_unified(tool_name, progress_callback)
        
        except Exception as e:
            self.logger.log(f"Installation of {tool_name} failed: {str(e)}", "ERROR")
            return False
    
    def _detect_installer_type(self, filename):
        """
        Detect installer type based on file extension.
        Returns: 'zip', 'exe', 'msi', or 'unknown'
        """
        filename_lower = filename.lower()
        if filename_lower.endswith('.zip'):
            return 'zip'
        elif filename_lower.endswith('.exe'):
            return 'exe'
        elif filename_lower.endswith('.msi'):
            return 'msi'
        else:
            return 'unknown'
    
    def _install_unified(self, tool_name, progress_callback=None):
        """
        Unified installation method that handles all installer types.
        Automatically detects installer format and uses appropriate handler.
        """
        if tool_name not in self.download_urls:
            self.logger.log(f"No download configuration found for {tool_name}", "ERROR")
            return False
        
        tool_info = self.download_urls[tool_name]
        installer_type = self._detect_installer_type(tool_info['filename'])
        
        self.logger.log(f"Installing {tool_name} using {installer_type} installer")
        
        # Create progress callback wrapper for download
        def download_progress(percent, downloaded, total):
            if progress_callback:
                # Download is typically 70% of total installation process
                overall_progress = int(percent * 0.7)
                status = f"Downloading {tool_name}: {percent}% ({downloaded:,}/{total:,} bytes)"
                progress_callback(overall_progress, status)
        
        # Download the installer
        downloaded_file = self._download_file(tool_info['url'], tool_info['filename'], download_progress)
        
        if not downloaded_file:
            return False
        
        # Update progress for installation phase
        if progress_callback:
            progress_callback(70, f"Installing {tool_name}...")
        
        # Install based on type
        try:
            if installer_type == 'zip':
                success = self._install_from_zip(tool_name, downloaded_file, tool_info, progress_callback)
            elif installer_type == 'exe':
                success = self._install_from_exe(tool_name, downloaded_file, tool_info, progress_callback)
            elif installer_type == 'msi':
                success = self._install_from_msi(tool_name, downloaded_file, tool_info, progress_callback)
            else:
                self.logger.log(f"Unsupported installer type: {installer_type}", "ERROR")
                return False
            
            if success and progress_callback:
                progress_callback(100, f"{tool_name} installation completed successfully")
            
            return success
            
        except Exception as e:
            self.logger.log(f"Installation failed for {tool_name}: {str(e)}", "ERROR")
            return False
    
    def _download_file(self, url, filename, progress_callback=None):
        """
        Download a file from URL with progress tracking in a separate thread.
        Includes retry logic and error handling for network issues.
        """
        file_path = os.path.join(self.temp_dir, filename)
        self.logger.log(f"Downloading {filename} from {url}")
        
        try:
            import requests
            import threading
            
            # Use requests for better progress tracking
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            self.logger.log(f"Download size: {total_size} bytes")
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Report progress
                        if progress_callback and total_size > 0:
                            percent = min(100, (downloaded_size * 100) // total_size)
                            progress_callback(percent, downloaded_size, total_size)
            
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                self.logger.log(f"Downloaded {filename} successfully ({file_size} bytes)")
                return file_path
            else:
                raise Exception("Download completed but file not found")
        
        except Exception as e:
            self.logger.log(f"Download failed for {filename}: {str(e)}", "ERROR")
            # Fallback to urllib if requests fails
            try:
                def report_progress(block_num, block_size, total_size):
                    if progress_callback and total_size > 0:
                        downloaded = block_num * block_size
                        percent = min(100, (downloaded * 100) // total_size)
                        progress_callback(percent, downloaded, total_size)
                
                urllib.request.urlretrieve(url, file_path, reporthook=report_progress)
                
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    self.logger.log(f"Downloaded {filename} successfully via fallback ({file_size} bytes)")
                    return file_path
                else:
                    raise Exception("Fallback download completed but file not found")
            except Exception as fallback_e:
                self.logger.log(f"Fallback download also failed for {filename}: {str(fallback_e)}", "ERROR")
                return None
    
    def _install_from_zip(self, tool_name, zip_file_path, tool_info, progress_callback=None):
        """
        Install from ZIP archive by extracting to target directory.
        Handles Flutter and other ZIP-based installations.
        """
        try:
            install_dir = tool_info['install_dir']
            
            # Backup existing installation if it exists
            if os.path.exists(install_dir):
                backup_dir = f"{install_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.logger.log(f"Backing up existing {tool_name} installation to {backup_dir}")
                try:
                    shutil.move(install_dir, backup_dir)
                    self._add_rollback_action('restore_directory', install_dir, backup_dir)
                except PermissionError as pe:
                    error_msg = f"Permission denied when backing up {install_dir}: {str(pe)}"
                    self.logger.log(error_msg, "ERROR")
                    raise PermissionError(error_msg)
            
            if progress_callback:
                progress_callback(75, f"Extracting {tool_name}...")
            
            # Extract ZIP file
            self.logger.log(f"Extracting {tool_name} to {install_dir}")
            try:
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    # For Flutter, extract to parent directory (zip contains 'flutter' folder)
                    if tool_name.lower() == 'flutter':
                        extract_to = os.path.dirname(install_dir)
                    else:
                        extract_to = install_dir
                    
                    # Ensure target directory exists and is writable
                    os.makedirs(extract_to, exist_ok=True)
                    zip_ref.extractall(extract_to)
                    
            except PermissionError as pe:
                error_msg = f"Permission denied when extracting {tool_name} to {extract_to}: {str(pe)}"
                self.logger.log(error_msg, "ERROR")
                raise PermissionError(error_msg)
            except Exception as e:
                error_msg = f"Failed to extract {tool_name}: {str(e)}"
                self.logger.log(error_msg, "ERROR")
                raise Exception(error_msg)
            
            self._add_rollback_action('remove_directory', install_dir)
            
            if progress_callback:
                progress_callback(85, f"Configuring {tool_name} PATH...")
            
            # Add to PATH based on tool type
            if tool_name.lower() == 'flutter':
                # Verify Flutter executable exists
                flutter_exe = os.path.join(install_dir, 'bin', 'flutter.bat')
                if not os.path.exists(flutter_exe):
                    raise Exception("Flutter executable not found after extraction")
                
                # Add Flutter bin to PATH
                flutter_bin_path = os.path.join(install_dir, 'bin')
                self._add_to_system_path(flutter_bin_path)
                
                # Run flutter doctor to complete setup with streaming output
                if progress_callback:
                    progress_callback(90, f"Running Flutter doctor...")
                
                self._run_flutter_doctor_with_streaming(flutter_exe, progress_callback)
                
                # Verify Flutter installation with new process
                if progress_callback:
                    progress_callback(99, "Verifying Flutter installation...")
                self._verify_tool_installation('Flutter', 'flutter', install_dir)
            
            elif tool_name.lower() == 'java jdk':
                # Handle Java JDK zip extraction and setup
                self._setup_java_jdk(install_dir, progress_callback)
            
            else:
                # Generic ZIP installation - add main directory to PATH
                self._add_to_system_path(install_dir)
            
            self.logger.log(f"{tool_name} ZIP installation completed successfully")
            return True
            
        except Exception as e:
            self.logger.log(f"{tool_name} ZIP installation failed: {str(e)}", "ERROR")
            return False
    
    def _install_from_exe(self, tool_name, exe_file_path, tool_info, progress_callback=None):
        """
        Install from EXE installer with silent installation.
        Handles Android Studio, Git, and other EXE-based installations.
        """
        try:
            # Check for admin privileges for EXE installers
            if not self.is_admin():
                self.logger.log(f"Administrator privileges required for {tool_name} installation", "ERROR")
                return False
            
            if progress_callback:
                progress_callback(75, f"Running {tool_name} installer...")
            
            # Configure installer command based on tool
            if tool_name.lower() == 'android studio':
                return self._install_android_studio_silent(exe_file_path, tool_info, progress_callback)
                
            elif tool_name.lower() == 'git':
                install_cmd = [
                    exe_file_path,
                    '/VERYSILENT',  # Very silent installation
                    '/NORESTART',   # Don't restart after installation
                    '/NOCANCEL',    # Don't allow cancellation
                    '/SP-',         # Disable "This will install..." message
                    '/CLOSEAPPLICATIONS',  # Close applications using files to be updated
                    '/RESTARTAPPLICATIONS',  # Restart applications after installation
                    f'/DIR={tool_info["install_dir"]}',  # Installation directory
                    '/COMPONENTS=ext,ext\\shellhere,ext\\guihere,gitlfs,assoc,assoc_sh',
                    '/TASKS=desktopicon,quicklaunchicon,addcontextmenufiles,addcontextmenufolders,associateshfiles',
                    '/o:PathOption=Cmd',  # Add Git to PATH for command line
                    '/o:BashTerminalOption=ConHost',
                    '/o:EditorOption=Notepad',
                    '/o:CRLFOption=CRLFAlways',
                    '/o:BranchOption=BranchAlways',
                    '/o:PerformanceTweaksFSCache=Enabled',
                    '/o:UseCredentialManager=Enabled',
                    '/o:EnableSymlinks=Disabled',
                    '/o:EnablePseudoConsoleSupport=Disabled',
                    '/o:EnableFSMonitor=Disabled'
                ]
                timeout = 600  # 10 minutes for Git
                
            elif tool_name.lower() == 'java jdk':
                install_cmd = [
                    exe_file_path,
                    '/s',  # Silent installation
                    f'INSTALLDIR={tool_info["install_dir"]}'
                ]
                timeout = 600  # 10 minutes for Java JDK
                
            else:
                # Generic EXE installer
                install_cmd = [exe_file_path, '/S', f'/D={tool_info["install_dir"]}']
                timeout = 600
            
            # Run installer
            self.logger.log(f"Running {tool_name} installer with command: {' '.join(install_cmd)}")
            result = subprocess.run(install_cmd, timeout=timeout)
            
            if result.returncode == 0:
                self.logger.log(f"{tool_name} EXE installation completed")
                self._add_rollback_action('uninstall_program', tool_name)
                
                if progress_callback:
                    progress_callback(90, f"Configuring {tool_name} environment...")
                
                # Post-installation configuration
                if tool_name.lower() == 'android studio':
                    # Configure Android SDK environment variables
                    sdk_path = os.path.expanduser(r'~\AppData\Local\Android\Sdk')
                    self._set_environment_variable('ANDROID_HOME', sdk_path)
                    self._set_environment_variable('ANDROID_SDK_ROOT', sdk_path)
                    
                    # Add Android SDK tools to PATH
                    platform_tools = os.path.join(sdk_path, 'platform-tools')
                    if os.path.exists(platform_tools):
                        self._add_to_system_path(platform_tools)
                
                elif tool_name.lower() == 'git':
                    # Verify Git installation and add to PATH if needed
                    git_exe_path = os.path.join(tool_info['install_dir'], 'bin', 'git.exe')
                    if os.path.exists(git_exe_path):
                        git_bin_path = os.path.join(tool_info['install_dir'], 'bin')
                        self._add_to_system_path(git_bin_path)
                        
                        # Test Git installation
                        try:
                            test_result = subprocess.run([git_exe_path, '--version'], 
                                                       capture_output=True, text=True, timeout=10)
                            if test_result.returncode == 0:
                                self.logger.log(f"Git installation verified: {test_result.stdout.strip()}")
                        except Exception as e:
                            self.logger.log(f"Git verification failed: {str(e)}", "WARNING")
                
                elif tool_name.lower() == 'java jdk':
                    # Set JAVA_HOME and add bin to PATH
                    self._set_environment_variable('JAVA_HOME', tool_info['install_dir'])
                    java_bin_path = os.path.join(tool_info['install_dir'], 'bin')
                    self._add_to_system_path(java_bin_path)
                
                return True
            else:
                self.logger.log(f"{tool_name} installer failed with code {result.returncode}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.log(f"{tool_name} installation timed out", "ERROR")
            return False
        except Exception as e:
            self.logger.log(f"{tool_name} EXE installation failed: {str(e)}", "ERROR")
            return False
    
    def _install_android_studio_silent(self, exe_file_path, tool_info, progress_callback=None):
        """
        Install Android Studio with silent installation and proper error handling.
        """
        try:
            if progress_callback:
                progress_callback(75, "Installing Android Studio silently...")
            
            self.logger.log("Starting Android Studio silent installation...")
            
            # Configure silent installation command
            install_cmd = [
                exe_file_path,
                '/S',  # Silent installation flag
                f'/D={tool_info["install_dir"]}'  # Installation directory
            ]
            
            self.logger.log(f"Running Android Studio installer: {' '.join(install_cmd)}")
            
            # Run installer with extended timeout
            result = subprocess.run(install_cmd, timeout=1800)  # 30 minutes
            
            if result.returncode == 0:
                if progress_callback:
                    progress_callback(85, "Verifying Android Studio installation...")
                
                # Verify installation in default directory
                if self._verify_android_studio_installation(tool_info["install_dir"]):
                    self.logger.log("✅ Android Studio silent installation completed successfully")
                    
                    # Configure environment
                    if progress_callback:
                        progress_callback(90, "Configuring Android Studio environment...")
                    
                    self._configure_android_studio_environment()
                    
                    if progress_callback:
                        progress_callback(95, "Android Studio setup completed")
                    
                    return True
                else:
                    self.logger.log("Android Studio installation verification failed", "ERROR")
                    return self._handle_android_studio_manual_fallback(exe_file_path, tool_info)
            
            else:
                self.logger.log(f"Android Studio silent installation failed with exit code: {result.returncode}", "ERROR")
                return self._handle_android_studio_manual_fallback(exe_file_path, tool_info)
                
        except subprocess.TimeoutExpired:
            self.logger.log("Android Studio installation timed out after 30 minutes", "ERROR")
            return self._handle_android_studio_manual_fallback(exe_file_path, tool_info)
        except Exception as e:
            self.logger.log(f"Android Studio installation failed: {str(e)}", "ERROR")
            return self._handle_android_studio_manual_fallback(exe_file_path, tool_info)
    
    def _verify_android_studio_installation(self, install_dir):
        """
        Verify Android Studio installation by checking for studio64.exe and registry.
        """
        try:
            # Check for studio64.exe in default directory
            studio_exe = os.path.join(install_dir, 'bin', 'studio64.exe')
            if os.path.exists(studio_exe):
                self.logger.log(f"Android Studio executable found: {studio_exe}")
                
                # Try to get version information
                try:
                    result = subprocess.run(
                        [studio_exe, '--version'], 
                        capture_output=True, 
                        text=True, 
                        timeout=30
                    )
                    if result.returncode == 0:
                        self.logger.log(f"Android Studio version verified: {result.stdout.strip()}")
                        return True
                except Exception:
                    # Version check failed, but executable exists
                    self.logger.log("Android Studio executable found but version check failed")
                    return True
            
            # Check registry as fallback
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r'SOFTWARE\Android Studio') as key:
                    install_path = winreg.QueryValueEx(key, 'Path')[0]
                    if os.path.exists(install_path):
                        self.logger.log(f"Android Studio found in registry: {install_path}")
                        return True
            except (WindowsError, FileNotFoundError):
                pass
            
            self.logger.log("Android Studio installation verification failed")
            return False
            
        except Exception as e:
            self.logger.log(f"Error verifying Android Studio installation: {str(e)}")
            return False
    
    def _configure_android_studio_environment(self):
        """
        Configure Android Studio environment variables and PATH.
        """
        try:
            # Configure Android SDK environment variables
            sdk_path = os.path.expanduser(r'~\AppData\Local\Android\Sdk')
            self.logger.log(f"Setting Android SDK environment variables to: {sdk_path}")
            
            self._set_environment_variable('ANDROID_HOME', sdk_path)
            self._set_environment_variable('ANDROID_SDK_ROOT', sdk_path)
            
            # Add Android SDK tools to PATH if they exist
            platform_tools = os.path.join(sdk_path, 'platform-tools')
            if os.path.exists(platform_tools):
                self.logger.log(f"Adding Android platform-tools to PATH: {platform_tools}")
                self._add_to_system_path(platform_tools)
            else:
                self.logger.log("Android platform-tools not found, will be available after first SDK download")
                
        except Exception as e:
            self.logger.log(f"Error configuring Android Studio environment: {str(e)}", "WARNING")
    
    def _handle_android_studio_manual_fallback(self, exe_file_path, tool_info):
        """
        Handle fallback to manual installation if silent install fails.
        """
        try:
            self.logger.log("Silent installation failed, prompting for manual installation...", "WARNING")
            self.logger.log("=" * 60, "INFO")
            self.logger.log("MANUAL INSTALLATION REQUIRED", "INFO")
            self.logger.log("=" * 60, "INFO")
            self.logger.log(f"Please run the installer manually: {exe_file_path}", "INFO")
            self.logger.log(f"Install to directory: {tool_info['install_dir']}", "INFO")
            self.logger.log("After installation completes, the scanner will detect it automatically.", "INFO")
            self.logger.log("=" * 60, "INFO")
            
            # Check if user completed manual installation
            import time
            for i in range(12):  # Check for 2 minutes
                if self._verify_android_studio_installation(tool_info["install_dir"]):
                    self.logger.log("✅ Manual Android Studio installation detected!")
                    self._configure_android_studio_environment()
                    return True
                
                self.logger.log(f"Waiting for manual installation... ({i+1}/12)")
                time.sleep(10)
            
            self.logger.log("Manual installation not detected within timeout", "WARNING")
            self.logger.log("You can complete the installation later and run the scanner again", "INFO")
            return False
            
        except Exception as e:
            self.logger.log(f"Error in manual installation fallback: {str(e)}", "ERROR")
            return False
    
    def _install_from_msi(self, tool_name, msi_file_path, tool_info, progress_callback=None):
        """
        Install from MSI installer using msiexec with silent installation.
        Handles MSI-based installations like some Java distributions.
        """
        try:
            # Check for admin privileges for MSI installers
            if not self.is_admin():
                self.logger.log(f"Administrator privileges required for {tool_name} MSI installation", "ERROR")
                return False
            
            if progress_callback:
                progress_callback(75, f"Running {tool_name} MSI installer...")
            
            # Configure MSI installer command
            install_cmd = [
                'msiexec',
                '/i', msi_file_path,  # Install package
                '/quiet',  # Quiet mode (no user interaction)
                '/norestart',  # Don't restart after installation
                f'INSTALLDIR={tool_info["install_dir"]}',  # Installation directory
                '/L*V', os.path.join(self.temp_dir, f'{tool_name}_install.log')  # Verbose logging
            ]
            
            # Run MSI installer
            self.logger.log(f"Running {tool_name} MSI installer with command: {' '.join(install_cmd)}")
            result = subprocess.run(install_cmd, timeout=600)  # 10 minute timeout
            
            if result.returncode == 0:
                self.logger.log(f"{tool_name} MSI installation completed")
                self._add_rollback_action('uninstall_program', tool_name)
                
                if progress_callback:
                    progress_callback(90, f"Configuring {tool_name} environment...")
                
                # Post-installation configuration for MSI packages
                if 'java' in tool_name.lower():
                    # Set JAVA_HOME and add bin to PATH
                    self._set_environment_variable('JAVA_HOME', tool_info['install_dir'])
                    java_bin_path = os.path.join(tool_info['install_dir'], 'bin')
                    self._add_to_system_path(java_bin_path)
                else:
                    # Generic MSI installation - add main directory to PATH
                    self._add_to_system_path(tool_info['install_dir'])
                
                return True
            else:
                self.logger.log(f"{tool_name} MSI installer failed with code {result.returncode}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.log(f"{tool_name} MSI installation timed out", "ERROR")
            return False
        except Exception as e:
            self.logger.log(f"{tool_name} MSI installation failed: {str(e)}", "ERROR")
            return False
    
    def _install_flutter(self):
        """
        Install Flutter SDK by downloading and extracting to C:\flutter.
        Configures PATH environment variable for system-wide access.
        """
        self.logger.log("Installing Flutter SDK...")
        
        # Download Flutter SDK
        flutter_info = self.download_urls['Flutter']
        downloaded_file = self._download_file(flutter_info['url'], flutter_info['filename'])
        
        if not downloaded_file:
            return False
        
        try:
            # Create installation directory
            install_dir = flutter_info['install_dir']
            if os.path.exists(install_dir):
                # Backup existing installation
                backup_dir = f"{install_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.logger.log(f"Backing up existing Flutter installation to {backup_dir}")
                shutil.move(install_dir, backup_dir)
                self._add_rollback_action('restore_directory', install_dir, backup_dir)
            
            # Extract Flutter SDK
            self.logger.log(f"Extracting Flutter to {install_dir}")
            with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
                # Extract to parent directory (zip contains 'flutter' folder)
                extract_to = os.path.dirname(install_dir)
                zip_ref.extractall(extract_to)
            
            self._add_rollback_action('remove_directory', install_dir)
            
            # Verify installation
            flutter_exe = os.path.join(install_dir, 'bin', 'flutter.bat')
            if not os.path.exists(flutter_exe):
                raise Exception("Flutter executable not found after extraction")
            
            # Add Flutter to PATH
            flutter_bin_path = os.path.join(install_dir, 'bin')
            self._add_to_system_path(flutter_bin_path)
            
            # Run flutter doctor to complete setup
            self.logger.log("Running flutter doctor to complete setup...")
            result = subprocess.run([flutter_exe, 'doctor'], 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.logger.log("Flutter installation completed successfully")
                return True
            else:
                self.logger.log(f"Flutter doctor reported issues: {result.stdout}", "WARNING")
                return True  # Still consider successful if Flutter is installed
        
        except Exception as e:
            self.logger.log(f"Flutter installation failed: {str(e)}", "ERROR")
            return False
    
    def _install_android_studio(self):
        """
        Install Android Studio using the official installer.
        Handles silent installation and SDK configuration.
        """
        self.logger.log("Installing Android Studio...")
        
        # Check for admin privileges
        if not self.is_admin():
            self.logger.log("Administrator privileges required for Android Studio installation", "ERROR")
            return False
        
        # Download Android Studio installer
        studio_info = self.download_urls['Android Studio']
        downloaded_file = self._download_file(studio_info['url'], studio_info['filename'])
        
        if not downloaded_file:
            return False
        
        try:
            # Run Android Studio installer silently
            self.logger.log("Running Android Studio installer...")
            install_cmd = [
                downloaded_file,
                '/S',  # Silent installation
                f'/D={studio_info["install_dir"]}'  # Installation directory
            ]
            
            result = subprocess.run(install_cmd, timeout=1800)  # 30 minute timeout
            
            if result.returncode == 0:
                self.logger.log("Android Studio installation completed")
                self._add_rollback_action('uninstall_program', 'Android Studio')
                
                # Configure Android SDK environment variables
                sdk_path = os.path.expanduser(r'~\AppData\Local\Android\Sdk')
                self._set_environment_variable('ANDROID_HOME', sdk_path)
                self._set_environment_variable('ANDROID_SDK_ROOT', sdk_path)
                
                # Add Android SDK tools to PATH
                platform_tools = os.path.join(sdk_path, 'platform-tools')
                if os.path.exists(platform_tools):
                    self._add_to_system_path(platform_tools)
                
                return True
            else:
                self.logger.log(f"Android Studio installer failed with code {result.returncode}", "ERROR")
                return False
        
        except subprocess.TimeoutExpired:
            self.logger.log("Android Studio installation timed out", "ERROR")
            return False
        except Exception as e:
            self.logger.log(f"Android Studio installation failed: {str(e)}", "ERROR")
            return False
    
    def _install_java_jdk(self):
        """
        Install Java JDK using the official installer.
        Configures JAVA_HOME environment variable.
        """
        self.logger.log("Installing Java JDK...")
        
        # Check for admin privileges
        if not self.is_admin():
            self.logger.log("Administrator privileges required for Java JDK installation", "ERROR")
            return False
        
        # Download Java JDK installer
        jdk_info = self.download_urls['Java JDK']
        downloaded_file = self._download_file(jdk_info['url'], jdk_info['filename'])
        
        if not downloaded_file:
            return False
        
        try:
            # Run Java JDK installer silently
            self.logger.log("Running Java JDK installer...")
            install_cmd = [
                downloaded_file,
                '/s',  # Silent installation
                f'INSTALLDIR={jdk_info["install_dir"]}'
            ]
            
            result = subprocess.run(install_cmd, timeout=600)  # 10 minute timeout
            
            if result.returncode == 0:
                self.logger.log("Java JDK installation completed")
                self._add_rollback_action('uninstall_program', 'Java JDK')
                
                # Set JAVA_HOME environment variable
                self._set_environment_variable('JAVA_HOME', jdk_info['install_dir'])
                
                # Add Java bin directory to PATH
                java_bin_path = os.path.join(jdk_info['install_dir'], 'bin')
                self._add_to_system_path(java_bin_path)
                
                return True
            else:
                self.logger.log(f"Java JDK installer failed with code {result.returncode}", "ERROR")
                return False
        
        except subprocess.TimeoutExpired:
            self.logger.log("Java JDK installation timed out", "ERROR")
            return False
        except Exception as e:
            self.logger.log(f"Java JDK installation failed: {str(e)}", "ERROR")
            return False
    
    def _install_git(self):
        """
        Install Git for Windows using the official installer.
        Handles silent installation and PATH configuration.
        """
        self.logger.log("Installing Git for Windows...")
        
        # Check for admin privileges
        if not self.is_admin():
            self.logger.log("Administrator privileges required for Git installation", "ERROR")
            return False
        
        # Download Git installer
        git_info = self.download_urls['Git']
        downloaded_file = self._download_file(git_info['url'], git_info['filename'])
        
        if not downloaded_file:
            return False
        
        try:
            # Run Git installer silently with recommended settings
            self.logger.log("Running Git installer...")
            install_cmd = [
                downloaded_file,
                '/VERYSILENT',  # Very silent installation
                '/NORESTART',   # Don't restart after installation
                '/NOCANCEL',    # Don't allow cancellation
                '/SP-',         # Disable "This will install..." message
                '/CLOSEAPPLICATIONS',  # Close applications using files to be updated
                '/RESTARTAPPLICATIONS',  # Restart applications after installation
                f'/DIR={git_info["install_dir"]}',  # Installation directory
                '/COMPONENTS=ext,ext\\shellhere,ext\\guihere,gitlfs,assoc,assoc_sh',  # Components to install
                '/TASKS=desktopicon,quicklaunchicon,addcontextmenufiles,addcontextmenufolders,associateshfiles',  # Tasks
                '/o:PathOption=Cmd',  # Add Git to PATH for command line
                '/o:BashTerminalOption=ConHost',  # Use Windows' default console window
                '/o:EditorOption=Notepad',  # Use Notepad as default editor
                '/o:CRLFOption=CRLFAlways',  # Checkout Windows-style, commit Unix-style line endings
                '/o:BranchOption=BranchAlways',  # Default behavior for git pull
                '/o:PerformanceTweaksFSCache=Enabled',  # Enable file system caching
                '/o:UseCredentialManager=Enabled',  # Enable Git Credential Manager
                '/o:EnableSymlinks=Disabled',  # Disable symbolic links (safer for Windows)
                '/o:EnablePseudoConsoleSupport=Disabled',  # Disable pseudo console support
                '/o:EnableFSMonitor=Disabled'  # Disable FSMonitor
            ]
            
            result = subprocess.run(install_cmd, timeout=600)  # 10 minute timeout
            
            if result.returncode == 0:
                self.logger.log("Git installation completed successfully")
                self._add_rollback_action('uninstall_program', 'Git')
                
                # Verify Git installation by checking if git.exe exists
                git_exe_path = os.path.join(git_info['install_dir'], 'bin', 'git.exe')
                if os.path.exists(git_exe_path):
                    self.logger.log(f"Git executable found at: {git_exe_path}")
                    
                    # Add Git to PATH (installer should do this, but ensure it's there)
                    git_bin_path = os.path.join(git_info['install_dir'], 'bin')
                    self._add_to_system_path(git_bin_path)
                    
                    # Test Git installation
                    try:
                        test_result = subprocess.run([git_exe_path, '--version'], 
                                                   capture_output=True, text=True, timeout=10)
                        if test_result.returncode == 0:
                            self.logger.log(f"Git installation verified: {test_result.stdout.strip()}")
                        else:
                            self.logger.log("Git installation completed but version check failed", "WARNING")
                    except Exception as e:
                        self.logger.log(f"Git installation completed but verification failed: {str(e)}", "WARNING")
                    
                    return True
                else:
                    self.logger.log("Git installation completed but executable not found", "ERROR")
                    return False
            else:
                self.logger.log(f"Git installer failed with code {result.returncode}", "ERROR")
                return False
        
        except subprocess.TimeoutExpired:
            self.logger.log("Git installation timed out", "ERROR")
            return False
        except Exception as e:
            self.logger.log(f"Git installation failed: {str(e)}", "ERROR")
            return False
    
    def _run_flutter_doctor_with_streaming(self, flutter_exe, progress_callback=None):
        """
        Run Flutter doctor with extended timeout and streaming output to logs.
        This method is specifically for Flutter doctor to handle its longer execution time.
        """
        try:
            self.logger.log("Starting Flutter doctor with streaming output...")
            
            if progress_callback:
                progress_callback(92, "Running Flutter doctor (this may take several minutes)...")
            
            # Start Flutter doctor process with streaming
            process = subprocess.Popen(
                [flutter_exe, 'doctor', '-v'],  # Verbose output for more details
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            output_lines = []
            
            # Read output line by line in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    output_lines.append(line)
                    # Log each line to show progress
                    self.logger.log(f"Flutter doctor: {line}")
                    
                    # Update progress callback with current status
                    if progress_callback and line:
                        if "Checking" in line or "Looking" in line:
                            progress_callback(94, f"Flutter doctor: {line[:50]}...")
                        elif "Doctor summary" in line:
                            progress_callback(96, "Flutter doctor: Generating summary...")
            
            # Wait for process to complete (no timeout - let it run as long as needed)
            return_code = process.wait()
            
            # Log final results
            full_output = '\n'.join(output_lines)
            
            if return_code == 0:
                self.logger.log("Flutter doctor completed successfully")
                if progress_callback:
                    progress_callback(98, "Flutter doctor completed successfully")
            else:
                self.logger.log(f"Flutter doctor completed with warnings/errors (exit code: {return_code})", "WARNING")
                if progress_callback:
                    progress_callback(98, f"Flutter doctor completed with warnings (exit code: {return_code})")
            
            # Log summary of issues found (if any)
            if "No issues found" in full_output:
                self.logger.log("Flutter doctor: No issues found - Flutter is ready to use!")
            elif "issues found" in full_output.lower():
                self.logger.log("Flutter doctor found some issues - check logs for details", "WARNING")
            
            return return_code == 0
            
        except Exception as e:
            error_msg = f"Flutter doctor execution failed: {str(e)}"
            self.logger.log(error_msg, "ERROR")
            if progress_callback:
                progress_callback(98, "Flutter doctor failed - check logs")
            return False
    
    def _add_to_system_path(self, path_to_add):
        """
        Add a directory to the system PATH environment variable with verification.
        Modifies system PATH and broadcasts changes to refresh environment.
        """
        try:
            self.logger.log(f"Adding {path_to_add} to system PATH")
            
            # Check for admin privileges before modifying system PATH
            if not self.is_admin():
                self.logger.log("Administrator privileges required for system PATH modification", "ERROR")
                raise PermissionError("Administrator privileges required to modify system PATH")
            
            # Get current PATH from registry (system-wide)
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
                               0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                
                try:
                    current_path, _ = winreg.QueryValueEx(key, 'PATH')
                except FileNotFoundError:
                    current_path = ''
                
                # Check if path is already in PATH
                path_entries = current_path.split(os.pathsep)
                if path_to_add not in path_entries:
                    # Add new path
                    new_path = current_path + os.pathsep + path_to_add if current_path else path_to_add
                    winreg.SetValueEx(key, 'PATH', 0, winreg.REG_EXPAND_SZ, new_path)
                    
                    # Record for rollback
                    self._add_rollback_action('remove_from_path', path_to_add, current_path)
                    
                    self.logger.log(f"Successfully added {path_to_add} to system PATH")
                    
                    # Broadcast environment change to notify all processes
                    self._broadcast_environment_change()
                    
                else:
                    self.logger.log(f"{path_to_add} already in system PATH")
        
        except PermissionError as pe:
            error_msg = f"Permission denied when adding {path_to_add} to PATH: {str(pe)}"
            self.logger.log(error_msg, "ERROR")
            raise PermissionError(error_msg)
        except Exception as e:
            error_msg = f"Failed to add {path_to_add} to PATH: {str(e)}"
            self.logger.log(error_msg, "ERROR")
            raise Exception(error_msg)
    
    def _broadcast_environment_change(self):
        """
        Broadcast environment variable changes to all processes.
        This helps refresh PATH without requiring system restart.
        """
        try:
            import ctypes
            from ctypes import wintypes
            
            # Constants for broadcasting environment changes
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            SMTO_ABORTIFHUNG = 0x0002
            
            # Broadcast the change
            result = ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                "Environment",
                SMTO_ABORTIFHUNG,
                5000,  # 5 second timeout
                None
            )
            
            if result:
                self.logger.log("Successfully broadcast environment change")
            else:
                self.logger.log("Failed to broadcast environment change", "WARNING")
                
        except Exception as e:
            self.logger.log(f"Failed to broadcast environment change: {str(e)}", "WARNING")
    
    def _verify_tool_installation(self, tool_name, command_name, install_dir):
        """
        Verify tool installation by spawning new process to test PATH and fallback to install directory.
        This ensures PATH updates are properly detected even if not immediately available.
        """
        try:
            self.logger.log(f"Verifying {tool_name} installation...")
            
            # Method 1: Try running from PATH in a new process
            path_success = False
            try:
                result = subprocess.run(
                    [command_name, '--version'], 
                    capture_output=True, 
                    text=True, 
                    timeout=30,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                )
                if result.returncode == 0:
                    path_success = True
                    self.logger.log(f"{tool_name} successfully accessible from PATH: {result.stdout.strip()}")
                else:
                    self.logger.log(f"{tool_name} not accessible from PATH (exit code: {result.returncode})")
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
                self.logger.log(f"{tool_name} not accessible from PATH: {str(e)}")
            
            # Method 2: Try running from install directory as fallback
            fallback_success = False
            if not path_success:
                try:
                    if tool_name.lower() == 'flutter':
                        fallback_exe = os.path.join(install_dir, 'bin', 'flutter.bat')
                    elif tool_name.lower() == 'dart':
                        fallback_exe = os.path.join(install_dir, 'bin', 'dart.exe')
                    else:
                        fallback_exe = os.path.join(install_dir, 'bin', f'{command_name}.exe')
                    
                    if os.path.exists(fallback_exe):
                        result = subprocess.run(
                            [fallback_exe, '--version'], 
                            capture_output=True, 
                            text=True, 
                            timeout=30
                        )
                        if result.returncode == 0:
                            fallback_success = True
                            self.logger.log(f"{tool_name} accessible from install directory: {result.stdout.strip()}")
                            self.logger.log(f"NOTE: {tool_name} is installed but PATH may not be refreshed yet. "
                                          f"You may need to restart your terminal or system for PATH changes to take effect.", "WARNING")
                        else:
                            self.logger.log(f"{tool_name} failed from install directory (exit code: {result.returncode})")
                    else:
                        self.logger.log(f"{tool_name} executable not found at {fallback_exe}")
                        
                except Exception as e:
                    self.logger.log(f"Failed to verify {tool_name} from install directory: {str(e)}")
            
            # Report final verification status
            if path_success:
                self.logger.log(f"✅ {tool_name} installation verified - accessible from PATH")
                return True
            elif fallback_success:
                self.logger.log(f"⚠️ {tool_name} installation verified - accessible from install directory only")
                self.logger.log(f"PATH refresh may be needed for full functionality")
                return True
            else:
                self.logger.log(f"❌ {tool_name} installation verification failed")
                return False
                
        except Exception as e:
            self.logger.log(f"Error verifying {tool_name} installation: {str(e)}", "ERROR")
            return False
    
    def _setup_java_jdk(self, install_dir, progress_callback):
        """
        Setup Java JDK after zip extraction.
        Handles directory structure, sets JAVA_HOME, and adds bin to PATH.
        """
        try:
            if progress_callback:
                progress_callback(85, "Setting up Java JDK...")
            
            self.logger.log("Setting up Java JDK installation...")
            
            # Find the actual JDK directory (zip may contain nested folders)
            jdk_root = self._find_jdk_root_directory(install_dir)
            if not jdk_root:
                raise Exception(f"Could not find JDK root directory in {install_dir}")
            
            self.logger.log(f"Found JDK root directory: {jdk_root}")
            
            # Set JAVA_HOME environment variable
            if progress_callback:
                progress_callback(90, "Setting JAVA_HOME...")
            
            self.logger.log(f"Setting JAVA_HOME to: {jdk_root}")
            self._set_environment_variable('JAVA_HOME', jdk_root)
            
            # Add JDK bin directory to PATH
            if progress_callback:
                progress_callback(95, "Adding JDK to PATH...")
            
            java_bin_path = os.path.join(jdk_root, 'bin')
            if os.path.exists(java_bin_path):
                self.logger.log(f"Adding JDK bin to PATH: {java_bin_path}")
                self._add_to_system_path(java_bin_path)
            else:
                raise Exception(f"JDK bin directory not found: {java_bin_path}")
            
            # Verify Java installation
            if progress_callback:
                progress_callback(98, "Verifying Java installation...")
            
            self._verify_java_installation(jdk_root)
            
            self.logger.log("Java JDK setup completed successfully")
            
        except Exception as e:
            self.logger.log(f"Java JDK setup failed: {str(e)}", "ERROR")
            raise
    
    def _find_jdk_root_directory(self, base_dir):
        """
        Find the actual JDK root directory within the extracted files.
        JDK zips often contain nested directories.
        """
        # Check if base_dir itself is the JDK root (contains bin/java.exe)
        if os.path.exists(os.path.join(base_dir, 'bin', 'java.exe')):
            return base_dir
        
        # Look for JDK directory one level down
        try:
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                if os.path.isdir(item_path):
                    # Check if this directory contains bin/java.exe
                    if os.path.exists(os.path.join(item_path, 'bin', 'java.exe')):
                        return item_path
        except Exception as e:
            self.logger.log(f"Error searching for JDK root: {str(e)}")
        
        return None
    
    def _verify_java_installation(self, jdk_root):
        """
        Verify Java installation by testing java and javac commands.
        Handles PATH refresh issues gracefully.
        """
        try:
            self.logger.log("Verifying Java installation...")
            
            # Method 1: Try running from PATH (new process)
            path_success = self._test_java_from_path()
            if path_success:
                self.logger.log("✅ Java JDK verified - accessible from PATH")
                return True
            
            # Method 2: Try running from install directory as fallback
            self.logger.log("Java not accessible from PATH, testing from install directory...")
            
            java_exe = os.path.join(jdk_root, 'bin', 'java.exe')
            javac_exe = os.path.join(jdk_root, 'bin', 'javac.exe')
            
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
                        self.logger.log("✅ Java JDK verified - accessible from install directory")
                        self.logger.log("⚠️ Java is installed but PATH may not be refreshed yet", "WARNING")
                        self.logger.log("You may need to restart your terminal or system for PATH changes to take effect", "WARNING")
                        return True
                    else:
                        self.logger.log(f"Java executable found but failed to run (exit code: {result.returncode})")
                        
                except Exception as e:
                    self.logger.log(f"Failed to verify Java from install directory: {str(e)}")
            else:
                self.logger.log(f"Java executables not found: {java_exe}, {javac_exe}")
            
            self.logger.log("❌ Java JDK installation verification failed")
            return False
            
        except Exception as e:
            self.logger.log(f"Error verifying Java installation: {str(e)}", "ERROR")
            return False
    
    def _test_java_from_path(self):
        """
        Test if Java is accessible from PATH using new process.
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
                result = subprocess.run(
                    ['javac', '--version'], 
                    capture_output=True, 
                    text=True, 
                    timeout=30,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                )
                
                if result.returncode == 0:
                    return True
                else:
                    self.logger.log("Java found in PATH but javac not accessible")
            else:
                self.logger.log("Java not accessible from PATH")
                
        except Exception as e:
            self.logger.log(f"Java PATH test failed: {str(e)}")
        
        return False
    
    def _set_environment_variable(self, var_name, var_value):
        """
        Set a system environment variable.
        Creates or updates the specified environment variable in the registry.
        """
        try:
            self.logger.log(f"Setting environment variable {var_name}={var_value}")
            
            # Check for admin privileges before modifying system environment variables
            if not self.is_admin():
                self.logger.log("Administrator privileges required for system environment variable modification", "ERROR")
                raise PermissionError("Administrator privileges required to modify system environment variables")
            
            # Set system-wide environment variable
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
                               0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                
                # Check if variable already exists for rollback
                try:
                    old_value, _ = winreg.QueryValueEx(key, var_name)
                    self._add_rollback_action('restore_env_var', var_name, old_value)
                except FileNotFoundError:
                    self._add_rollback_action('remove_env_var', var_name)
                
                # Set new value
                winreg.SetValueEx(key, var_name, 0, winreg.REG_EXPAND_SZ, var_value)
                self.logger.log(f"Successfully set {var_name} environment variable")
        
        except PermissionError as pe:
            error_msg = f"Permission denied when setting environment variable {var_name}: {str(pe)}"
            self.logger.log(error_msg, "ERROR")
            raise PermissionError(error_msg)
        except Exception as e:
            error_msg = f"Failed to set environment variable {var_name}: {str(e)}"
            self.logger.log(error_msg, "ERROR")
            raise Exception(error_msg)
    
    def _add_rollback_action(self, action_type, *args):
        """
        Record an action for potential rollback.
        Stores information needed to undo installation changes.
        """
        rollback_action = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'args': args
        }
        
        self.rollback_data.append(rollback_action)
        
        # Save rollback data to file
        try:
            with open(self.rollback_file, 'w') as f:
                json.dump(self.rollback_data, f, indent=2)
        except Exception as e:
            self.logger.log(f"Failed to save rollback data: {str(e)}", "ERROR")
    
    def rollback_changes(self):
        """
        Rollback all installation changes using recorded actions.
        Attempts to restore the system to its pre-installation state.
        """
        self.logger.log("Starting rollback process...")
        
        if not os.path.exists(self.rollback_file):
            self.logger.log("No rollback data found", "WARNING")
            return False
        
        try:
            with open(self.rollback_file, 'r') as f:
                rollback_actions = json.load(f)
            
            # Execute rollback actions in reverse order
            success_count = 0
            total_actions = len(rollback_actions)
            
            for action in reversed(rollback_actions):
                try:
                    action_type = action['action_type']
                    args = action['args']
                    
                    if action_type == 'remove_directory':
                        if os.path.exists(args[0]):
                            shutil.rmtree(args[0])
                            self.logger.log(f"Removed directory: {args[0]}")
                    
                    elif action_type == 'restore_directory':
                        if os.path.exists(args[1]):  # backup exists
                            if os.path.exists(args[0]):  # remove current
                                shutil.rmtree(args[0])
                            shutil.move(args[1], args[0])
                            self.logger.log(f"Restored directory: {args[0]}")
                    
                    elif action_type == 'remove_from_path':
                        self._remove_from_system_path(args[0], args[1])
                    
                    elif action_type == 'restore_env_var':
                        self._set_environment_variable(args[0], args[1])
                    
                    elif action_type == 'remove_env_var':
                        self._remove_environment_variable(args[0])
                    
                    elif action_type == 'uninstall_program':
                        self._uninstall_program(args[0])
                    
                    success_count += 1
                
                except Exception as e:
                    self.logger.log(f"Rollback action failed: {action_type} - {str(e)}", "ERROR")
            
            self.logger.log(f"Rollback completed: {success_count}/{total_actions} actions successful")
            
            # Clean up rollback file
            os.remove(self.rollback_file)
            
            return success_count == total_actions
        
        except Exception as e:
            self.logger.log(f"Rollback process failed: {str(e)}", "ERROR")
            return False
    
    def _remove_from_system_path(self, path_to_remove, original_path):
        """Remove a directory from the system PATH environment variable."""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
                               0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                
                winreg.SetValueEx(key, 'PATH', 0, winreg.REG_EXPAND_SZ, original_path)
                self.logger.log(f"Removed {path_to_remove} from system PATH")
        
        except Exception as e:
            self.logger.log(f"Failed to remove {path_to_remove} from PATH: {str(e)}", "ERROR")
    
    def _remove_environment_variable(self, var_name):
        """Remove a system environment variable."""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
                               0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                
                winreg.DeleteValue(key, var_name)
                self.logger.log(f"Removed environment variable: {var_name}")
        
        except Exception as e:
            self.logger.log(f"Failed to remove environment variable {var_name}: {str(e)}", "ERROR")
    
    def _uninstall_program(self, program_name):
        """
        Attempt to uninstall a program using Windows uninstaller.
        Searches for uninstall strings in the registry.
        """
        try:
            self.logger.log(f"Attempting to uninstall {program_name}")
            
            # Search for uninstall information in registry
            uninstall_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'
            
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, uninstall_key) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                display_name, _ = winreg.QueryValueEx(subkey, 'DisplayName')
                                if program_name.lower() in display_name.lower():
                                    uninstall_string, _ = winreg.QueryValueEx(subkey, 'UninstallString')
                                    
                                    # Run uninstaller
                                    subprocess.run(uninstall_string + ' /S', shell=True, timeout=600)
                                    self.logger.log(f"Uninstalled {program_name}")
                                    return
                            except FileNotFoundError:
                                continue
                    except Exception:
                        continue
            
            self.logger.log(f"Could not find uninstaller for {program_name}", "WARNING")
        
        except Exception as e:
            self.logger.log(f"Failed to uninstall {program_name}: {str(e)}", "ERROR")
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during installation."""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.logger.log("Cleaned up temporary files")
        except Exception as e:
            self.logger.log(f"Failed to clean up temp files: {str(e)}", "ERROR")
