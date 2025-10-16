"""
Simple script to test if your Malware Bazaar API key is working correctly.
"""

import os
import requests
from dotenv import load_dotenv
from colorama import init, Fore, Style

init(autoreset=True)
load_dotenv()

API_KEY = os.getenv('MALWAREBAZAAR_API_KEY')
API_URL = "https://mb-api.abuse.ch/api/v1/"

print(f"{Fore.CYAN}{Style.BRIGHT}Testing Malware Bazaar API Key...")
print(f"{Style.BRIGHT}{'='*60}\n")

# Check if API key is set
if not API_KEY or API_KEY == "your_api_key_here":
    print(f"{Fore.RED}✗ API key not found or not configured!")
    print(f"\n{Fore.YELLOW}Steps to configure:")
    print(f"1. Get a free API key from: https://bazaar.abuse.ch/api/")
    print(f"2. Create/edit .env file in this directory")
    print(f"3. Add this line: MALWAREBAZAAR_API_KEY=your_actual_key")
    exit(1)

print(f"{Fore.GREEN}✓ API key found in .env file")
print(f"  Key: {API_KEY[:10]}{'*' * (len(API_KEY) - 10)}\n")

# Test with a known malware hash (WannaCry sample)
# This is a well-known malware sample that should be in the database
# test_hash = "ed01ebfbc9eb5bbea545af4d01bf5f1071661840480439c6e5babe8e080e41aa"
test_hash = "5a4eaf32d0659b7901cf0c8414447abf7729f191ee9117afdabbb67d10367f27"

print(f"{Fore.CYAN}Testing API connection...")
print(f"Using test hash: {test_hash[:32]}...\n")

headers = {'Auth-Key': API_KEY}
data = {
    'query': 'get_info',
    'hash': test_hash
}

try:
    response = requests.post(API_URL, data=data, headers=headers, timeout=10)
    
    print(f"Response Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print(f"{Fore.GREEN}✓ API connection successful!")
        
        result = response.json()
        query_status = result.get('query_status')
        
        print(f"\nQuery Status: {query_status}")
        
        if query_status == 'ok':
            print(f"{Fore.GREEN}✓ API is working correctly!")
            print(f"\n{Fore.CYAN}Sample data retrieved:")
            data = result.get('data', [{}])[0]
            print(f"  File Name: {data.get('file_name', 'N/A')}")
            print(f"  Signature: {data.get('signature', 'N/A')}")
            print(f"  First Seen: {data.get('first_seen', 'N/A')}")
        elif query_status in ['no_results', 'hash_not_found']:
            print(f"{Fore.GREEN}✓ API is working (hash not found in database)")
        else:
            print(f"{Fore.YELLOW}⚠ Unexpected status: {query_status}")
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}✓ Your API key is configured correctly!")
        print(f"{Fore.GREEN}You can now use: python malware_checker.py examples")
        
    elif response.status_code == 401:
        print(f"{Fore.RED}✗ Authentication failed (401 Unauthorized)")
        print(f"\n{Fore.YELLOW}Your API key is invalid or expired.")
        print(f"Please check:")
        print(f"1. The key in your .env file is correct")
        print(f"2. The key hasn't expired")
        print(f"3. Get a new key from: https://bazaar.abuse.ch/api/")
        
    else:
        print(f"{Fore.RED}✗ Unexpected status code: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"{Fore.RED}✗ Request failed: {e}")
    print(f"\n{Fore.YELLOW}Possible issues:")
    print(f"- Internet connection problem")
    print(f"- Malware Bazaar API is down")
    print(f"- Firewall blocking the request")

print(f"\n{Style.BRIGHT}{'='*60}")

