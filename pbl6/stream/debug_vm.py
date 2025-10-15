"""
Script debug để kiểm tra trạng thái VMware và máy ảo.
Chạy: python stream/debug_vm.py
"""

import subprocess
import sys
from pathlib import Path

# Đường dẫn đến VM
VM_PATH = r"E:\package\VMWare os\kali-linux-2025.2-vmware-amd64.vmwarevm\kali-linux-2025.2-vmware-amd64.vmx"


def run_command(cmd):
    """Chạy lệnh và hiển thị kết quả."""
    print(f"\n{'='*60}")
    print(f"🔧 Đang chạy: {' '.join(cmd[:5]) + '...' if len(cmd) > 5 else ' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ Thành công!")
            if result.stdout:
                print(f"📤 Output:\n{result.stdout}")
        else:
            print(f"❌ Lỗi (code: {result.returncode})")
            if result.stderr:
                print(f"📤 Error:\n{result.stderr}")
            if result.stdout:
                print(f"📤 Output:\n{result.stdout}")
                
        return result
        
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout sau 30 giây")
        return None
    except FileNotFoundError:
        print(f"❌ Không tìm thấy lệnh. VMware chưa được cài đặt hoặc chưa thêm vào PATH")
        return None
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None


def main():
    print("🚀 KIỂM TRA VMWARE VÀ MÁY ẢO")
    print("="*60)
    
    # 1. Kiểm tra vmrun có khả dụng không
    print("\n1️⃣ Kiểm tra vmrun...")
    result = run_command(["vmrun"])
    if result is None:
        print("\n❌ KHÔNG THỂ TIẾP TỤC - VMware chưa được cài đặt đúng")
        sys.exit(1)
    
    # 2. Kiểm tra file VM có tồn tại không
    print(f"\n2️⃣ Kiểm tra file VM tại: {VM_PATH}")
    vm_path = Path(VM_PATH)
    if vm_path.exists():
        print(f"✅ File VM tồn tại")
        print(f"📁 Kích thước: {vm_path.stat().st_size / (1024*1024):.2f} MB")
    else:
        print(f"❌ File VM KHÔNG tồn tại")
        print("   Vui lòng cập nhật đường dẫn trong script hoặc sandbox.py")
        sys.exit(1)
    
    # 3. Liệt kê các VM đang chạy
    print("\n3️⃣ Liệt kê các VM đang chạy...")
    run_command(["vmrun", "list"])
    
    # 4. Thử lấy IP của VM (nếu đang chạy)
    print("\n4️⃣ Thử lấy địa chỉ IP của VM...")
    result = run_command(["vmrun", "getGuestIPAddress", VM_PATH, "-wait"])
    
    if result and result.returncode == 0:
        print("✅ VM đang chạy và có thể lấy IP")
    else:
        print("⚠️ Không thể lấy IP - VM có thể chưa khởi động hoặc VMware Tools chưa chạy")
        print("\n📝 Gợi ý:")
        print("   1. Khởi động VM thủ công bằng VMware Workstation")
        print("   2. Đảm bảo VMware Tools đã được cài đặt trong VM")
        print("   3. Chờ VM khởi động hoàn toàn (khoảng 1-2 phút)")
        print("   4. Chạy lại script này")
    
    # 5. Thử chạy lệnh trong VM (nếu đang chạy)
    print("\n5️⃣ Thử chạy lệnh trong VM...")
    run_command([
        "vmrun",
        "-T", "ws",
        "-gu", "kali",
        "-gp", "kali",
        "runProgramInGuest",
        VM_PATH,
        "/bin/bash",
        "-c",
        "echo 'Hello from VM'"
    ])
    
    print("\n" + "="*60)
    print("✅ KIỂM TRA HOÀN TẤT")
    print("="*60)
    print("\n📋 TÓM TẮT:")
    print("   - Nếu tất cả đều thành công ✅, bạn có thể chạy Django server")
    print("   - Nếu có lỗi ❌, hãy sửa theo gợi ý ở trên")
    print("   - Để khởi động server: python manage.py runserver")
    print("   - Truy cập: http://127.0.0.1:8000/stream/")


if __name__ == "__main__":
    main()
