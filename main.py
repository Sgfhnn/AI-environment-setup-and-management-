import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import sys
import os
import ctypes
from datetime import datetime

# Import our custom modules
from system_scanner import SystemScanner
from installer_manager import InstallerManager
from logger import Logger

class FlutterDevSetupGUI:
    """
    Main GUI application for Flutter development environment setup on Windows.
    Provides scanning, installation, and management of Flutter development tools.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Flutter Dev Environment Setup - Phase 1 MVP")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Initialize core components
        self.logger = Logger()
        
        # Debug: Verify module imports and initialization
        self.logger.log("=== APPLICATION INITIALIZATION DEBUG ===", "DEBUG")
        self.logger.log("Logger initialized successfully", "DEBUG")
        
        # Check administrator privileges at startup
        self.is_admin = self._check_admin_privileges()
        self.logger.log(f"Administrator privileges: {'Yes' if self.is_admin else 'No'}", "DEBUG")
        
        try:
            self.scanner = SystemScanner(self.logger)
            self.logger.log("SystemScanner initialized successfully", "DEBUG")
        except Exception as e:
            self.logger.log(f"ERROR: Failed to initialize SystemScanner: {str(e)}", "ERROR")
            raise
        
        try:
            self.installer = InstallerManager(self.logger)
            self.logger.log("InstallerManager initialized successfully", "DEBUG")
        except Exception as e:
            self.logger.log(f"ERROR: Failed to initialize InstallerManager: {str(e)}", "ERROR")
            raise
        
        # Track installation state
        self.scan_results = {}
        self.installation_in_progress = False
        
        # Create GUI components
        self.create_widgets()
        
        # Log application startup
        self.logger.log("Application started successfully")
        self.logger.log("=== END APPLICATION INITIALIZATION DEBUG ===", "DEBUG")
    
    def create_widgets(self):
        """
        Create and arrange all GUI widgets in the main window.
        Uses a structured layout with frames for different sections.
        """
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for responsive design
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title section
        title_label = ttk.Label(main_frame, text="Flutter Development Environment Setup", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Control buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Action buttons with consistent styling
        self.scan_button = ttk.Button(buttons_frame, text="Scan System", 
                                     command=self.start_scan, width=15)
        self.scan_button.grid(row=0, column=0, padx=(0, 10))
        
        self.install_button = ttk.Button(buttons_frame, text="Start Installation", 
                                        command=self.start_installation, width=15)
        self.install_button.grid(row=0, column=1, padx=(0, 10))
        self.install_button.config(state='disabled')  # Initially disabled
        
        self.logs_button = ttk.Button(buttons_frame, text="View Logs", 
                                     command=self.show_logs, width=15)
        self.logs_button.grid(row=0, column=2, padx=(0, 10))
        
        # Rollback button for safety
        self.rollback_button = ttk.Button(buttons_frame, text="Rollback Changes", 
                                         command=self.rollback_installation, width=15)
        self.rollback_button.grid(row=0, column=3)
        self.rollback_button.config(state='disabled')
        
        # Status display area with scrollable content
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        
        # Treeview for displaying tool status with columns
        columns = ("Tool", "Version", "Status", "Path")
        self.status_tree = ttk.Treeview(status_frame, columns=columns, show="headings", height=8)
        
        # Configure column headers and widths
        self.status_tree.heading("Tool", text="Development Tool")
        self.status_tree.heading("Version", text="Installed Version")
        self.status_tree.heading("Status", text="Status")
        self.status_tree.heading("Path", text="Installation Path")
        
        self.status_tree.column("Tool", width=150)
        self.status_tree.column("Version", width=120)
        self.status_tree.column("Status", width=100)
        self.status_tree.column("Path", width=300)
        
        # Add scrollbar for the treeview
        status_scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_tree.yview)
        self.status_tree.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        status_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Progress section for installation tracking
        progress_frame = ttk.LabelFrame(main_frame, text="Installation Progress", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # Progress bar with percentage display
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Progress status label
        self.progress_label = ttk.Label(progress_frame, text="Ready to scan system")
        self.progress_label.grid(row=1, column=0, sticky=tk.W)
        
        # Log display area (initially hidden, shown when "View Logs" is clicked)
        self.log_window = None
        
        # Initialize status display with placeholder data
        self.update_status_display()
        
        # Update window title to show admin status
        admin_status = " (Administrator)" if self.is_admin else " (Standard User)"
        self.root.title(f"Flutter Dev Environment Setup - Phase 1 MVP{admin_status}")
    
    def _check_admin_privileges(self):
        """
        Check if the current process has administrator privileges.
        Returns True if running as administrator, False otherwise.
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _request_admin_privileges(self):
        """
        Request administrator privileges using UAC (User Account Control).
        Restarts the application with elevated permissions if needed.
        """
        if self.is_admin:
            return True
        
        try:
            self.logger.log("Requesting administrator privileges...")
            
            # Show UAC elevation dialog
            result = messagebox.askyesno(
                "Administrator Privileges Required",
                "This operation requires administrator privileges to:\n\n"
                "• Extract files to system directories\n"
                "• Modify system PATH environment variables\n"
                "• Install development tools\n\n"
                "The application will restart with elevated privileges. Continue?"
            )
            
            if not result:
                return False
            
            # Re-run the program with admin privileges
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            
            # Close current instance
            self.root.quit()
            return True
            
        except Exception as e:
            self.logger.log(f"Failed to request admin privileges: {str(e)}", "ERROR")
            messagebox.showerror(
                "Privilege Elevation Failed",
                f"Could not request administrator privileges:\n{str(e)}\n\n"
                "Please run the application as administrator manually."
            )
            return False
    
    def start_scan(self):
        """
        Initiate system scan in a separate thread to prevent GUI freezing.
        Scans for Flutter, Dart, Android Studio, and Java JDK installations.
        """
        if self.installation_in_progress:
            messagebox.showwarning("Scan Blocked", "Cannot scan while installation is in progress.")
            return
        
        # Disable scan button during operation
        self.scan_button.config(state='disabled')
        self.progress_label.config(text="Scanning system...")
        self.progress_var.set(0)
        
        # Run scan in background thread to maintain UI responsiveness
        scan_thread = threading.Thread(target=self._perform_scan, daemon=True)
        scan_thread.start()
    
    def _perform_scan(self):
        """
        Internal method to perform the actual system scan.
        Updates GUI elements from the background thread using thread-safe methods.
        """
        try:
            # Perform comprehensive system scan
            self.scan_results = self.scanner.scan_system()
            
            # Update GUI from main thread (thread-safe)
            self.root.after(0, self._scan_complete)
            
        except Exception as e:
            error_msg = f"Scan failed: {str(e)}"
            self.logger.log(error_msg, "ERROR")
            self.root.after(0, lambda: self._scan_error(error_msg))
    
    def _scan_complete(self):
        """
        Handle scan completion - update GUI with results and enable installation if needed.
        """
        self.progress_var.set(100)
        self.progress_label.config(text="System scan completed")
        self.scan_button.config(state='normal')
        
        # Update status display with scan results
        self.update_status_display()
        
        # Enable installation button if missing tools are detected
        missing_tools = [tool for tool, info in self.scan_results.items() 
                        if not info.get('installed', False)]
        
        if missing_tools:
            self.install_button.config(state='normal')
            self.progress_label.config(text=f"Found {len(missing_tools)} missing tools. Ready to install.")
        else:
            self.progress_label.config(text="All development tools are properly installed!")
        
        self.logger.log("System scan completed successfully")
    
    def _scan_error(self, error_msg):
        """Handle scan errors by updating GUI and showing error message."""
        self.progress_label.config(text="Scan failed - check logs for details")
        self.scan_button.config(state='normal')
        messagebox.showerror("Scan Error", error_msg)
    
    def start_installation(self):
        """
        Begin installation process for missing development tools.
        Shows component selection dialog and handles UAC elevation.
        """
        if not self.scan_results:
            messagebox.showwarning("No Scan Data", "Please scan the system first.")
            return
        
        missing_tools = [tool for tool, info in self.scan_results.items() 
                        if not info.get('installed', False)]
        
        if not missing_tools:
            messagebox.showinfo("Nothing to Install", "All tools are already installed.")
            return
        
        # Show component selection dialog
        selected_tools = self._show_component_selection_dialog(missing_tools)
        
        if not selected_tools:
            return  # User cancelled or selected nothing
        
        # Check for administrator privileges before installation
        if not self.is_admin:
            self.logger.log("Installation requires administrator privileges", "WARNING")
            if not self._request_admin_privileges():
                messagebox.showwarning(
                    "Installation Cancelled", 
                    "Administrator privileges are required to install development tools.\n\n"
                    "Please run the application as administrator or grant UAC elevation when prompted."
                )
                return
            # If we reach here, the app is restarting with admin privileges
            return
        
        # Confirm installation with user
        confirm_msg = f"This will install the following selected tools:\n\n" + "\n".join(selected_tools)
        confirm_msg += "\n\nRunning with administrator privileges. Continue?"
        
        if not messagebox.askyesno("Confirm Installation", confirm_msg):
            return
        
        # Prepare for installation
        self.installation_in_progress = True
        self.install_button.config(state='disabled')
        self.scan_button.config(state='disabled')
        self.rollback_button.config(state='normal')
        
        # Start installation in background thread
        install_thread = threading.Thread(target=self._perform_installation, 
                                         args=(selected_tools,), daemon=True)
        install_thread.start()
    
    def _show_component_selection_dialog(self, missing_tools):
        """
        Show a dialog with checkboxes for selecting which components to install.
        Returns list of selected tools or None if cancelled.
        """
        # Create selection dialog window
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Select Components to Install")
        selection_window.geometry("550x500")
        selection_window.resizable(True, True)
        selection_window.minsize(500, 450)
        selection_window.transient(self.root)
        selection_window.grab_set()
        
        # Center the dialog
        selection_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 125,
            self.root.winfo_rooty() + 50
        ))
        
        selected_tools = []
        checkbox_vars = {}
        
        # Configure grid weights for responsive layout
        selection_window.columnconfigure(0, weight=1)
        selection_window.rowconfigure(0, weight=1)
        
        # Main frame with padding
        main_frame = ttk.Frame(selection_window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # Make checkbox area expandable
        
        # Title
        title_label = ttk.Label(main_frame, text="Select Components to Install", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 15), sticky=tk.W+tk.E)
        
        # Description
        desc_label = ttk.Label(main_frame, 
                              text="Choose which development tools you want to install.\nAll components are selected by default.",
                              justify=tk.CENTER)
        desc_label.grid(row=1, column=0, pady=(0, 20), sticky=tk.W+tk.E)
        
        # Scrollable frame for checkboxes
        checkbox_container = ttk.Frame(main_frame)
        checkbox_container.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        checkbox_container.columnconfigure(0, weight=1)
        checkbox_container.rowconfigure(0, weight=1)
        
        canvas = tk.Canvas(checkbox_container, height=180)
        scrollbar = ttk.Scrollbar(checkbox_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create checkboxes for each missing tool
        for i, tool in enumerate(missing_tools):
            var = tk.BooleanVar(value=True)  # Default to selected
            checkbox_vars[tool] = var
            
            # Tool info from scan results
            tool_info = self.scan_results.get(tool, {})
            
            # Create checkbox frame
            checkbox_frame = ttk.Frame(scrollable_frame)
            checkbox_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Checkbox
            checkbox = ttk.Checkbutton(checkbox_frame, text=tool, variable=var)
            checkbox.pack(side=tk.LEFT)
            
            # Tool description
            descriptions = {
                "Flutter": "Cross-platform UI toolkit for mobile, web, and desktop",
                "Dart": "Programming language optimized for building mobile, desktop, server, and web applications",
                "Android Studio": "Official IDE for Android development with Flutter support",
                "Java JDK": "Java Development Kit required for Android development",
                "Git": "Version control system for tracking changes in source code"
            }
            
            desc_text = descriptions.get(tool, "Development tool")
            desc_label = ttk.Label(checkbox_frame, text=f"  - {desc_text}", 
                                  font=("Arial", 9), foreground="gray")
            desc_label.pack(side=tk.LEFT, padx=(10, 0))
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Selection buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        button_frame.columnconfigure(2, weight=1)  # Add space between button groups
        
        # Select/Deselect all buttons
        def select_all():
            for var in checkbox_vars.values():
                var.set(True)
        
        def deselect_all():
            for var in checkbox_vars.values():
                var.set(False)
        
        select_all_btn = ttk.Button(button_frame, text="Select All", command=select_all)
        select_all_btn.grid(row=0, column=0, padx=(0, 10), sticky=tk.W)
        
        deselect_all_btn = ttk.Button(button_frame, text="Deselect All", command=deselect_all)
        deselect_all_btn.grid(row=0, column=1, sticky=tk.W)
        
        # Action buttons frame
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(20, 0))
        action_frame.columnconfigure(0, weight=1)  # Push buttons to the right
        
        # Result variable
        dialog_result = {"cancelled": True}
        
        def on_install():
            selected = [tool for tool, var in checkbox_vars.items() if var.get()]
            if not selected:
                messagebox.showwarning("No Selection", "Please select at least one component to install.")
                return
            
            dialog_result["cancelled"] = False
            dialog_result["selected"] = selected
            selection_window.destroy()
        
        def on_cancel():
            dialog_result["cancelled"] = True
            selection_window.destroy()
        
        # Install and Cancel buttons with proper spacing
        cancel_btn = ttk.Button(action_frame, text="Cancel", command=on_cancel, width=12)
        cancel_btn.grid(row=0, column=1, padx=(10, 0), sticky=tk.E)
        
        install_btn = ttk.Button(action_frame, text="Install Selected", command=on_install, width=15)
        install_btn.grid(row=0, column=2, padx=(10, 0), sticky=tk.E)
        
        # Handle window close
        selection_window.protocol("WM_DELETE_WINDOW", on_cancel)
        
        # Wait for dialog to close
        selection_window.wait_window()
        
        # Return selected tools or None if cancelled
        if dialog_result["cancelled"]:
            return None
        else:
            return dialog_result["selected"]
    
    def _perform_installation(self, tools_to_install):
        """
        Internal method to handle the installation process with real-time progress updates.
        Manages downloads, installations, and environment configuration with proper error handling.
        """
        try:
            total_tools = len(tools_to_install)
            
            for i, tool in enumerate(tools_to_install):
                # Create progress callback for this tool
                def tool_progress_callback(progress, status, tool_index=i, tool_name=tool):
                    # Calculate overall progress across all tools
                    base_progress = (tool_index / total_tools) * 100
                    tool_progress = progress / total_tools
                    overall_progress = base_progress + tool_progress
                    
                    # Update GUI from main thread
                    self.root.after(0, lambda: self._update_install_progress(overall_progress, status))
                
                # Initial progress update
                self.root.after(0, lambda t=tool: self._update_install_progress((i / total_tools) * 100, f"Starting {t} installation..."))
                
                try:
                    # Perform installation for current tool with progress callback
                    success = self.installer.install_tool(tool, self.scan_results[tool], tool_progress_callback)
                    
                    if not success:
                        error_msg = f"Failed to install {tool}"
                        self.logger.log(error_msg, "ERROR")
                        self.root.after(0, lambda msg=error_msg: self._installation_error(msg))
                        return
                        
                except PermissionError as pe:
                    error_msg = f"Permission denied during {tool} installation: {str(pe)}"
                    self.logger.log(error_msg, "ERROR")
                    self.root.after(0, lambda msg=error_msg: self._installation_permission_error(msg))
                    return
                except Exception as tool_e:
                    error_msg = f"Failed to install {tool}: {str(tool_e)}"
                    self.logger.log(error_msg, "ERROR")
                    self.root.after(0, lambda msg=error_msg: self._installation_error(msg))
                    return
            
            # Installation completed successfully
            self.root.after(0, self._installation_complete)
            
        except Exception as e:
            error_msg = f"Installation failed: {str(e)}"
            self.logger.log(error_msg, "ERROR")
            self.root.after(0, lambda: self._installation_error(error_msg))
    
    def _update_install_progress(self, progress, status_text):
        """Update installation progress bar and status text."""
        self.progress_var.set(progress)
        self.progress_label.config(text=status_text)
    
    def _installation_complete(self):
        """Handle successful installation completion."""
        self.progress_var.set(100)
        self.progress_label.config(text="Installation completed successfully!")
        self.installation_in_progress = False
        
        # Re-enable buttons
        self.scan_button.config(state='normal')
        self.install_button.config(state='disabled')
        
        # Suggest rescanning to verify installation
        messagebox.showinfo("Installation Complete", 
                           "All tools have been installed successfully!\n\nPlease restart your system and run a new scan to verify the installation.")
        
        self.logger.log("Installation process completed successfully")
    
    def _installation_error(self, error_msg):
        """Handle installation errors."""
        self.progress_label.config(text="Installation failed - check logs")
        self.installation_in_progress = False
        
        # Re-enable buttons
        self.scan_button.config(state='normal')
        self.install_button.config(state='normal')
        
        messagebox.showerror("Installation Error", error_msg)
    
    def _installation_permission_error(self, error_msg):
        """Handle permission-related installation errors with specific guidance."""
        self.progress_label.config(text="Installation failed - permission denied")
        self.installation_in_progress = False
        
        # Re-enable buttons
        self.scan_button.config(state='normal')
        self.install_button.config(state='normal')
        
        # Show specific permission error dialog
        messagebox.showerror(
            "Permission Denied", 
            f"{error_msg}\n\n"
            "This error typically occurs when:\n"
            "• The application is not running as administrator\n"
            "• System directories are write-protected\n"
            "• Antivirus software is blocking file operations\n\n"
            "Solutions:\n"
            "1. Right-click the application and select 'Run as administrator'\n"
            "2. Temporarily disable antivirus real-time protection\n"
            "3. Check Windows Defender exclusions for the installation directories"
        )
    
    def rollback_installation(self):
        """
        Rollback recent installation changes for system recovery.
        Uses logged installation steps to reverse changes safely.
        """
        if not messagebox.askyesno("Confirm Rollback", 
                                  "This will attempt to undo recent installation changes. Continue?"):
            return
        
        try:
            success = self.installer.rollback_changes()
            if success:
                messagebox.showinfo("Rollback Complete", "Installation changes have been rolled back.")
                self.rollback_button.config(state='disabled')
            else:
                messagebox.showerror("Rollback Failed", "Could not complete rollback. Check logs for details.")
        except Exception as e:
            messagebox.showerror("Rollback Error", f"Rollback failed: {str(e)}")
    
    def show_logs(self):
        """
        Display application logs in a separate window.
        Shows detailed information about scans, installations, and errors.
        """
        if self.log_window and self.log_window.winfo_exists():
            self.log_window.lift()
            return
        
        # Create log viewer window
        self.log_window = tk.Toplevel(self.root)
        self.log_window.title("Application Logs")
        self.log_window.geometry("700x500")
        
        # Log display with scrolling
        log_frame = ttk.Frame(self.log_window, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=80, height=25)
        log_text.pack(fill=tk.BOTH, expand=True)
        
        # Load and display logs
        try:
            logs = self.logger.get_logs()
            log_text.insert(tk.END, logs)
            log_text.config(state='disabled')  # Make read-only
        except Exception as e:
            log_text.insert(tk.END, f"Error loading logs: {str(e)}")
    
    def update_status_display(self):
        """
        Update the status tree view with current scan results.
        Shows installation status, versions, and paths for each tool.
        """
        # Clear existing items
        for item in self.status_tree.get_children():
            self.status_tree.delete(item)
        
        # Define expected tools for Flutter development
        expected_tools = ["Flutter", "Dart", "Android Studio", "Java JDK", "Git"]
        
        if not self.scan_results:
            # Show placeholder data when no scan has been performed
            for tool in expected_tools:
                self.status_tree.insert("", "end", values=(tool, "Unknown", "Not Scanned", "Unknown"))
        else:
            # Display actual scan results
            for tool in expected_tools:
                if tool in self.scan_results:
                    info = self.scan_results[tool]
                    status = "✅ Installed" if info.get('installed', False) else "❌ Missing"
                    version = info.get('version', 'Unknown')
                    path = info.get('path', 'Not Found')
                else:
                    status = "❌ Missing"
                    version = "Not Found"
                    path = "Not Found"
                
                self.status_tree.insert("", "end", values=(tool, version, status, path))


def main():
    """
    Application entry point. Creates and runs the main GUI application.
    Handles any startup errors gracefully.
    """
    try:
        # Create main window
        root = tk.Tk()
        
        # Initialize application
        app = FlutterDevSetupGUI(root)
        
        # Start GUI event loop
        root.mainloop()
        
    except Exception as e:
        # Handle critical startup errors
        error_msg = f"Failed to start application: {str(e)}"
        print(error_msg)
        
        # Try to show error dialog if possible
        try:
            messagebox.showerror("Startup Error", error_msg)
        except:
            pass  # GUI might not be available
        
        sys.exit(1)


if __name__ == "__main__":
    main()
