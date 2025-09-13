import requests

# 🔑 Get your API key: https://www.hybrid-analysis.com/ -> Sign up -> API Key
API_KEY = "YOUR_API_KEY_HERE"
FILE_PATH = "test.exe"   # change to your sample file

url = "https://www.hybrid-analysis.com/api/v2/submit/file"
headers = {
    "User-Agent": "Falcon Sandbox",   # required by Hybrid Analysis
    "api-key": API_KEY
}

# Upload file
with open(FILE_PATH, "rb") as f:
    files = {"file": (FILE_PATH, f)}
    data = {
        "environment_id": "120"  # Windows 10 64-bit; other options possible
    }
    resp = requests.post(url, headers=headers, files=files, data=data)

print("Upload response:", resp.json())
