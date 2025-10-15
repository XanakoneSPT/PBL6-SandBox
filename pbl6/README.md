# PBL6 - Sandbox VM Streaming System

Hệ thống quản lý và streaming sandbox VMware sử dụng Django, cho phép người dùng kết nối và tương tác với máy ảo thông qua giao diện web với công nghệ VNC.

## 📋 Mục Lục

- [Tổng Quan](#tổng-quan)
- [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
- [Cài Đặt](#cài-đặt)
- [Cấu Hình VMware](#cấu-hình-vmware)
- [Chạy Ứng Dụng](#chạy-ứng-dụng)
- [Tính Năng](#tính-năng)
- [Cấu Trúc Dự Án](#cấu-trúc-dự-án)
- [API Endpoints](#api-endpoints)
- [Xử Lý Lỗi](#xử-lý-lỗi)

## 🎯 Tổng Quan

Dự án này cung cấp một nền tảng sandbox an toàn để:
- Chạy và phân tích code trong môi trường máy ảo cách ly
- Stream màn hình máy ảo qua giao diện web (VNC)
- Upload file/thư mục vào máy ảo
- Quản lý vòng đời máy ảo (start, stop, revert snapshot)
- Hỗ trợ nhiều ngôn ngữ lập trình (Python, JavaScript, C/C++, Java, Go, Ruby, Perl, PHP)

## 💻 Yêu Cầu Hệ Thống

### Phần Mềm Bắt Buộc

1. **VMware Workstation Pro/Player** (phiên bản 15.0 trở lên)
   - Windows: Download từ [VMware Website](https://www.vmware.com/products/workstation-pro.html)
   - Đảm bảo `vmrun.exe` có trong PATH hoặc tại thư mục cài đặt mặc định

2. **Python** (phiên bản 3.8 trở lên)
   - Download từ [Python.org](https://www.python.org/downloads/)

3. **Máy Ảo Guest OS**
   - Khuyến nghị: Kali Linux 2025.2 hoặc Ubuntu/Debian
   - Cần cài đặt VMware Tools
   - Cần tạo snapshot sạch để revert

### Yêu Cầu Phần Cứng

- **CPU**: Intel VT-x hoặc AMD-V (hỗ trợ ảo hóa)
- **RAM**: Tối thiểu 8GB (khuyến nghị 16GB+)
- **Ổ Cứng**: 50GB trống
- **Kết Nối Mạng**: Stable network cho VNC streaming

## 📦 Cài Đặt

### Bước 1: Clone Repository

```bash
git clone https://github.com/XanakoneSPT/PBL6-SandBox.git
cd PBL6-SandBox
git checkout feature/stream
```

### Bước 2: Tạo Virtual Environment (Khuyến nghị)

```cmd
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài Đặt Dependencies

```cmd
pip install -r requirements.txt
```

### Bước 4: Thiết Lập Database

```cmd
python manage.py migrate
python manage.py createsuperuser
```

### Bước 5: Clone noVNC
```bash
cd pbl6/stream/static
git clone https://github.com/novnc/noVNC.git
```
## ⚙️ Cấu Hình VMware

### 1. Chuẩn Bị Máy Ảo

#### Tạo hoặc Import VM:
```
- Tải Kali Linux VMware image từ: https://www.kali.org/get-kali/#kali-virtual-machines
- Giải nén và import vào VMware Workstation
- Hoặc tạo VM mới với OS Debian/Ubuntu
```

#### Cấu Hình Cơ Bản VM:
```
- RAM: 2GB - 4GB
- CPU: 2 cores
- Network: NAT hoặc Bridged
- Tài khoản: username/password (ví dụ: kali/kali)
```

### 2. Cài VMware Tools Trong Guest OS

```bash
# Trong máy ảo (Kali/Ubuntu)
sudo apt-get update
sudo apt-get install open-vm-tools open-vm-tools-desktop
```

### 3. Cài Đặt Dependencies Trong Guest OS

```bash
# Cài các package cần thiết
sudo apt-get update
sudo apt-get install -y \
    x11vnc \
    xvfb \
    python3 \
    nodejs \
    gcc \
    g++ \
    openjdk-11-jdk \
    golang \
    ruby \
    perl \
    php
```

### 4. Tạo Snapshot

```
1. Đảm bảo VM đang chạy
2. VM Menu → Snapshot → Take Snapshot
3. Tên snapshot: "CleanSnapshot1"
4. Mô tả: "Clean state with all dependencies"
5. Click OK
```

### 5. Cấu Hình Firewall (Trong Guest OS - có thể bỏ qua)

```bash
# Cho phép VNC port
sudo ufw allow 5900/tcp
sudo ufw enable
```

### 6. Cập Nhật Đường Dẫn VM Trong Code

Mở file `stream/sandbox.py` và cập nhật:

```python
def __init__(
    self,
    vm_path: str = "E:\\package\\VMWare os\\kali-linux-2025.2-vmware-amd64.vmwarevm\\kali-linux-2025.2-vmware-amd64.vmx",
    guest_user: str = "kali",
    guest_pass: str = "kali",
    base_snapshot: str = "CleanSnapshot1",
    base_dir: str = "/home/kali",
    timeout: int = 100,
):
```

**Thay đổi các tham số:**
- `vm_path`: Đường dẫn đầy đủ đến file `.vmx` của máy ảo
- `guest_user`: Username trong guest OS
- `guest_pass`: Password trong guest OS
- `base_snapshot`: Tên snapshot đã tạo ở bước 4
- `base_dir`: Thư mục làm việc trong guest OS

## 🚀 Chạy Ứng Dụng

### Khởi Động Development Server

```cmd
python manage.py runserver
```

Server sẽ chạy tại: `http://127.0.0.1:8000`

### Truy Cập Ứng Dụng

1. **Stream Sandbox**: 
   ```
   http://127.0.0.1:8000/stream/
   ```
   - Tự động khởi động VM (nếu chưa chạy)
   - Hiển thị màn hình VM qua noVNC
   - Cho phép upload file

2. **Admin Panel**:
   ```
   http://127.0.0.1:8000/admin/
   ```

## ✨ Tính Năng

### 1. VM Management
- ✅ Tự động khởi động VM
- ✅ Singleton pattern - chỉ khởi tạo VM một lần
- ✅ Revert về snapshot sạch
- ✅ Quản lý vòng đời VM

### 2. VNC Streaming
- ✅ Stream màn hình VM real-time
- ✅ Sử dụng noVNC (HTML5)
- ✅ Xác thực bằng password
- ✅ Responsive UI

### 3. File Operations
- ✅ Upload file đơn lẻ
- ✅ Upload cả thư mục (với cấu trúc)
- ✅ Tự động copy file vào VM
- ✅ Download file từ VM

### 4. Code Execution
- ✅ Hỗ trợ nhiều ngôn ngữ:
  - **Interpreted**: Python, JavaScript, Bash, Ruby, Perl, PHP
  - **Compiled**: C, C++, Java, Go
- ✅ Tự động detect ngôn ngữ
- ✅ Compile & execute
- ✅ Phân tích system call với `strace`

### 5. Security
- ✅ Môi trường sandbox cách ly
- ✅ Revert snapshot sau mỗi session
- ✅ Kiểm tra path traversal
- ✅ Timeout protection

## 📁 Cấu Trúc Dự Án

```
pbl6/
├── manage.py                 # Django management script
├── db.sqlite3               # Database file
├── requirements.txt         # Python dependencies
├── README.md               # This file
│
├── pbl6/                   # Project configuration
│   ├── __init__.py
│   ├── settings.py        # Django settings
│   ├── urls.py            # Main URL configuration
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
│
└── stream/                # Main application
    ├── __init__.py
    ├── admin.py          # Admin configuration
    ├── apps.py           # App configuration
    ├── models.py         # Database models
    ├── views.py          # View handlers
    ├── urls.py           # App URLs
    ├── sandbox.py        # 🔥 Core VM management logic
    ├── tests.py          # Unit tests
    │
    ├── utils/            # Utilities
    │   └── error.py      # Custom exceptions
    │
    ├── templates/        # HTML templates
    │   └── sandbox_stream.html
    │
    ├── static/           # Static files
    │   └── noVNC/        # VNC client library
    │
    └── migrations/       # Database migrations
```

## 🔌 API Endpoints

### 1. Stream Sandbox
```
GET /stream/
```
**Response**: HTML page với VNC viewer

**Chức năng**:
- Khởi động VM nếu chưa chạy
- Cài đặt VNC dependencies
- Trả về endpoint VNC

### 2. Upload File
```
POST /upload_file/
Content-Type: multipart/form-data
```

**Parameters**:
- `files[]`: Danh sách file cần upload
- `{filename}_relative_path`: Đường dẫn tương đối (cho thư mục)

**Response**:
```json
{
  "status": "success",
  "files": ["file1.py", "folder/file2.js"]
}
```