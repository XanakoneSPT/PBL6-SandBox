import os
import subprocess
import logging
from pathlib import Path, PurePosixPath
from typing import Optional, List, Tuple, Dict


class SandboxError(Exception):
    """Base exception for sandbox operations."""
    pass


class VMControlError(SandboxError):
    """Exception for VM control operations."""
    pass


class FileOperationError(SandboxError):
    """Exception for file operations."""
    pass


class ExecutionError(SandboxError):
    """Exception for code execution operations."""
    pass


class SandboxRunner:
    """Manages a VMware-based sandbox for secure code execution and analysis."""

    # Supported file extensions and their interpreters/compilers
    _INTERPRETERS = {
        ".py": "python3",
        ".js": "node",
        ".sh": "bash",
        ".rb": "ruby",
        ".pl": "perl",
        ".php": "php",
    }

    _COMPILERS = {
        ".c": "gcc",
        ".cpp": "g++",
        ".java": "javac",
        ".go": "go",
    }

    # Document file types that can be analyzed but not executed
    _DOCUMENT_TYPES = {
        ".pdf": "pdf",
        ".doc": "doc",
        ".docx": "docx",
        ".txt": "txt",
        ".rtf": "rtf",
    }

    def __init__(
        self,
        vm_path: str = "E:\\Downloads\\kali-linux-2025.2-vmware-amd64.vmwarevm\\kali-linux-2025.2-vmware-amd64.vmx",
        guest_user: str = "kali",
        guest_pass: str = "kali",
        base_snapshot: str = "CleanSnapshot1",
        base_dir: str = "/home/kali/SandboxAnalysis",
        timeout: int = 100,
    ):
        """
        Initialize the SandboxRunner.

        Args:
            vm_path: Path to the VMware .vmx configuration file.
            guest_user: Username for guest OS authentication.
            guest_pass: Password for guest OS authentication.
            base_snapshot: Name of the snapshot to revert to.
            base_dir: Working directory inside the guest OS.
            timeout: Default timeout for operations in seconds.

        Raises:
            FileNotFoundError: If VM path doesn't exist.
            VMControlError: If vmrun utility is unavailable.
        """
        self.vm_path = Path(vm_path).resolve()
        self.guest_user = guest_user
        self.guest_pass = guest_pass
        self.base_snapshot = base_snapshot
        self.base_dir = PurePosixPath(base_dir)
        self.timeout = timeout
        self.logger = self._setup_logging()

        if not self.vm_path.exists():
            raise FileNotFoundError(f"VM configuration file not found: {self.vm_path}")

        if not self._is_vmrun_available():
            raise VMControlError("vmrun utility not found. Ensure VMware Workstation/Player is installed.")

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for the sandbox."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        return logging.getLogger(self.__class__.__name__)

    def _is_vmrun_available(self) -> bool:
        """Check if vmrun utility is available."""
        try:
            subprocess.run(["vmrun"], capture_output=True, check=False)
            return True
        except FileNotFoundError:
            return False

    def _run_vmrun(self, *args, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """
        Execute a vmrun command with error handling.

        Args:
            *args: Arguments to pass to vmrun.
            timeout: Operation timeout in seconds.

        Returns:
            subprocess.CompletedProcess: Command execution result.

        Raises:
            VMControlError: If the vmrun command fails.
        """
        cmd = ["vmrun", "-T", "ws", "-gu", self.guest_user, "-gp", self.guest_pass] + list(args)
        self.logger.debug(f"Executing vmrun command: {' '.join(cmd[:5] + ['<hidden>'] + cmd[6:])}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                check=True,
            )
            self.logger.debug(f"STDOUT: {result.stdout.strip()}")
            if result.stderr:
                self.logger.debug(f"STDERR: {result.stderr.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            raise VMControlError(f"vmrun failed: {e.stderr or e.stdout or str(e)}") from e
        except subprocess.TimeoutExpired as e:
            raise VMControlError(f"vmrun timed out after {timeout or self.timeout}s") from e

    def _run_vmrun_allow_exit_code(self, *args, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """
        Execute a vmrun command that allows non-zero exit codes (for strace analysis).

        Args:
            *args: Arguments to pass to vmrun.
            timeout: Operation timeout in seconds.

        Returns:
            subprocess.CompletedProcess: Command execution result.
        """
        cmd = ["vmrun", "-T", "ws", "-gu", self.guest_user, "-gp", self.guest_pass] + list(args)
        self.logger.debug(f"Executing vmrun command (allow exit codes): {' '.join(cmd[:5] + ['<hidden>'] + cmd[6:])}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                check=False,  # Don't raise exception on non-zero exit code
            )
            self.logger.debug(f"STDOUT: {result.stdout.strip()}")
            if result.stderr:
                self.logger.debug(f"STDERR: {result.stderr.strip()}")
            return result
        except subprocess.TimeoutExpired as e:
            raise VMControlError(f"vmrun timed out after {timeout or self.timeout}s") from e

    def start_vm(self, gui: bool = False) -> None:
        """Start the virtual machine."""
        self.logger.info("Starting virtual machine...")
        self._run_vmrun("start", str(self.vm_path), "gui" if gui else "nogui")
        self.logger.info("Virtual machine started.")

    def stop_vm(self, force: bool = False) -> None:
        """Stop the virtual machine."""
        self.logger.info("Stopping virtual machine...")
        self._run_vmrun("stop", str(self.vm_path), "hard" if force else "soft")
        self.logger.info("Virtual machine stopped.")

    def revert_to_snapshot(self, snapshot_name: Optional[str] = None) -> None:
        """Revert VM to the specified or base snapshot."""
        snapshot = snapshot_name or self.base_snapshot
        self.logger.info(f"Reverting to snapshot: {snapshot}")
        self._run_vmrun("revertToSnapshot", str(self.vm_path), snapshot)
        self.logger.info("Snapshot reverted.")

    def create_snapshot(self, snapshot_name: str, description: str = "") -> None:
        """Create a new VM snapshot."""
        self.logger.info(f"Creating snapshot: {snapshot_name}")
        self._run_vmrun("snapshot", str(self.vm_path), snapshot_name)
        self.logger.info("Snapshot created.")

    def ensure_guest_directory(self, directory: str) -> None:
        """Ensure a directory exists in the guest OS."""
        self.logger.debug(f"Ensuring guest directory: {directory}")
        try:
            self._run_vmrun("runProgramInGuest", str(self.vm_path), "/bin/mkdir", "-p", directory)
        except VMControlError:
            self.logger.debug(f"Directory {directory} already exists or mkdir failed.")

    def copy_to_vm(self, src: str) -> str:
        """Copy a file from host to guest VM."""
        src_path = Path(src).resolve()
        if not src_path.exists():
            raise FileOperationError(f"Source file not found: {src_path}")

        guest_dest_path = self.base_dir / src_path.name
        self.ensure_guest_directory(str(self.base_dir))
        self.logger.info(f"Copying {src_path} to {guest_dest_path}")
        self._run_vmrun("copyFileFromHostToGuest", str(self.vm_path), str(src_path), str(guest_dest_path))
        self.logger.info("File copied to VM.")
        return str(guest_dest_path)

    def copy_from_vm(self, src: str, dest: str) -> None:
        """Copy a file from guest VM to host."""
        dest_path = Path(dest).resolve()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        guest_src_path = PurePosixPath(src) if src.startswith("/") else self.base_dir / src

        self.logger.info(f"Copying {guest_src_path} to {dest_path}")
        self._run_vmrun("copyFileFromGuestToHost", str(self.vm_path), str(guest_src_path), str(dest_path))
        self.logger.info("File copied from VM.")

    def copy_directory_to_vm(self, src_dir: str) -> List[str]:
        """Copy a directory recursively from host to guest VM."""
        src_path = Path(src_dir).resolve()
        if not src_path.is_dir():
            raise FileOperationError(f"Source directory not found: {src_path}")

        copied_files = []
        for item in src_path.iterdir():
            if item.is_file():
                copied_files.append(self.copy_to_vm(str(item)))
            elif item.is_dir():
                copied_files.extend(self.copy_directory_to_vm(str(item)))
        return copied_files

    def detect_language(self, file_path: str) -> Tuple[Optional[str], str, bool]:
        """Detect programming language and execution requirements."""
        ext = Path(file_path).suffix.lower()
        
        # Check if it's a document type (non-executable)
        if ext in self._DOCUMENT_TYPES:
            return (self._DOCUMENT_TYPES[ext], ext, False)
        
        # Check if it's an executable file type
        interpreter = self._INTERPRETERS.get(ext) or self._COMPILERS.get(ext)
        return (interpreter, ext, ext in self._COMPILERS)

    def compile_code(self, source_path: str) -> str:
        """Compile source code in the guest VM."""
        interpreter, ext, _ = self.detect_language(source_path)
        if not interpreter:
            raise ExecutionError(f"Compilation not supported for {ext}")

        try:
            if ext in (".c", ".cpp"):
                exe_path = source_path.replace(ext, "_compiled")
                compiler = "/usr/bin/gcc" if ext == ".c" else "/usr/bin/g++"
                self._run_vmrun("runProgramInGuest", str(self.vm_path), compiler, source_path, "-o", exe_path)
                return exe_path
            elif ext == ".java":
                self._run_vmrun("runProgramInGuest", str(self.vm_path), "/usr/bin/javac", source_path)
                return source_path.replace(".java", "")
            elif ext == ".go":
                exe_path = source_path.replace(".go", "_compiled")
                self._run_vmrun("runProgramInGuest", str(self.vm_path), "/usr/bin/go", "build", "-o", exe_path, source_path)
                return exe_path
        except VMControlError as e:
            raise ExecutionError(f"Compilation failed: {e}") from e

    def execute_code(self, file_path: str, args: List[str] = None, working_dir: Optional[str] = None) -> None:
        """Execute code in the guest VM."""
        args = args or []
        interpreter, ext, needs_compilation = self.detect_language(file_path)
        if not interpreter:
            raise ExecutionError(f"Unsupported file type: {ext}")

        self.logger.info(f"Executing {file_path} with args: {args}")
        try:
            cmd = []
            if needs_compilation:
                compiled_path = self.compile_code(file_path)
                if ext == ".java":
                    cmd.extend(["/usr/bin/java", Path(compiled_path).name])
                else:
                    cmd.append(compiled_path)
            else:
                cmd.extend([interpreter, file_path])
            cmd.extend(args)

            self._run_vmrun("runProgramInGuest", str(self.vm_path), *cmd)
            self.logger.info("Execution completed.")
        except VMControlError as e:
            raise ExecutionError(f"Code execution failed: {e}") from e

    def analyze_with_strace(self, file_path: str, log_file: str = "syscall_log.txt", args: List[str] = None) -> str:
        """Run strace on a program and log system calls."""
        args = args or []
        interpreter, ext, needs_compilation = self.detect_language(file_path)
        if not interpreter:
            self.logger.warning(f"Strace analysis skipped: Unsupported file type {ext}")
            return None

        log_path = str(self.base_dir / log_file)
        file_path = str(self.base_dir / file_path)
        self.ensure_guest_directory(str(self.base_dir))
        self._run_vmrun("runProgramInGuest", str(self.vm_path), "/usr/bin/touch", log_path)

        self.logger.info(f"Running strace on {file_path}, logging to {log_path}")
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

            # Use a custom vmrun call that doesn't fail on non-zero exit codes
            # since the target program may exit with non-zero (which is normal)
            self._run_vmrun_allow_exit_code("runProgramInGuest", str(self.vm_path), *cmd)
            self.logger.info("Strace analysis completed.")
            return log_path
        except VMControlError as e:
            # Even if strace fails, we might still have some log data
            self.logger.warning(f"Strace analysis encountered issues: {e}")
            return log_path if log_path else None

    def run_custom_tracker(self, tracker_source: str, target_file: str, args: List[str] = None) -> None:
        """Run a custom tracker on a target file."""
        args = args or []
        tracker_binary = self.compile_code(tracker_source)
        interpreter, ext, needs_compilation = self.detect_language(target_file)
        if not interpreter:
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
            self.logger.info("Custom tracker execution completed.")
        except VMControlError as e:
            raise ExecutionError(f"Custom tracker execution failed: {e}") from e

    def get_log_file(self, log_file: str, dest: str) -> None:
        """Retrieve a log file from the guest VM."""
        if not log_file:
            self.logger.warning("No log file specified.")
            return
        self.copy_from_vm(log_file, dest)
        self.logger.info(f"Log file copied to: {dest}")

    def analyze_document(self, file_path: str, log_file: str = "document_analysis.txt") -> str:
        """Analyze document files (PDF, DOC, etc.) for metadata and content."""
        interpreter, ext, _ = self.detect_language(file_path)
        if not interpreter or ext not in self._DOCUMENT_TYPES:
            raise ExecutionError(f"Document analysis not supported for file type: {ext}")
        
        log_path = str(self.base_dir / log_file)
        file_path = str(self.base_dir / file_path)
        self.ensure_guest_directory(str(self.base_dir))
        
        self.logger.info(f"Analyzing document {file_path}, logging to {log_path}")
        
        try:
            # Create analysis script based on file type
            if ext == ".pdf":
                analysis_script = f"""
#!/bin/bash
echo "=== PDF Document Analysis ===" > {log_path}
echo "File: {file_path}" >> {log_path}
echo "Analysis Time: $(date)" >> {log_path}
echo "" >> {log_path}

# Check if file exists
if [ ! -f "{file_path}" ]; then
    echo "ERROR: File not found" >> {log_path}
    exit 1
fi

# Basic file information
echo "=== File Information ===" >> {log_path}
ls -la "{file_path}" >> {log_path}
file "{file_path}" >> {log_path}
echo "" >> {log_path}

# Try to extract PDF metadata if pdfinfo is available
if command -v pdfinfo >/dev/null 2>&1; then
    echo "=== PDF Metadata ===" >> {log_path}
    pdfinfo "{file_path}" >> {log_path} 2>&1
    echo "" >> {log_path}
fi

# Try to extract text content if pdftotext is available
if command -v pdftotext >/dev/null 2>&1; then
    echo "=== PDF Text Content (first 1000 chars) ===" >> {log_path}
    pdftotext "{file_path}" - | head -c 1000 >> {log_path} 2>&1
    echo "" >> {log_path}
fi

# Check for embedded objects or scripts
if command -v pdfdetach >/dev/null 2>&1; then
    echo "=== PDF Attachments ===" >> {log_path}
    pdfdetach -list "{file_path}" >> {log_path} 2>&1
    echo "" >> {log_path}
fi

# Security analysis if qpdf is available
if command -v qpdf >/dev/null 2>&1; then
    echo "=== PDF Security Analysis ===" >> {log_path}
    qpdf --show-encryption "{file_path}" >> {log_path} 2>&1
    echo "" >> {log_path}
fi

echo "=== Analysis Complete ===" >> {log_path}
"""
            else:
                # Generic document analysis for other types
                analysis_script = f"""
#!/bin/bash
echo "=== Document Analysis ===" >> {log_path}
echo "File: {file_path}" >> {log_path}
echo "Type: {ext}" >> {log_path}
echo "Analysis Time: $(date)" >> {log_path}
echo "" >> {log_path}

# Check if file exists
if [ ! -f "{file_path}" ]; then
    echo "ERROR: File not found" >> {log_path}
    exit 1
fi

# Basic file information
echo "=== File Information ===" >> {log_path}
ls -la "{file_path}" >> {log_path}
file "{file_path}" >> {log_path}
echo "" >> {log_path}

# Try to extract text content
echo "=== Text Content (first 1000 chars) ===" >> {log_path}
head -c 1000 "{file_path}" >> {log_path} 2>&1
echo "" >> {log_path}

echo "=== Analysis Complete ===" >> {log_path}
"""
            
            # Write and execute the analysis script
            script_path = str(self.base_dir / "analyze_document.sh")
            self._run_vmrun("runProgramInGuest", str(self.vm_path), "/bin/bash", "-c", f"cat > {script_path} << 'EOF'\n{analysis_script}\nEOF")
            self._run_vmrun("runProgramInGuest", str(self.vm_path), "chmod", "+x", script_path)
            self._run_vmrun("runProgramInGuest", str(self.vm_path), "/bin/bash", script_path)
            
            self.logger.info("Document analysis completed.")
            return log_path
            
        except VMControlError as e:
            self.logger.warning(f"Document analysis encountered issues: {e}")
            return log_path if log_path else None

    def cleanup(self) -> None:
        """Clean up the sandbox environment."""
        self.logger.info("Cleaning up sandbox...")
        try:
            self.revert_to_snapshot()
            self.logger.info("Sandbox cleaned.")
        except VMControlError as e:
            self.logger.error(f"Cleanup failed: {e}")

    def get_vm_info(self) -> Dict[str, str]:
        """Get information about the VM."""
        try:
            result = self._run_vmrun("list")
            status = "running" if str(self.vm_path) in result.stdout else "stopped"
        except VMControlError:
            status = "unknown"
        return {
            "vm_path": str(self.vm_path),
            "status": status,
            "base_snapshot": self.base_snapshot,
            "guest_user": self.guest_user,
            "base_dir": str(self.base_dir),
        }

    def __enter__(self):
        """Start VM when entering context."""
        self.start_vm()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up when exiting context."""
        self.cleanup()