import os
from pathlib import Path
from typing import List, Set, Optional
import yara
from .YARACompiler import YARACompiler


class YARAScanner:
    """
    YARA Scanner với bộ lọc thông minh để giảm false positive.
    """
    
    # Supported file extensions (YARA can scan any file, but we focus on these)
    SUPPORTED_EXTENSIONS: Set[str] = {
        # Windows executables & libraries
        ".exe", ".dll", ".sys", ".appx", ".vxd", ".scr", ".cpl", ".ocx", ".msi", ".cab",
        
        # Unix/Linux executables & libraries  
        ".elf", ".so", ".dylib", ".bin", ".run", ".app", ".out", ".o", ".a",
        
        # Mobile applications
        ".apk", ".ipa", ".dex", ".aab", ".xap",
        
        # Scripts - Shell
        ".sh", ".bash", ".zsh", ".fish", ".csh", ".ksh",
        
        # Scripts - Windows
        ".bat", ".cmd", ".ps1", ".psm1", ".psd1", ".vbs", ".vbe", ".wsf", ".wsh",
        
        # Scripting Languages
        ".py", ".pyc", ".pyw", ".pyo", ".pyd",  # Python
        ".js", ".jsx", ".mjs", ".cjs",  # JavaScript
        ".ts", ".tsx",  # TypeScript
        ".rb", ".rbw",  # Ruby
        ".pl", ".pm", ".t", ".pod",  # Perl
        ".php", ".php3", ".php4", ".php5", ".phtml",  # PHP
        ".lua",  # Lua
        ".tcl",  # Tcl
        ".r", ".rdata", ".rds",  # R
        
        # Compiled Languages Source
        ".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hxx",  # C/C++
        ".go",  # Go
        ".rs",  # Rust
        ".cs", ".vb",  # C#, VB.NET
        ".java", ".class", ".jar", ".war", ".ear",  # Java
        ".kt", ".kts",  # Kotlin
        ".swift",  # Swift
        ".m", ".mm",  # Objective-C
        ".scala",  # Scala
        ".groovy", ".gradle",  # Groovy
        ".nim",  # Nim
        ".d",  # D
        ".zig",  # Zig
        
        # Web Technologies
        ".html", ".htm", ".xhtml", ".shtml",  # HTML
        ".css", ".scss", ".sass", ".less",  # CSS
        ".xml", ".xsl", ".xsd", ".dtd", ".svg",  # XML
        ".json", ".jsonld",  # JSON
        ".yaml", ".yml",  # YAML
        ".toml",  # TOML
        ".ini", ".cfg", ".conf", ".config",  # Config
        
        # Web Frameworks & Templates
        ".jsp", ".jspx", ".asp", ".aspx", ".ascx",  # Server Pages
        ".vue", ".svelte",  # Modern Frameworks
        ".ejs", ".hbs", ".mustache", ".jade", ".pug",  # Templates
        
        # Documents
        ".pdf",  # PDF
        ".doc", ".docx", ".docm", ".dot", ".dotx", ".dotm",  # Word
        ".xls", ".xlsx", ".xlsm", ".xlt", ".xltx", ".xltm", ".xlsb",  # Excel
        ".ppt", ".pptx", ".pptm", ".pot", ".potx", ".potm",  # PowerPoint
        ".odt", ".ods", ".odp", ".odg",  # OpenDocument
        ".rtf", ".txt", ".csv",  # Text
        
        # Archives & Compression
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".lz", ".lzma",
        ".tgz", ".tbz2", ".tar.gz", ".tar.bz2", ".tar.xz",
        ".iso", ".img", ".dmg",  # Disk images
        
        # Databases
        ".sql", ".db", ".sqlite", ".sqlite3", ".mdb", ".accdb",
        
        # Markup & Data
        ".md", ".markdown", ".rst", ".tex",  # Markup
        ".csv", ".tsv",  # Tabular data
        
        # Assembly & Low-level
        ".asm", ".s", ".nasm",  # Assembly
        
        # JVM Languages
        ".groovy", ".clj", ".cljs",  # Clojure
        
        # Functional Languages
        ".hs", ".lhs",  # Haskell
        ".ml", ".mli",  # OCaml
        ".fs", ".fsx", ".fsi",  # F#
        ".erl", ".hrl",  # Erlang
        ".ex", ".exs",  # Elixir
        
        # Other Languages
        ".dart",  # Dart
        ".v", ".vhdl",  # Verilog/VHDL
        ".awk",  # AWK
        ".sed",  # Sed
        ".vim",  # VimScript
        
        # Multimedia (malware can hide in these)
        ".swf", ".fla",  # Flash
        ".gif", ".jpg", ".jpeg", ".png", ".bmp", ".ico", ".webp",  # Images
        
        # Package/Build files
        ".deb", ".rpm", ".pkg", ".dmg", ".snap", ".flatpak",
        ".whl", ".egg",  # Python packages
        ".gem",  # Ruby gems
        ".nupkg",  # NuGet
        
        # Container/VM
        ".ova", ".ovf", ".vmdk", ".vdi", ".vhd", ".vhdx",
        
        # Other executables
        ".com", ".pif", ".application", ".gadget", ".msp", ".mst",
        
        # Scripts without extension (check by content)
        "",  # Files without extension
    }
    
    def __init__(self, extensions: Set[str] = None, auto_filter: bool = True):
        """
        Initialize YARA scanner with compiled rules.
        
        Args:
            extensions: Set of file extensions to scan (uses defaults if None)
            auto_filter: Automatically filter false positives (recommended)
            
        Raises:
            RuntimeError: If rules compilation fails
        """
        self.compiler = YARACompiler()
        self.compiled_rules = self.compiler.compile_rules()
        self.extensions = extensions or self.SUPPORTED_EXTENSIONS
        self.auto_filter = auto_filter
        
        if self.compiled_rules is None:
            raise RuntimeError("❌ Không thể khởi tạo quy tắc YARA hợp lệ.")

    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file extension is supported."""
        return file_path.suffix.lower() in self.extensions

    def scan_file(self, file_path: str, filter_results: Optional[bool] = None) -> List[yara.Match]:
        """
        Scan a file with compiled YARA rules.
        
        Args:
            file_path: Path to file to scan
            filter_results: Override auto_filter setting (None = use default)
            
        Returns:
            List of YARA matches (filtered if enabled)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported
            RuntimeError: If YARA scanning fails
        """
        path = Path(file_path)
        
        if not path.is_file():
            raise FileNotFoundError(f"❌ Tệp không tồn tại: {file_path}")
        
        if not self._is_supported_file(path):
            raise ValueError(
                f"❌ Tệp không phải định dạng được hỗ trợ: {file_path}\n"
                f"Các định dạng hỗ trợ: {', '.join(sorted(self.extensions))}"
            )

        try:
            # Sử dụng phương thức match_file của compiler (có bộ lọc)
            should_filter = filter_results if filter_results is not None else self.auto_filter
            return self.compiler.match_file(str(path), filter_results=should_filter)
        except yara.Error as e:
            raise RuntimeError(f"❌ Lỗi khi quét tệp với YARA: {e}")

    def scan_directory(self, directory: str, recursive: bool = True, 
                      filter_results: Optional[bool] = None) -> dict:
        """
        Scan all supported files in a directory.
        
        Args:
            directory: Directory path to scan
            recursive: Whether to scan subdirectories
            filter_results: Override auto_filter setting (None = use default)
            
        Returns:
            Dictionary mapping file paths to their matches
        """
        results = {}
        dir_path = Path(directory)
        
        if not dir_path.is_dir():
            raise NotADirectoryError(f"❌ Không phải thư mục: {directory}")
        
        pattern = "**/*" if recursive else "*"
        scanned_count = 0
        
        for file_path in dir_path.glob(pattern):
            if file_path.is_file() and self._is_supported_file(file_path):
                scanned_count += 1
                try:
                    matches = self.scan_file(str(file_path), filter_results=filter_results)
                    if matches:
                        results[str(file_path)] = matches
                except Exception as e:
                    print(f"⚠️ Lỗi khi quét {file_path}: {e}")
        
        print(f"\n📊 Thống kê: Đã quét {scanned_count} file, phát hiện {len(results)} file nghi vấn.")
        return results

    @staticmethod
    def _decode_bytes(data: bytes) -> str:
        """Safely decode bytes to string."""
        try:
            return data.decode(errors="ignore")
        except Exception:
            return str(data)

    @staticmethod
    def print_match(match: yara.Match, verbose: bool = True) -> None:
        """
        Pretty print a YARA match result.
        
        Args:
            match: YARA match object
            verbose: Whether to print detailed information
        """
        print(f"- {match.rule}")
        
        if not verbose:
            return
            
        if match.tags:
            print(f"  ├─ Tags: {', '.join(match.tags)}")
        
        if match.meta:
            print(f"  ├─ Meta:")
            for key, value in match.meta.items():
                print(f"  │   {key}: {value}")
        
        if match.strings:
            print(f"  └─ Chuỗi trùng khớp ({len(match.strings)}):")
            for string_match in match.strings:
                YARAScanner._print_string_match(string_match)

    @staticmethod
    def _print_string_match(string_match) -> None:
        """Print individual string match (handles both old and new YARA versions)."""
        # YARA 4.x: StringMatch object with instances
        if hasattr(string_match, 'instances'):
            identifier = string_match.identifier
            for instance in string_match.instances:
                data = YARAScanner._decode_bytes(instance.matched_data) \
                       if isinstance(instance.matched_data, bytes) \
                       else instance.matched_data
                print(f"      • {identifier} at offset {instance.offset}: {data}")
        
        # YARA 3.x: tuple (offset, identifier, data)
        else:
            offset, identifier, data = string_match
            data = YARAScanner._decode_bytes(data) if isinstance(data, bytes) else data
            print(f"      • {identifier} at offset {offset}: {data}")

    def print_summary(self, results: dict, detailed: bool = False) -> None:
        """
        Print scan results summary.
        
        Args:
            results: Dictionary of scan results
            detailed: Show detailed match information
        """
        if not results:
            print("✅ Không phát hiện malware nào.")
            return
        
        print(f"\n🚨 CẢNH BÁO: Phát hiện {len(results)} file nghi vấn!")
        print("="*70)
        
        for file_path, matches in results.items():
            print(f"\n📁 File: {file_path}")
            print(f"   Phát hiện {len(matches)} rule:")
            
            for match in matches:
                if detailed:
                    self.print_match(match, verbose=True)
                else:
                    threat_type = "Unknown"
                    if match.tags:
                        if "apt" in [t.lower() for t in match.tags]:
                            threat_type = "APT"
                        elif "banker" in [t.lower() for t in match.tags]:
                            threat_type = "Banking Trojan"
                        elif "ransom" in [t.lower() for t in match.tags]:
                            threat_type = "Ransomware"
                    
                    description = match.meta.get('description', 'No description') if match.meta else 'No description'
                    print(f"   • [{threat_type}] {match.rule}: {description}")
        
        print("="*70)


def main():
    """Example usage of YARAScanner."""
    test_file = "./.examples/malware.exe"
    
    try:
        print("🚀 Khởi tạo YARA Scanner với bộ lọc thông minh...\n")
        
        # Khởi tạo scanner với auto-filter BẬT (khuyến nghị)
        scanner = YARAScanner(auto_filter=True)
        
        print(f"🔍 Đang quét file: {test_file}\n")
        results = scanner.scan_file(test_file)
        
        if results:
            print(f"🚨 Phát hiện {len(results)} malware signature trong {test_file}:")
            print("="*70)
            for match in results:
                scanner.print_match(match, verbose=True)
            print("="*70)
        else:
            print(f"✅ File sạch - Không phát hiện malware trong {test_file}")
        
        # Demo: So sánh với chế độ không lọc
        print("\n" + "="*70)
        print("📊 So sánh: Quét không có bộ lọc (để thấy sự khác biệt)")
        print("="*70)
        results_unfiltered = scanner.scan_file(test_file, filter_results=False)
        print(f"Không lọc: {len(results_unfiltered)} kết quả")
        print(f"Có lọc:    {len(results)} kết quả")
        print(f"Đã loại bỏ: {len(results_unfiltered) - len(results)} false positive")
        
    except FileNotFoundError:
        print(f"⚠️ File demo không tồn tại: {test_file}")
        print("💡 Sử dụng: scanner.scan_file('path/to/your/file.exe')")
    except Exception as e:
        print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    main()