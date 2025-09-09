import os
import logging
from datetime import datetime
from pathlib import Path
from resource_path import get_app_data_dir

class Logger:
    """
    Handles application logging with multiple levels and file output.
    Provides centralized logging for system scanning, installations, and errors.
    """
    
    def __init__(self, log_dir=None):
        """
        Initialize logger with file and console output.
        Creates log directory and sets up rotating log files.
        """
        # Set up log directory
        if log_dir is None:
            # Use app data directory for logs (PyInstaller compatible)
            log_dir = Path(get_app_data_dir()) / "logs"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = os.path.join(log_dir, f'flutter_setup_{timestamp}.log')
        
        # Set up Python logging
        self.logger = logging.getLogger('FlutterDevSetup')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Create file handler with detailed formatting
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create detailed formatter for file logs
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create simple formatter for console
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Log initialization
        self.log("Logger initialized successfully")
        self.log(f"Log file: {self.log_file}")
    
    def log(self, message, level="INFO"):
        """
        Log a message with specified level.
        Supports INFO, WARNING, ERROR, and DEBUG levels.
        """
        # Normalize level to uppercase
        level = level.upper()
        
        try:
            if level == "DEBUG":
                self.logger.debug(message)
            elif level == "INFO":
                self.logger.info(message)
            elif level == "WARNING":
                self.logger.warning(message)
            elif level == "ERROR":
                self.logger.error(message)
            else:
                # Default to INFO for unknown levels
                self.logger.info(f"[{level}] {message}")
        
        except Exception as e:
            # Fallback logging if main logger fails
            print(f"Logging error: {e}")
            print(f"Original message: [{level}] {message}")
    
    def log_system_info(self, system_info):
        """
        Log detailed system information for troubleshooting.
        Records OS version, architecture, and hardware details.
        """
        self.log("=== SYSTEM INFORMATION ===")
        
        for key, value in system_info.items():
            if isinstance(value, dict):
                self.log(f"{key}:")
                for sub_key, sub_value in value.items():
                    self.log(f"  {sub_key}: {sub_value}")
            else:
                self.log(f"{key}: {value}")
        
        self.log("=== END SYSTEM INFORMATION ===")
    
    def log_scan_results(self, scan_results):
        """
        Log comprehensive scan results for all development tools.
        Records installation status, versions, and paths.
        """
        self.log("=== SCAN RESULTS ===")
        
        for tool, info in scan_results.items():
            self.log(f"{tool}:")
            for key, value in info.items():
                self.log(f"  {key}: {value}")
            self.log("")  # Empty line for readability
        
        self.log("=== END SCAN RESULTS ===")
    
    def log_installation_start(self, tools_to_install):
        """
        Log the beginning of installation process.
        Records which tools will be installed and system state.
        """
        self.log("=== INSTALLATION STARTED ===")
        self.log(f"Tools to install: {', '.join(tools_to_install)}")
        self.log(f"Installation timestamp: {datetime.now().isoformat()}")
        
        # Log current PATH for reference
        current_path = os.environ.get('PATH', '')
        self.log(f"Current PATH length: {len(current_path)} characters")
        
        # Log available disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage('C:')
            free_gb = free / (1024**3)
            self.log(f"Available disk space: {free_gb:.2f} GB")
        except Exception as e:
            self.log(f"Could not check disk space: {e}", "WARNING")
    
    def log_installation_step(self, tool, step, status="IN_PROGRESS"):
        """
        Log individual installation steps for detailed tracking.
        Helps with troubleshooting failed installations.
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log(f"[{timestamp}] {tool} - {step}: {status}")
    
    def log_installation_complete(self, success_count, total_count):
        """
        Log installation completion summary.
        Records success rate and final system state.
        """
        self.log("=== INSTALLATION COMPLETED ===")
        self.log(f"Successfully installed: {success_count}/{total_count} tools")
        
        if success_count == total_count:
            self.log("All installations completed successfully!", "INFO")
        else:
            failed_count = total_count - success_count
            self.log(f"{failed_count} installations failed - check logs for details", "WARNING")
        
        self.log(f"Completion timestamp: {datetime.now().isoformat()}")
    
    def log_environment_changes(self, changes):
        """
        Log environment variable and PATH changes.
        Critical for rollback functionality and troubleshooting.
        """
        self.log("=== ENVIRONMENT CHANGES ===")
        
        for change in changes:
            change_type = change.get('type', 'unknown')
            
            if change_type == 'path_addition':
                self.log(f"Added to PATH: {change['path']}")
            elif change_type == 'env_var_set':
                self.log(f"Set environment variable: {change['name']}={change['value']}")
            elif change_type == 'env_var_removed':
                self.log(f"Removed environment variable: {change['name']}")
            else:
                self.log(f"Environment change: {change}")
        
        self.log("=== END ENVIRONMENT CHANGES ===")
    
    def log_error_details(self, error, context=""):
        """
        Log detailed error information for debugging.
        Includes stack trace and context information.
        """
        import traceback
        
        self.log("=== ERROR DETAILS ===", "ERROR")
        
        if context:
            self.log(f"Context: {context}", "ERROR")
        
        self.log(f"Error type: {type(error).__name__}", "ERROR")
        self.log(f"Error message: {str(error)}", "ERROR")
        
        # Log stack trace if available
        tb_str = traceback.format_exc()
        if tb_str and tb_str != "NoneType: None\n":
            self.log("Stack trace:", "ERROR")
            for line in tb_str.split('\n'):
                if line.strip():
                    self.log(f"  {line}", "ERROR")
        
        self.log("=== END ERROR DETAILS ===", "ERROR")
    
    def log_rollback_action(self, action_type, details, success=True):
        """
        Log rollback actions for audit trail.
        Records what was undone and whether it succeeded.
        """
        status = "SUCCESS" if success else "FAILED"
        self.log(f"ROLLBACK [{status}]: {action_type} - {details}")
    
    def get_logs(self):
        """
        Retrieve all logged content from the current log file.
        Used by the GUI to display logs to the user.
        """
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return "No log file found."
        
        except Exception as e:
            return f"Error reading log file: {str(e)}"
    
    def get_recent_logs(self, lines=50):
        """
        Get the most recent log entries.
        Useful for displaying current status without overwhelming the user.
        """
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    return ''.join(recent_lines)
            else:
                return "No log file found."
        
        except Exception as e:
            return f"Error reading recent logs: {str(e)}"
    
    def cleanup_old_logs(self, keep_days=30):
        """
        Clean up old log files to prevent disk space issues.
        Keeps logs for the specified number of days.
        """
        try:
            cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
            
            for log_file in Path(self.log_dir).glob('flutter_setup_*.log'):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    self.log(f"Cleaned up old log file: {log_file.name}")
        
        except Exception as e:
            self.log(f"Error cleaning up old logs: {str(e)}", "WARNING")
    
    def export_logs(self, export_path):
        """
        Export current logs to a specified location.
        Useful for sharing logs for support purposes.
        """
        try:
            if os.path.exists(self.log_file):
                shutil.copy2(self.log_file, export_path)
                self.log(f"Logs exported to: {export_path}")
                return True
            else:
                self.log("No log file to export", "WARNING")
                return False
        
        except Exception as e:
            self.log(f"Failed to export logs: {str(e)}", "ERROR")
            return False
    
    def close(self):
        """
        Close the logger and clean up resources.
        Should be called when the application exits.
        """
        self.log("Logger shutting down")
        
        # Close all handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
