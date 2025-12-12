# generate_yara_test_files.py
from pathlib import Path
import base64

def make_obfuscated_html():
    # Typical JS obfuscation pattern to trigger packers/Javascript_exploit_and_obfuscation.yar or JJencode.yar
    js_obfus = """
    <html><body><script>
    // Fake obfuscated payload for testing YARA JS obfuscation rules
    eval(function(p,a,c,k,e,d){e=function(c){return c.toString(a)};if(!''.replace(/^/,String)){while(c--)d[e(c)]=k[c]||e(c);k=[function(e){return d[e]}];e=function(){return'\\\\w+'};c=1};while(c--)if(k[c])p=p.replace(new RegExp('\\\\b'+e(c)+'\\\\b','g'),k[c]);return p}('alert(1);',2,2,'alert|1'.split('|'),0,{}));
    // Add a long base64 chunk to trigger base64.yar
    var b64 = "%s";
    </script></body></html>
    """ % base64.b64encode(b"A"*400).decode()

    Path("yara_test_obfus.html").write_text(js_obfus, encoding="utf-8")
    print("Wrote yara_test_obfus.html")

def make_suspicious_bin():
    # Strings commonly flagged by suspicious_strings.yar, url.yar, utils/url.yar, etc.
    suspicious_strings = [
        b"powershell -enc AAAA",              # encoded PowerShell usage
        b"cmd.exe /c",                        # command shell
        b"vssadmin delete shadows /all /quiet", # ransomware-like behavior
        b"http://malicious.example.com/c2",   # C2-style URL
        b"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",  # persistence
        b"Base64: " + base64.b64encode(b"evilpayload"*20),           # long base64
    ]
    data = b"\n".join(suspicious_strings)
    Path("yara_test_bin.bin").write_bytes(data)
    print("Wrote yara_test_bin.bin")

if __name__ == "__main__":
    make_obfuscated_html()
    make_suspicious_bin()