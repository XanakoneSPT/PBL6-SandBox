import os
import re
import yara
from pathlib import Path
from .YARARuleDownloader import YARARuleDownloader


class YARACompiler:
    """
    Trình biên dịch và quản lý YARA rule với bộ lọc thông minh nhằm giảm false positive.
    Tự động loại bỏ các rule không cần thiết hoặc chỉ kiểm tra đặc trưng file (utility rules).
    """

    # Từ khóa malware quan trọng → nếu rule chứa thì luôn giữ lại
    MALWARE_KEYWORDS = {
        "trojan", "ransom", "ransomware", "stealer", "infostealer",
        "spy", "spyeye", "zeus", "dridex", "qbot", "quakbot",
        "botnet", "emotet", "agent", "backdoor", "rootkit", "exploit",
        "miner", "loader", "rat", "webshell", "dropper", "payload",
        "malware", "virus", "worm", "adware", "keylogger"
    }

    # Từ khóa meta mô tả kỹ thuật, không phải malware
    META_KEYWORDS = {
        "pecheck", "peid", "compiler", "overlay", "packer",
        "entropy", "ispe", "isconsole"
    }

    # Chuỗi chung chung dễ gây match sai
    GENERIC_STRINGS = {
        '"data"', '"data_end"', '"error"', '"debug"', '"string"',
        '"start"', '"end"', '"main"', '"init"', '"test"',
        '"buffer"', '"config"', '"version"', '"info"'
    }

    # Thư mục cần bỏ qua khi load rules
    SKIP_DIRS = {"utils", "test", "tests", "examples", "docs"}

    def __init__(self, rules_dirs=None, auto_download=True, verbose=True):
        """
        Args:
            rules_dirs (list[str]): Danh sách thư mục chứa YARA rules
            auto_download (bool): Tự động tải rules nếu chưa có
            verbose (bool): Hiển thị log chi tiết
        """
        self.verbose = verbose

        if auto_download:
            downloader = YARARuleDownloader()
            downloader.start()

        # Use path relative to this file's location
        default_rules_dir = str(Path(__file__).parent / "custom_rules")
        self.rules_dirs = rules_dirs or [default_rules_dir]
        self.compiled_rules = None

    # ============================== #
    #        INTERNAL HELPERS        #
    # ============================== #

    def _log(self, msg: str):
        """Ghi log có điều kiện."""
        if self.verbose:
            print(msg)

    def _extract_string_patterns(self, content: str) -> list[str]:
        """Trích xuất các chuỗi $var = "..." trong rule."""
        return [m.group(1).lower() for m in re.finditer(r'\$\w+\s*=\s*"([^"]*)"', content)]

    def _should_skip_rule(self, filepath: str, content: str) -> tuple[bool, str]:
        """Kiểm tra rule có nên bỏ qua không."""
        lower = content.lower()
        filename = os.path.basename(filepath).lower()
        num_strings = len(re.findall(r"\$\w+", content))
        has_malware_kw = any(k in lower for k in self.MALWARE_KEYWORDS)
        has_meta_kw = any(k in lower for k in self.META_KEYWORDS)

        # 1️⃣ Bỏ rule utility hoặc PECheck
        if "pecheck" in filename or "tags: pecheck" in lower:
            return True, "chỉ kiểm tra cấu trúc PE"
        if "peid" in filename or "tags: peid" in lower:
            if not has_malware_kw:
                return True, "chỉ nhận diện packer/compiler"

        # 2️⃣ Bỏ rule tên utility
        skip_names = ["ispe", "isconsole", "hasoverlay", "isgui", "isdriver", "isdll"]
        m = re.search(r'rule\s+(\w+)', content, re.IGNORECASE)
        if m and any(sn in m.group(1).lower() for sn in skip_names):
            return True, f"utility rule ({m.group(1)})"

        # 3️⃣ Bỏ rule chỉ có string generic
        strings = self._extract_string_patterns(content)
        if strings:
            all_generic = all(
                any(gen in s for gen in ["data", "error", "debug", "string", "start", "end"])
                for s in strings
            )
            if all_generic and num_strings <= 3 and not has_malware_kw:
                return True, f"chuỗi match chung chung: {', '.join(strings[:3])}"

        # 4️⃣ Rule quá ngắn hoặc chỉ meta
        if num_strings <= 1 and not has_malware_kw:
            return True, "quá đơn giản, không có dấu hiệu malware"
        if has_meta_kw and not has_malware_kw and num_strings <= 3:
            return True, "chỉ kiểm tra meta, không phải malware"

        # 5️⃣ Bỏ rule chỉ match 1-2 chuỗi generic
        if num_strings <= 2:
            if any(gs in lower for gs in self.GENERIC_STRINGS) and not has_malware_kw:
                return True, "match 1–2 chuỗi generic"

        return False, ""

    # ============================== #
    #           COMPILATION          #
    # ============================== #

    def compile_rules(self) -> yara.Rules:
        """Biên dịch tất cả các rule hợp lệ và loại bỏ rule gây nhiễu."""
        rule_files = []
        for d in self.rules_dirs:
            if not os.path.exists(d):
                self._log(f"⚠️ Thư mục không tồn tại: {d}")
                continue
            for dirpath, dirnames, files in os.walk(d):
                dirnames[:] = [x for x in dirnames if x.lower() not in self.SKIP_DIRS]
                for f in files:
                    if f.lower().endswith((".yar", ".yara")):
                        rule_files.append(os.path.join(dirpath, f))

        if not rule_files:
            raise FileNotFoundError("❌ Không tìm thấy rule YARA nào.")

        valid, skipped_filter, skipped_syntax = {}, [], []

        self._log(f"🔍 Phát hiện {len(rule_files)} file rule — đang xử lý...")

        for fp in rule_files:
            try:
                text = Path(fp).read_text(encoding="utf-8", errors="ignore")
                skip, reason = self._should_skip_rule(fp, text)
                if skip:
                    skipped_filter.append((fp, reason))
                    self._log(f"⚠️ Bỏ: {os.path.basename(fp)} → {reason}")
                    continue
                yara.compile(filepath=fp)
                key = os.path.basename(fp)
                while key in valid:
                    name, ext = os.path.splitext(key)
                    key = f"{name}_dup{ext}"
                valid[key] = fp
            except yara.SyntaxError as e:
                skipped_syntax.append((fp, str(e)))
                self._log(f"❌ Lỗi cú pháp: {os.path.basename(fp)} ({e})")

        if not valid:
            raise RuntimeError("❌ Không có rule hợp lệ sau khi lọc.")

        self.compiled_rules = yara.compile(filepaths=valid)

        # 📊 Thống kê
        total = len(rule_files)
        self._log("\n" + "="*60)
        self._log(f"✅ HOÀN THÀNH BIÊN DỊCH YARA")
        self._log(f"📁 Tổng số file: {total}")
        self._log(f"✅ Hợp lệ: {len(valid)} ({len(valid)*100//total}%)")
        self._log(f"⚠️ Lọc bỏ: {len(skipped_filter)} | ❌ Lỗi cú pháp: {len(skipped_syntax)}")
        self._log("="*60 + "\n")

        return self.compiled_rules

    def get_compiled_rules(self) -> yara.Rules:
        """Trả về rules đã biên dịch."""
        if not self.compiled_rules:
            raise ValueError("⚠️ Chưa có rules. Hãy gọi compile_rules() trước.")
        return self.compiled_rules

    # ============================== #
    #             MATCH              #
    # ============================== #

    def _filter_results(self, matches):
        """Lọc kết quả match để giảm false positive."""
        skip = {
            "ispe32", "ispe64", "isconsole", "isgui", "isdll", "isdriver",
            "hasoverlay", "hasdebug", "hasresource", "hasimport",
            "microsoft_visual_cpp", "microsoft_visual_basic",
            "borland_delphi", "mingw", "gcc", "msvc"
        }
        filtered = []
        for m in matches:
            name = m.rule.lower()
            if any(s in name for s in skip):
                continue
            if len(m.strings) <= 1:
                tags = [t.lower() for t in m.tags]
                meta = {k.lower(): str(v).lower() for k, v in m.meta.items()}
                strong = ["apt", "ransomware", "backdoor", "c2", "exploit"]
                if not any(i in tags or i in meta.get("description", "") for i in strong):
                    continue
            tags = [t.lower() for t in m.tags]
            if ("pecheck" in tags or "peid" in tags) and not any(
                t in tags for t in ["malware", "trojan", "apt", "ransom"]
            ):
                continue
            filtered.append(m)
        return filtered

    def match_file(self, filepath: str, filter_results=True, debug=False):
        """Quét file bằng rules đã biên dịch."""
        rules = self.get_compiled_rules()
        matches = rules.match(filepath)
        if debug:
            print(f"[debug] {len(matches)} matches cho {filepath}")
            for m in matches:
                print(f" - {m.rule} ({len(m.strings)} strings)")
        return self._filter_results(matches) if filter_results else matches

    def match_data(self, data: bytes, filter_results=True, debug=False):
        """Quét dữ liệu dạng bytes."""
        rules = self.get_compiled_rules()
        matches = rules.match(data=data)
        if debug:
            print(f"[debug] {len(matches)} matches cho data ({len(data)} bytes)")
        return self._filter_results(matches) if filter_results else matches


if __name__ == "__main__":
    print("🚀 Khởi động YARACompiler (Smart Filter Enabled)...\n")
    try:
        # Use default path (will be relative to this file's location)
        compiler = YARACompiler(auto_download=True)
        compiler.compile_rules()
        print("✅ Rules đã sẵn sàng.")
        print("💡 Sử dụng: compiler.match_file('path/to/file')")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
