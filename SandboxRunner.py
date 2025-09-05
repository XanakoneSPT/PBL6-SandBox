"""
VM-based Sandbox Runner for Secure Code Analysis

This module provides a secure sandbox environment for executing and analyzing
potentially untrusted code using VMware virtual machines. It supports multiple
programming languages and provides system call tracing capabilities.

Author: Minh Duc
Version: 1.0.0
Requirements: VMware Workstation/Player, vmrun utility, Kali Linux VM with VMware Tools
"""

import os
import subprocess
import logging
from pathlib import Path, PurePosixPath
from typing import Optional, List, Tuple, Dict


class SandboxError(Exception):
    """Base exception for sandbox operations"""
    pass


class VMControlError(SandboxError):
    """Exception raised for VM control operations"""
    pass


class FileOperationError(SandboxError):
    """Exception raised for file operations"""
    pass


class ExecutionError(SandboxError):
    """Exception raised for code execution operations"""
    pass


class SandboxRunner:
    """
    VM-based sandbox for secure code execution and analysis.
    
    This class provides a secure environment for executing potentially dangerous
    code by running it in an isolated virtual machine that can be easily reset
    to a clean state.
    
    Attributes:
        vm_path (str): Path to the VMware .vmx file
        guest_user (str): Username for guest OS authentication
        guest_pass (str): Password for guest OS authentication
        base_snapshot (str): Name of the clean snapshot for rollback
        base_dir (str): Working directory inside the guest OS
    """
    
    # Supported file extensions and their interpreters/compilers
    INTERPRETERS: Dict[str, str] = {
        ".py": "python3",
        ".js": "node",
        ".sh": "bash",
        ".rb": "ruby",
        ".pl": "perl",
        ".php": "php",
    }
    
    COMPILERS: Dict[str, str] = {
        ".c": "gcc",
        ".cpp": "g++",
        ".java": "javac",
        ".go": "go",
    }
    
    def __init__(
        self,
        vm_path: str = "E:\\package\\VMWare os\\kali-linux-2025.2-vmware-amd64.vmwarevm\\kali-linux-2025.2-vmware-amd64.vmx",
        guest_user: str = "kali",
        guest_pass: str = "kali",
        base_snapshot: str = "CleanSnapshot1",
        base_dir: str = "/home/kali/SandboxAnalysis",
        timeout: int = 100  # seconds ~ 1.5 minutes
    ):
        """
        Initialize the SandboxRunner.
        
        Args:
            vm_path: Path to the VMware .vmx configuration file
            guest_user: Username for guest OS authentication
            guest_pass: Password for guest OS authentication
            base_snapshot: Name of the snapshot to rollback to
            base_dir: Working directory inside the guest OS
            timeout: Default timeout for operations in seconds
            
        Raises:
            FileNotFoundError: If the VM path doesn't exist
            VMControlError: If vmrun utility is not available
        """
        self.vm_path = Path(vm_path)
        self.guest_user = guest_user
        self.guest_pass = guest_pass
        self.base_snapshot = base_snapshot
        self.base_dir = base_dir
        self.timeout = timeout
        
        # Validate VM path
        if not self.vm_path.exists():
            raise FileNotFoundError(f"VM configuration file not found: {vm_path}")
        
        # Check if vmrun is available
        if not self._check_vmrun_available():
            raise VMControlError("vmrun utility not found. Please install VMware Workstation/Player.")
        
        # Setup logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _check_vmrun_available(self) -> bool:
        """Check if vmrun utility is available in PATH"""
        try:
            subprocess.run(["vmrun"], capture_output=True, check=False)
            return True
        except FileNotFoundError:
            return False

    def _run_vmrun(self, *args, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """
        Execute vmrun command with error handling.
        
        Args:
            *args: Arguments to pass to vmrun
            timeout: Operation timeout in seconds
            
        Returns:
            subprocess.CompletedProcess: Command execution result
            
        Raises:
            VMControlError: If vmrun command fails
        """
        cmd = [
            "vmrun",
            "-T", "ws",  # VMware Workstation
            "-gu", self.guest_user,
            "-gp", self.guest_pass,
        ] + list(args)
        
        self.logger.info(f"Executing: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                check=True
            )
            
            if result.stdout:
                self.logger.debug(f"STDOUT: {result.stdout}")
            if result.stderr:
                self.logger.debug(f"STDERR: {result.stderr}")
                
            return result
            
        except subprocess.CalledProcessError as e:
            error_msg = f"vmrun command failed: {e.stderr or e.stdout or str(e)}"
            self.logger.error(error_msg)
            raise VMControlError(error_msg) from e
        
        except subprocess.TimeoutExpired as e:
            error_msg = f"vmrun command timed out after {timeout or self.timeout}s"
            self.logger.error(error_msg)
            raise VMControlError(error_msg) from e

    # ============ VM Control Methods ============

    def start_vm(self, gui: bool = False) -> None:
        """
        Start the virtual machine.
        
        Args:
            gui: Whether to start with GUI (default: False for headless)
            
        Raises:
            VMControlError: If VM fails to start
        """
        self.logger.info("Starting virtual machine...")
        gui_option = "gui" if gui else "nogui"
        self._run_vmrun("start", str(self.vm_path), gui_option)
        self.logger.info("Virtual machine started successfully")

    def stop_vm(self, force: bool = False) -> None:
        """
        Stop the virtual machine.
        
        Args:
            force: Whether to force shutdown (default: False for soft shutdown)
            
        Raises:
            VMControlError: If VM fails to stop
        """
        self.logger.info("Stopping virtual machine...")
        stop_type = "hard" if force else "soft"
        self._run_vmrun("stop", str(self.vm_path), stop_type)
        self.logger.info("Virtual machine stopped successfully")

    def rollback_vm(self, snapshot_name: Optional[str] = None) -> None:
        """
        Rollback VM to a clean snapshot.
        
        Args:
            snapshot_name: Name of snapshot to rollback to (uses base_snapshot if None)
            
        Raises:
            VMControlError: If rollback fails
        """
        snapshot = snapshot_name or self.base_snapshot
        self.logger.info(f"Rolling back to snapshot: {snapshot}")
        self._run_vmrun("revertToSnapshot", str(self.vm_path), snapshot)
        self.logger.info("Rollback completed successfully")

    def create_snapshot(self, snapshot_name: str, description: str = "") -> None:
        """
        Create a new snapshot of the current VM state.
        
        Args:
            snapshot_name: Name for the new snapshot
            description: Optional description for the snapshot
            
        Raises:
            VMControlError: If snapshot creation fails
        """
        self.logger.info(f"Creating snapshot: {snapshot_name}")
        self._run_vmrun("snapshot", str(self.vm_path), snapshot_name)
        self.logger.info("Snapshot created successfully")

    def ensure_guest_directory(self, directory: str) -> None:
        """
        Ensure directory exists in guest OS.
        
        Args:
            directory: Path to directory in guest OS
            
        Raises:
            VMControlError: If directory creation fails
        """
        self.logger.debug(f"Creating directory in guest: {directory}")
        try:
            self._run_vmrun("runProgramInGuest", str(self.vm_path), 
                           "/bin/mkdir", "-p", directory)
        except VMControlError:
            # Directory might already exist, which is fine
            pass

    # ============ File Operations ============

    def copy_to_vm(self, src: str, dest: str) -> None:
        """
        Copy file from host to guest VM.

        Args:
            src: Source file path on host
            dest: Destination file path in guest (relative to self.base_dir or absolute Linux path)

        Raises:
            FileOperationError: If copy operation fails
        """
        # Convert source to absolute host path
        src_path = Path(src).resolve()
        if not src_path.exists():
            raise FileOperationError(f"Source file not found: {src_path}")

        # Build guest absolute path in Linux-style
        guest_dest_path = PurePosixPath(self.base_dir) / PurePosixPath(dest)
        guest_dest_dir = guest_dest_path.parent

        # Create destination directory in guest if needed
        if str(guest_dest_dir) not in (".", "/"):
            try:
                self.logger.info(f"Creating directory in guest: {guest_dest_dir}")
                self._run_vmrun(
                    "runProgramInGuest",
                    str(self.vm_path),
                    "/bin/mkdir",
                    "-p",
                    str(guest_dest_dir)  # convert PurePosixPath -> str
                )
            except VMControlError as e:
                raise FileOperationError(f"Failed to create directory in guest: {e}") from e

        self.logger.info(f"Copying {src_path} to {guest_dest_path}")

        # Copy file to guest
        try:
            self._run_vmrun(
                "copyFileFromHostToGuest",
                str(self.vm_path),
                str(src_path),
                str(guest_dest_path)
            )
            self.logger.info("File copied successfully")
        except VMControlError as e:
            raise FileOperationError(f"Failed to copy file to VM: {e}") from e
        
    def copy_from_vm(self, src: str, dest: str) -> None:
        """
        Copy file from guest VM to host.
        
        Args:
            src: Source file path in guest (relative to self.base_dir or absolute Linux path)
            dest: Destination file path on host
            
        Raises:
            FileOperationError: If copy operation fails
        """
        # Ensure host destination directory exists
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build guest source path using PurePosixPath for Linux compatibility
        if src.startswith("/"):
            guest_src_path = PurePosixPath(src)
        else:
            guest_src_path = PurePosixPath(self.base_dir) / PurePosixPath(src)
        
        self.logger.info(f"Copying {guest_src_path} to {dest_path}")
        
        try:
            self._run_vmrun("copyFileFromGuestToHost", str(self.vm_path),
                        str(guest_src_path), str(dest_path))
            self.logger.info("File copied successfully")
        except VMControlError as e:
            raise FileOperationError(f"Failed to copy file from VM: {e}") from e

    # ============ Code Analysis Methods ============

    def detect_language(self, file_path: str) -> Tuple[Optional[str], str, bool]:
        """
        Detect programming language and execution method for a file.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            Tuple of (interpreter/compiler, file_extension, needs_compilation)
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in self.INTERPRETERS:
            return self.INTERPRETERS[file_ext], file_ext, False
        elif file_ext in self.COMPILERS:
            return self.COMPILERS[file_ext], file_ext, True
        else:
            return None, file_ext, False

    def compile_code(self, source_path: str) -> str:
        """
        Compile source code in the guest VM.
        
        Args:
            source_path: Path to source file in guest
            
        Returns:
            Path to compiled executable
            
        Raises:
            ExecutionError: If compilation fails
        """
        _, ext, _ = self.detect_language(source_path)
        
        try:
            if ext == ".c":
                exe_path = source_path.replace(".c", "_compiled")
                self._run_vmrun("runProgramInGuest", str(self.vm_path),
                               "/usr/bin/gcc", source_path, "-o", exe_path)
                return exe_path
                
            elif ext == ".cpp":
                exe_path = source_path.replace(".cpp", "_compiled")
                self._run_vmrun("runProgramInGuest", str(self.vm_path),
                               "/usr/bin/g++", source_path, "-o", exe_path)
                return exe_path
                
            elif ext == ".java":
                self._run_vmrun("runProgramInGuest", str(self.vm_path),
                               "/usr/bin/javac", source_path)
                return source_path.replace(".java", "")
                
            elif ext == ".go":
                exe_path = source_path.replace(".go", "_compiled")
                self._run_vmrun("runProgramInGuest", str(self.vm_path),
                               "/usr/bin/go", "build", "-o", exe_path, source_path)
                return exe_path
                
            else:
                raise ExecutionError(f"Compilation not supported for {ext}")
                
        except VMControlError as e:
            raise ExecutionError(f"Compilation failed: {e}") from e

    def execute_code(self, file_path: str, args: List[str] = None, 
                    working_dir: Optional[str] = None) -> None:
        """
        Execute code file in the guest VM.
        
        Args:
            file_path: Path to code file in guest
            args: Command line arguments for the program
            working_dir: Working directory for execution
            
        Raises:
            ExecutionError: If execution fails
        """
        args = args or []
        interpreter, ext, needs_compilation = self.detect_language(file_path)
        
        if not interpreter and not needs_compilation:
            raise ExecutionError(f"Unsupported file type: {ext}")
        
        self.logger.info(f"Executing {file_path} with args: {args}")
        
        try:
            # Change to working directory if specified
            if working_dir:
                # This would need to be implemented with a shell command
                # For now, we assume execution happens in the file's directory
                pass
            
            if needs_compilation:
                compiled_path = self.compile_code(file_path)
                if ext == ".java":
                    # Java needs special handling
                    class_name = Path(compiled_path).name
                    self._run_vmrun("runProgramInGuest", str(self.vm_path),
                                   "/usr/bin/java", class_name, *args)
                else:
                    self._run_vmrun("runProgramInGuest", str(self.vm_path),
                                   compiled_path, *args)
            else:
                self._run_vmrun("runProgramInGuest", str(self.vm_path),
                               interpreter, file_path, *args)
                               
            self.logger.info("Execution completed successfully")
            
        except VMControlError as e:
            raise ExecutionError(f"Code execution failed: {e}") from e

    def analyze_with_strace(self, file_path: str, log_file: str = "syscall_log.txt",
                       args: List[str] = None) -> str:
        """
        Execute code with system call tracing using strace.
        
        Args:
            file_path: Path to code file in guest
            log_file: Name of log file for strace output
            args: Command line arguments for the program
            
        Returns:
            Path to the strace log file in guest
            
        Raises:
            ExecutionError: If strace analysis fails
        """
        args = args or []
        interpreter, ext, needs_compilation = self.detect_language(file_path)
        
        if not interpreter and not needs_compilation:
            raise ExecutionError(f"Unsupported file type for strace: {ext}")
        
        # Use PurePosixPath to ensure Linux-compatible path with /
        log_path = str(PurePosixPath(self.base_dir) / PurePosixPath(log_file))
        file_path = str(PurePosixPath(self.base_dir) / PurePosixPath(file_path))
        
        self.logger.info(f"Analyzing {file_path} with strace, logging to {log_path}")
        
        try:
            cmd = ["/usr/bin/strace", "-f", "-o", log_path]
            
            if needs_compilation:
                compiled_path = self.compile_code(file_path)
                if ext == ".java":
                    cmd.extend(["java", Path(compiled_path).name])
                else:
                    cmd.append(compiled_path)
            else:
                cmd.extend([interpreter, file_path])
            
            cmd.extend(args)
            
            self._run_vmrun("runProgramInGuest", str(self.vm_path), *cmd)
            self.logger.info("Strace analysis completed successfully")
            
            return log_path
            
        except VMControlError as e:
            raise ExecutionError(f"Strace analysis failed: {e}") from e

    def run_custom_tracker(self, tracker_source: str, target_file: str,
                          args: List[str] = None) -> None:
        """
        Compile and run a custom C tracker to monitor another program.
        
        Args:
            tracker_source: Path to C source file of the tracker
            target_file: Path to file to be tracked
            args: Arguments for the target program
            
        Raises:
            ExecutionError: If tracker execution fails
        """
        args = args or []
        
        # Compile the tracker
        tracker_binary = self.compile_code(tracker_source)
        
        # Determine target execution method
        interpreter, ext, needs_compilation = self.detect_language(target_file)
        
        if not interpreter and not needs_compilation:
            raise ExecutionError(f"Unsupported target file type: {ext}")
        
        self.logger.info(f"Running tracker {tracker_binary} on {target_file}")
        
        try:
            cmd = [tracker_binary]
            
            if needs_compilation:
                compiled_target = self.compile_code(target_file)
                if ext == ".java":
                    cmd.extend(["java", Path(compiled_target).name])
                else:
                    cmd.append(compiled_target)
            else:
                cmd.extend([interpreter, target_file])
            
            cmd.extend(args)
            
            self._run_vmrun("runProgramInGuest", str(self.vm_path), *cmd)
            self.logger.info("Custom tracker execution completed")
            
        except VMControlError as e:
            raise ExecutionError(f"Custom tracker execution failed: {e}") from e

    # ============ Utility Methods ============

    def cleanup(self) -> None:
        """
        Clean up sandbox environment.
        Rollback to clean state and optionally stop VM.
        """
        self.logger.info("Cleaning up sandbox environment...")
        try:
            self.rollback_vm()
            self.logger.info("Sandbox cleanup completed")
        except VMControlError as e:
            self.logger.error(f"Cleanup failed: {e}")

    def get_vm_info(self) -> Dict[str, str]:
        """
        Get information about the VM state.
        
        Returns:
            Dictionary containing VM information
        """
        try:
            result = self._run_vmrun("list")
            running = str(self.vm_path) in result.stdout
            
            return {
                "vm_path": str(self.vm_path),
                "status": "running" if running else "stopped",
                "base_snapshot": self.base_snapshot,
                "guest_user": self.guest_user,
                "base_dir": self.base_dir
            }
        except VMControlError:
            return {
                "vm_path": str(self.vm_path),
                "status": "unknown",
                "base_snapshot": self.base_snapshot,
                "guest_user": self.guest_user,
                "base_dir": self.base_dir
            }

    def __enter__(self):
        """Context manager entry"""
        self.start_vm()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.cleanup()
