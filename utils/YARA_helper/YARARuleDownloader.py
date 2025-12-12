# import yara
# import os
# import shutil
# from git import Repo

# class YARARuleDownloader:
#     def __init__(self):
#         # self.repo_url = "https://github.com/Yara-Rules/rules.git"
#         self.repo_url = "https://github.com/hkodur/YARA-rules.git"
#         self.clone_dir = "./yara-rules"
#         self.parent_dir = os.path.dirname(os.path.abspath(__file__))
#         self.rules_dir = "./custom_rules"
    
#     def clone_repo(self):
#         if os.path.exists(self.rules_dir):
#             print("✅ Thư mục custom_rules đã tồn tại, bỏ qua việc tải xuống.")
#             return
#         if os.path.exists(self.clone_dir):
#             import shutil
#             shutil.rmtree(self.clone_dir)
#         Repo.clone_from(self.repo_url, self.clone_dir)
#         print("✅ Đã tải repo Yara-Rules vào:", self.clone_dir)

#     def move_yara_rules(self, target_dir="./custom_rules") -> list:
#         """
#         Di chuyển toàn bộ các thư mục con (và file .yar/.yara bên trong)
#         từ self.rules_dir sang target_dir.
#         Giữ nguyên các file ở thư mục gốc (top-level).
#         """

#         src_root = os.path.abspath(self.clone_dir)
#         target_dir = os.path.abspath(target_dir)

#         os.makedirs(target_dir, exist_ok=True)
#         moved_dirs = []

#         # Duyệt tất cả các thư mục con trong src_root (1 cấp)
#         for entry in os.listdir(src_root):
#             src_path = os.path.join(src_root, entry)
#             if os.path.isdir(src_path):
#                 dst_path = os.path.join(target_dir, entry)

#                 # Nếu đã tồn tại thư mục trùng tên, đổi tên để tránh đè
#                 counter = 1
#                 base_dst = dst_path
#                 while os.path.exists(dst_path):
#                     dst_path = f"{base_dst}_{counter}"
#                     counter += 1

#                 try:
#                     shutil.move(src_path, dst_path)
#                     moved_dirs.append(dst_path)
#                     print(f"✅ Đã di chuyển thư mục con: '{src_path}' -> '{dst_path}'")
#                 except Exception as e:
#                     print(f"❌ Lỗi khi di chuyển '{src_path}': {e}")

#         shutil.rmtree(src_root)
#         print(f"📦 Tổng cộng đã di chuyển {len(moved_dirs)} thư mục con đến '{target_dir}'.")
#         return moved_dirs
            
#     def start(self) -> str:
#         if not os.path.exists(self.rules_dir):
#             self.clone_repo()
#             self.move_yara_rules()
#         else:
#             print("✅ Thư mục custom_rules đã tồn tại, bỏ qua việc tải xuống.")
#         return os.path.join(self.parent_dir, self.rules_dir)


import os
import shutil
from pathlib import Path
from git import Repo

class YARARuleDownloader:
    def __init__(self, repo_url: str = "https://github.com/hkodur/YARA-rules.git"):
        self.repo_url = repo_url
        # Use paths relative to this file's location
        self.base_dir = Path(__file__).parent
        self.clone_dir = self.base_dir / "yara-rules"
        self.rules_dir = self.base_dir / "custom_rules"
    
    def _clone_repo(self) -> None:
        """Clone the YARA rules repository."""
        if self.clone_dir.exists():
            shutil.rmtree(self.clone_dir)
        
        Repo.clone_from(self.repo_url, self.clone_dir)
        print(f"✅ Đã tải repo YARA-Rules vào: {self.clone_dir}")

    def _move_subdirectories(self) -> int:
        """
        Move all subdirectories from clone_dir to rules_dir.
        Returns the number of directories moved.
        """
        moved_count = 0
        
        for entry in self.clone_dir.iterdir():
            if not entry.is_dir():
                continue
            
            dst_path = self.rules_dir / entry.name
            
            # Handle name conflicts
            if dst_path.exists():
                counter = 1
                while dst_path.exists():
                    dst_path = self.rules_dir / f"{entry.name}_{counter}"
                    counter += 1
            
            try:
                shutil.move(str(entry), str(dst_path))
                moved_count += 1
                print(f"✅ Đã di chuyển: '{entry.name}' -> '{dst_path.name}'")
            except Exception as e:
                print(f"❌ Lỗi khi di chuyển '{entry.name}': {e}")
        
        return moved_count
    
    def start(self) -> str:
        """
        Download and setup YARA rules if not already present.
        Returns the absolute path to the rules directory.
        """
        if self.rules_dir.exists():
            print("✅ Thư mục custom_rules đã tồn tại, bỏ qua việc tải xuống.")
        else:
            self.rules_dir.mkdir(parents=True, exist_ok=True)
            self._clone_repo()
            
            moved_count = self._move_subdirectories()
            print(f"📦 Đã di chuyển {moved_count} thư mục đến '{self.rules_dir}'.")
            
            # Cleanup clone directory
            if self.clone_dir.exists():
                shutil.rmtree(self.clone_dir)
                print(f"🗑️  Đã xóa thư mục tạm: {self.clone_dir}")
        
        return str(self.rules_dir.resolve())