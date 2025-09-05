# Hướng Dẫn Thiết Lập Môi Trường cho VM-based Sandbox Runner

## Yêu cầu hệ thống

### Phần mềm
- **VMware Workstation** hoặc **VMware Player** (phiên bản 16 trở lên).
- Tiện ích `vmrun` (đi kèm với VMware Workstation/Player).
- Python 3.8 trở lên.
- Máy ảo Kali Linux (khuyến nghị phiên bản 2025.2 hoặc mới hơn) với VMware Tools được cài đặt.

## Các bước thiết lập môi trường

### Bước 1: Cài đặt VMware Workstation/Player
1. Tải xuống VMware Workstation/Player từ [trang chính thức của VMware](https://www.vmware.com/products/workstation-pro.html).
2. Cài đặt phần mềm theo hướng dẫn trên trang web.
3. Đảm bảo tiện ích `vmrun` được cài đặt:
   - Trên Windows, `vmrun.exe` thường nằm trong thư mục cài đặt VMware (ví dụ: `C:\Program Files (x86)\VMware\VMware Workstation`).
   - Kiểm tra bằng lệnh:
     ```bash
     vmrun -h
     ```
   - Nếu lệnh trên không chạy được, thêm thư mục chứa `vmrun` vào biến môi trường `PATH`.

### Bước 2: Thiết lập máy ảo Kali Linux
1. **Tải xuống Kali Linux**:
   - Tải tệp ISO hoặc hình ảnh máy ảo VMware từ [trang chính thức của Kali Linux](https://www.kali.org/get-kali/#_vmware).
   - Khuyến nghị sử dụng phiên bản 2025.2 hoặc mới hơn.

2. **Tạo máy ảo**:
   - Mở VMware Workstation/Player.
   - Chọn **Create a New Virtual Machine**.
   - Sử dụng tệp ISO Kali Linux hoặc hình ảnh VMware đã tải.
   - Cấu hình máy ảo với:
     - RAM: Tối thiểu 4GB.
     - CPU: Tối thiểu 2 nhân.
     - Đĩa cứng: Tối thiểu 20GB.
   - Cài đặt Kali Linux theo hướng dẫn trên màn hình. Sử dụng tài khoản mặc định:
     - Tên người dùng: `kali`
     - Mật khẩu: `kali`

3. **Cài đặt VMware Tools**:
   - Trong VMware, chọn **VM > Install VMware Tools**.
   - Trong Kali Linux, gắn đĩa VMware Tools và cài đặt:
     ```bash
     sudo mount /dev/cdrom /mnt
     tar -xzf /mnt/VMwareTools-*.tar.gz -C /tmp
     cd /tmp/vmware-tools-distrib
     sudo ./vmware-install.pl
     ```
   - Làm theo hướng dẫn để hoàn tất cài đặt. VMware Tools cần thiết để `vmrun` hoạt động đúng.

4. **Tạo snapshot sạch**:
   - Sau khi cài đặt Kali Linux và VMware Tools, tạo một snapshot để quay lại trạng thái sạch:
     - Trong VMware, chọn **VM > Snapshot > Take Snapshot**.
     - Đặt tên snapshot, ví dụ: `CleanSnapShot1`.
   - Snapshot này sẽ được sử dụng để khôi phục máy ảo sau mỗi lần thực thi mã.

### Bước 3: Cài đặt các công cụ cần thiết trong Kali Linux
1. **Cập nhật hệ thống**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Cài đặt `strace`**:
   ```bash
   sudo apt install strace
   ```
   Kiểm tra cài đặt:
   ```bash
   which strace
   ```
   Kết quả nên là `/usr/bin/strace`.

3. **Cài đặt các trình thông dịch và trình biên dịch**:
   Module hỗ trợ các ngôn ngữ như Python, JavaScript, Bash, Ruby, Perl, PHP, C, C++, Java, và Go. Cài đặt các công cụ tương ứng:
   ```bash
   sudo apt install python3 nodejs bash ruby perl php gcc g++ default-jdk golang -y
   ```
   Kiểm tra từng công cụ:
   ```bash
   python3 --version
   node --version
   bash --version
   ruby --version
   perl --version
   php --version
   gcc --version
   g++ --version
   javac --version
   go version
   ```

4. **Tạo thư mục làm việc**:
   Tạo thư mục `/home/kali/SandboxAnalysis` trong Kali Linux:
   ```bash
   mkdir -p /home/kali/SandboxAnalysis
   chmod u+rwx /home/kali/SandboxAnalysis
   ```

### Bước 4: Cài đặt môi trường Python trên host
1. **Cài đặt Python**:
   - Tải và cài đặt Python 3.8 trở lên từ [python.org](https://www.python.org/downloads/).
   - Kiểm tra phiên bản:
     ```bash
     python3 --version
     ```

2. **Cài đặt module Python**:
   Module này sử dụng các thư viện Python tiêu chuẩn (`os`, `subprocess`, `logging`, `pathlib`, `typing`). Không cần cài đặt thêm gói nào.

3. **Sao chép mã SandboxRunner**:
   - Tải tệp `sandbox_runner.py` (hoặc mã bạn đã cung cấp) vào máy chủ (host).
   - Đặt tệp trong thư mục làm việc của bạn, ví dụ: `C:\SandboxProject\sandbox_runner.py`.

### Bước 5: Cấu hình và chạy SandboxRunner
1. **Cấu hình SandboxRunner**:
   - Mở tệp `sandbox_runner.py` và kiểm tra các tham số trong `__init__`:
     ```python
     def __init__(
         self,
         vm_path: str = "E:\\package\\VMWare os\\kali-linux-2025.2-vmware-amd64.vmwarevm\\kali-linux-2025.2-vmware-amd64.vmx",
         guest_user: str = "kali",
         guest_pass: str = "kali",
         base_snapshot: str = "CleanSnapShot1",
         base_dir: str = "/home/kali/SandboxAnalysis",
         timeout: int = 100
     ):
     ```
   - Cập nhật `vm_path` để trỏ đến tệp `.vmx` của máy ảo Kali Linux trên máy chủ của bạn.
   - Đảm bảo `guest_user`, `guest_pass`, `base_snapshot`, và `base_dir` khớp với cấu hình máy ảo.

2. **Chạy thử nghiệm**:
   - Tạo một tệp mã mẫu, ví dụ `test.py`:
     ```python
     print("Hello, World!")
     ```
   - Chạy đoạn mã sau trong Python trên host:
     ```python
     from sandbox_runner import SandboxRunner

     sandbox = SandboxRunner()
     sandbox.start_vm()
     sandbox.copy_to_vm("test.py", "test.py")
     log_path = sandbox.analyze_with_strace("test.py")
     sandbox.copy_from_vm(log_path, "local_syscall_log.txt")
     sandbox.cleanup()
     ```
   - Kiểm tra tệp `local_syscall_log.txt` để xem kết quả phân tích `strace`.

### Khắc phục sự cố
1. **Lỗi `vmrun command failed: Guest program exited with non-zero exit code: 2`**:
   - Kiểm tra xem tệp `file_path` đã được sao chép vào `/home/kali/SandboxAnalysis`.
   - Đảm bảo `strace` và trình thông dịch (ví dụ: `python3`) được cài đặt:
     ```bash
     sudo apt install strace python3
     ```
   - Kiểm tra quyền thư mục:
     ```bash
     chmod u+rwx /home/kali/SandboxAnalysis
     ```

2. **Lỗi đường dẫn chứa `\`**:
   - Đảm bảo rằng tất cả đường dẫn trong guest OS sử dụng `/`. Mã đã được sửa để sử dụng `PurePosixPath` cho `file_path` và `log_path`.

3. **Máy ảo không phản hồi**:
   - Kiểm tra trạng thái máy ảo:
     ```python
     print(sandbox.get_vm_info())
     ```
   - Đảm bảo VMware Tools được cài đặt và máy ảo đang chạy.
