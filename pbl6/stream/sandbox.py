import os
import re
import time
import secrets
import logging
import subprocess
from pathlib import Path, PurePosixPath
from typing import Optional, List, Tuple, Dict

from .utils.error import SandboxError, VMControlError, FileOperationError, ExecutionError


class SandboxRunner:
    """Quản lý môi trường sandbox (VMware) để phân tích và chạy code an toàn."""

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

    _instance_cache = None 
    
    def __init__(
        self,
        vm_path: str = "E:\\package\\VMWare os\\kali-linux-2025.2-vmware-amd64.vmwarevm\\kali-linux-2025.2-vmware-amd64.vmx",
        guest_user: str = "kali",
        guest_pass: str = "kali",
        base_snapshot: str = "CleanSnapshot1",
        base_dir: str = "/home/kali",
        timeout: int = 100,
    ):
        self.vm_path = Path(vm_path).resolve()
        self.guest_user = guest_user
        self.guest_pass = guest_pass
        self.base_snapshot = base_snapshot
        self.base_dir = PurePosixPath(base_dir)
        self.timeout = timeout
        self.logger = self._setup_logging()
        
        if not self.vm_path.exists():
            raise FileNotFoundError(f"VM config file not found: {self.vm_path}")
        if not self._is_vmrun_available():
            raise VMControlError("`vmrun` not found. Ensure VMware Workstation/Player is installed.")

    # ==========================================================
    # 🚀 SINGLETON KHỞI TẠO
    # ==========================================================
    @classmethod
    def initialize_vm_once(cls):
        """Khởi tạo VM chỉ 1 lần, cache lại endpoint VNC + IP."""
        if cls._instance_cache:
            cls._instance_cache["runner"].logger.info("♻️ Dùng lại VM đã khởi tạo.")
            return cls._instance_cache

        runner = cls()
        cls._instance_vm = runner
        runner.logger.info("🚀 Khởi tạo máy ảo lần đầu...")

        endpoint = runner.setup_vnc_environment(vnc_port=5900, password="123456", start_vm=True)
        ip, port = endpoint.split(":")[0], 5900

        cls._instance_cache = {
            "runner": runner,
            "endpoint": endpoint,
            "ip": ip,
            "port": port,
            "password": "123456",
            "timestamp": time.time(),
        }
        runner.logger.info(f"✅ VM sẵn sàng tại {endpoint}")
        return cls._instance_cache
        
    @classmethod
    def get_instance(cls):
        """
        Lấy ra instance duy nhất của SandboxRunner.
        Nếu chưa tồn tại, tự động khởi tạo và lưu vào cache.
        """
        if cls._instance_cache and "runner" in cls._instance_cache:
            return cls._instance_cache["runner"]

        # Nếu chưa có cache, khởi tạo lần đầu
        runner = cls()
        cls._instance_cache = {"runner": runner}
        runner.logger.info("🚀 SandboxRunner instance được khởi tạo lần đầu.")
        return runner
    
    # ==========================================================
    # ⚙️ HỆ THỐNG CƠ BẢN
    # ==========================================================
    def _setup_logging(self) -> logging.Logger:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        return logging.getLogger("SandboxRunner")

    def _is_vmrun_available(self) -> bool:
        try:
            subprocess.run(["vmrun"], capture_output=True, check=False)
            return True
        except FileNotFoundError:
            return False

    def _run_vmrun(self, *args, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        cmd = ["vmrun", "-T", "ws", "-gu", self.guest_user, "-gp", self.guest_pass, *args]
        self.logger.debug(f"▶ Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout or self.timeout, check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            raise VMControlError(f"vmrun failed: {e.stderr or e.stdout}")
        except subprocess.TimeoutExpired:
            raise VMControlError(f"vmrun timed out after {timeout or self.timeout}s")

    # ==========================================================
    # 🔧 QUẢN LÝ VM
    # ==========================================================
    def start_vm(self, gui: bool = True):
        """Khởi động máy ảo (nếu chưa chạy)."""
        result = self._run_vmrun("list")
        if str(self.vm_path) in result.stdout:
            self.logger.info("✅ Máy ảo đã chạy.")
            return
        self._run_vmrun("start", str(self.vm_path), "gui" if gui else "nogui")
        self.logger.info("🚀 Máy ảo khởi động thành công.")
        time.sleep(5)

    def stop_vm(self, force: bool = False):
        self._run_vmrun("stop", str(self.vm_path), "hard" if force else "soft")
        self.logger.info("🛑 VM đã dừng.")

    def revert_to_snapshot(self, snapshot: Optional[str] = None):
        snapshot = snapshot or self.base_snapshot
        self.logger.info(f"↩️ Reverting snapshot: {snapshot}")
        self._run_vmrun("revertToSnapshot", str(self.vm_path), snapshot)

    # ==========================================================
    # 📂 QUẢN LÝ FILE
    # ==========================================================
    def ensure_guest_directory(self, directory: str):
        try:
            self._run_vmrun("runProgramInGuest", str(self.vm_path), "/bin/mkdir", "-p", directory)
        except VMControlError:
            pass

    def copy_to_vm(self, src: str) -> str:
        src_path = Path(src).resolve()
        if not src_path.exists():
            raise FileOperationError(f"File not found: {src_path}")

        dest = self.base_dir / src_path.name
        self.ensure_guest_directory(str(self.base_dir))
        self._run_vmrun("copyFileFromHostToGuest", str(self.vm_path), str(src_path), str(dest))
        return str(dest)

    def copy_from_vm(self, src: str, dest: str):
        guest_src = PurePosixPath(src) if src.startswith("/") else self.base_dir / src
        dest_path = Path(dest).resolve()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        self._run_vmrun("copyFileFromGuestToHost", str(self.vm_path), str(guest_src), str(dest_path))

    # ==========================================================
    # 💻 PHÁT HIỆN & CHẠY CODE
    # ==========================================================
    def detect_language(self, file_path: str) -> Tuple[Optional[str], str, bool]:
        ext = Path(file_path).suffix.lower()
        return (self._INTERPRETERS.get(ext) or self._COMPILERS.get(ext), ext, ext in self._COMPILERS)

    def compile_code(self, src_path: str) -> str:
        interpreter, ext, _ = self.detect_language(src_path)
        if not interpreter:
            raise ExecutionError(f"Unsupported file: {ext}")

        exe_path = src_path.replace(ext, "_compiled")
        cmds = {
            ".c": ["/usr/bin/gcc", src_path, "-o", exe_path],
            ".cpp": ["/usr/bin/g++", src_path, "-o", exe_path],
            ".java": ["/usr/bin/javac", src_path],
            ".go": ["/usr/bin/go", "build", "-o", exe_path, src_path],
        }
        self._run_vmrun("runProgramInGuest", str(self.vm_path), *cmds[ext])
        return exe_path

    def execute_code(self, file_path: str, args: Optional[List[str]] = None):
        args = args or []
        interpreter, ext, needs_compile = self.detect_language(file_path)
        if not interpreter:
            raise ExecutionError(f"Unsupported file type: {ext}")

        cmd = []
        if needs_compile:
            compiled = self.compile_code(file_path)
            cmd = [compiled] if ext != ".java" else ["/usr/bin/java", Path(compiled).name]
        else:
            cmd = [interpreter, file_path]
        cmd.extend(args)
        self._run_vmrun("runProgramInGuest", str(self.vm_path), *cmd)

    # ==========================================================
    # 🔍 PHÂN TÍCH
    # ==========================================================
    def analyze_with_strace(self, file_path: str, log_file: str = "syscall_log.txt", args: List[str] = None) -> str:
        args = args or []
        interpreter, ext, needs_compile = self.detect_language(file_path)
        if not interpreter:
            raise ExecutionError(f"Unsupported type: {ext}")

        log_path = str(self.base_dir / log_file)
        self._run_vmrun("runProgramInGuest", str(self.vm_path), "/bin/touch", log_path)

        cmd = ["/usr/bin/strace", "-f", "-o", log_path]
        if needs_compile:
            compiled = self.compile_code(file_path)
            cmd += [compiled] if ext != ".java" else ["java", Path(compiled).name]
        else:
            cmd += [interpreter, file_path]
        cmd += args
        self._run_vmrun("runProgramInGuest", str(self.vm_path), *cmd)
        return log_path

    # ==========================================================
    # 🧹 CLEANUP
    # ==========================================================
    def cleanup(self):
        try:
            self.revert_to_snapshot()
            self.logger.info("🧹 Sandbox reverted to clean state.")
        except VMControlError as e:
            self.logger.error(f"Cleanup failed: {e}")

    # ==========================================================
    # 🌐 MÔI TRƯỜNG VNC
    # ==========================================================
    def install_vnc_dependencies(self):
        self.logger.info("🔧 Installing x11vnc + Xvfb if missing...")
        cmd = (
            "export DEBIAN_FRONTEND=noninteractive && "
            "if ! command -v x11vnc >/dev/null; then "
            "sudo apt-get update -qq && "
            "sudo apt-get install -y -qq x11vnc xvfb; fi"
        )
        self._run_vmrun("runProgramInGuest", str(self.vm_path), "/bin/bash", "-c", cmd)

    def start_virtual_display(self, display=":0", resolution="1920x1080x24"):
        self._run_vmrun("runProgramInGuest", str(self.vm_path),
                        "/bin/bash", "-c", f"pkill -9 Xvfb || true && nohup Xvfb {display} -screen 0 {resolution} >/tmp/xvfb.log 2>&1 &")
        self.logger.info("🖥️ Xvfb started.")

    def start_x11vnc(self, vnc_port=5900, password=None, display=":0") -> str:
        password = password or secrets.token_hex(4)
        self._run_vmrun("runProgramInGuest", str(self.vm_path),
                        "/bin/bash", "-c", f"pkill -9 x11vnc || true && export DISPLAY={display} && nohup x11vnc -display {display} -rfbport {vnc_port} -passwd {password} -forever -shared >/tmp/x11vnc.log 2>&1 &")
        return password

    def get_vm_ip(self, retries=10, delay=5) -> str:
        for i in range(retries):
            try:
                ip = self._run_vmrun("getGuestIPAddress", str(self.vm_path), "-wait").stdout.strip()
                if re.match(r"\d+\.\d+\.\d+\.\d+", ip):
                    return ip
            except VMControlError:
                pass
            self.logger.warning(f"⚠️ Lần {i+1}/{retries}: chưa lấy được IP, chờ {delay}s...")
            time.sleep(delay)
        raise SandboxError("Không thể lấy IP từ VM.")

    def open_vnc_port(self, port=5900):
        cmd = f"sudo ufw allow {port}/tcp || true"
        self._run_vmrun("runProgramInGuest", str(self.vm_path), "/bin/bash", "-c", cmd)

    def setup_vnc_environment(self, vnc_port=5900, password=None, start_vm=True) -> str:
        if start_vm:
            self.start_vm(gui=True)
        time.sleep(5)

        ip = self.get_vm_ip()
        self.install_vnc_dependencies()
        self.start_virtual_display()
        self.open_vnc_port(vnc_port)
        password = self.start_x11vnc(vnc_port, password)
        endpoint = f"{ip}:{vnc_port}|password={password}"
        self.logger.info(f"✅ VNC sẵn sàng tại {endpoint}")
        return endpoint

    # ==========================================================
    # CONTEXT MANAGER
    # ==========================================================
    def __enter__(self):
        self.start_vm()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
