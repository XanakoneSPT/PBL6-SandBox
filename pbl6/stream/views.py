from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .sandbox import SandboxRunner
import logging
from pathlib import Path
import os
from typing import List

logger = logging.getLogger(__name__)

def stream_sandbox(request):
    """
    Khởi động hoặc tái sử dụng VM sandbox, sau đó render trang VNC stream.
    """
    try:
        logger.info("🎬 Yêu cầu kết nối sandbox...")

        vm_info = SandboxRunner.initialize_vm_once()
        if not vm_info:
            raise RuntimeError("Không thể khởi tạo hoặc lấy lại thông tin VM.")

        vm_ip = vm_info["ip"]
        vm_port = vm_info["port"]
        vm_password = vm_info["password"]

        logger.info(f"✅ VM sẵn sàng tại {vm_ip}:{vm_port}")

        return render(request, "sandbox_stream.html", {
            "vnc_ip": vm_ip,
            "vnc_port": vm_port,
            "vnc_password": vm_password,
            "error": False
        })

    except Exception as e:
        logger.exception("❌ Lỗi khi khởi động hoặc truy cập sandbox.")
        return render(request, "sandbox_stream.html", {
            "error": True,
            "error_message": f"Không thể khởi động sandbox: {str(e)}",
            "error_detail": "Kiểm tra:\n- VMware hoạt động\n- VM có snapshot hợp lệ\n- Tools đã cài đặt"
        }, status=500)


@csrf_exempt
def upload_file(request):
    """
    📁 Xử lý upload file hoặc thư mục từ giao diện web:
      - Hỗ trợ webkitdirectory (tải thư mục đầy đủ)
      - Giữ nguyên cấu trúc thư mục gốc
      - Gửi file vào VM nếu Sandbox đang chạy
    """
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Phương thức không hợp lệ."},
            status=405
        )

    try:
        # ====== 1️⃣ Thiết lập thư mục tạm trên host ======
        upload_root = Path("/tmp/sandbox_uploads").resolve()
        upload_root.mkdir(parents=True, exist_ok=True)

        uploaded_files: List[str] = []

        # ====== 2️⃣ Ghi file vào host ======
        for f in request.FILES.getlist("files"):
            rel_path = request.POST.get(f"{f.name}_relative_path", f.name) or f.name
            safe_rel_path = os.path.normpath(rel_path).replace("\\", "/").lstrip("/")
            
            if ".." in safe_rel_path or safe_rel_path.startswith("/"):
                logger.warning(f"⛔ Đường dẫn nguy hiểm bị từ chối: {rel_path}")
                return JsonResponse(
                    {"status": "error", "message": f"Đường dẫn không hợp lệ: {rel_path}"},
                    status=400
                )

            abs_path = upload_root / safe_rel_path
            abs_path.parent.mkdir(parents=True, exist_ok=True)

            with open(abs_path, "wb") as dest:
                for chunk in f.chunks():
                    dest.write(chunk)

            uploaded_files.append(safe_rel_path)
            logger.info(f"⬆️ Uploaded: {safe_rel_path}")

        # ====== 3️⃣ Nếu VM đã khởi tạo, copy vào trong ======
        if SandboxRunner._instance_cache:
            runner = SandboxRunner.get_instance()

            for rel_path in uploaded_files:
                src = str(upload_root / rel_path)
                try:
                    dest = runner.copy_to_vm(src)
                    logger.info(f"📤 Copied to VM: {rel_path} → {dest}")
                except Exception as e:
                    logger.error(f"❌ Lỗi khi gửi file {rel_path} vào VM: {e}")
                    return JsonResponse(
                        {"status": "error", "message": f"Lỗi khi gửi {rel_path} vào VM: {str(e)}"},
                        status=500
                    )

        # ====== 4️⃣ Trả kết quả ======
        return JsonResponse({"status": "success", "files": uploaded_files})

    except Exception as e:
        logger.exception("❌ Lỗi upload")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)