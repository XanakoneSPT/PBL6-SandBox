"""
Malware Bazaar API Client
Simple API for checking a single file hash against Malware Bazaar database.
Designed for backend integration - one hash at a time.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Malware Bazaar API configuration
API_URL = "https://mb-api.abuse.ch/api/v1/"
API_KEY = os.getenv('MALWAREBAZAAR_API_KEY')


def check_hash(hash_value, hash_type="sha256"):
    """
    Query Malware Bazaar API to check if a hash is known as malicious.
    
    Args:
        hash_value (str): The hash value to check (MD5, SHA1, or SHA256)
        hash_type (str): Type of hash - "md5", "sha1", or "sha256" (default: "sha256")
    
    Returns:
        dict: Structured response with the following format:
            {
                "success": bool,           # Whether the API call succeeded
                "is_malicious": bool,      # True if hash found in malware database
                "error": str or None,      # Error message if any
                "query_status": str,       # API query status
                "malware_info": dict or None,  # Malware details if found
                "raw_response": dict       # Full API response
            }
    
    Example:
        >>> result = check_hash("abc123...", "sha256")
        >>> if result["is_malicious"]:
        >>>     print(f"Malware detected: {result['malware_info']['signature']}")
    """
    # Validate API key
    if not API_KEY or API_KEY == "your_api_key_here":
        return {
            "success": False,
            "is_malicious": False,
            "error": "API key not configured. Please add MALWAREBAZAAR_API_KEY to .env file",
            "query_status": "error",
            "malware_info": None,
            "raw_response": None
        }
    
    # Prepare API request
    headers = {'Auth-Key': API_KEY}
    data = {
        'query': 'get_info',
        'hash': hash_value
    }
    
    try:
        # Make API request
        response = requests.post(API_URL, data=data, headers=headers, timeout=10)
        
        # Handle authentication errors
        if response.status_code == 401:
            return {
                "success": False,
                "is_malicious": False,
                "error": "Authentication failed (401 Unauthorized). Invalid or expired API key",
                "query_status": "error",
                "malware_info": None,
                "raw_response": None
            }
        
        response.raise_for_status()
        api_response = response.json()
        
        # Parse API response
        query_status = api_response.get('query_status')
        
        if query_status == 'ok':
            # Hash found - it's malicious
            malware_data = api_response.get('data', [{}])[0]
            return {
                "success": True,
                "is_malicious": True,
                "error": None,
                "query_status": query_status,
                "malware_info": {
                    "file_name": malware_data.get('file_name'),
                    "file_type": malware_data.get('file_type'),
                    "file_size": malware_data.get('file_size'),
                    "signature": malware_data.get('signature'),
                    "first_seen": malware_data.get('first_seen'),
                    "last_seen": malware_data.get('last_seen'),
                    "reporter": malware_data.get('reporter'),
                    "tags": malware_data.get('tags', []),
                    "imphash": malware_data.get('imphash'),
                    "tlsh": malware_data.get('tlsh'),
                    "md5": malware_data.get('md5_hash'),
                    "sha1": malware_data.get('sha1_hash'),
                    "sha256": malware_data.get('sha256_hash')
                },
                "raw_response": api_response
            }
        
        elif query_status in ['no_results', 'hash_not_found']:
            # Hash not found - appears safe
            return {
                "success": True,
                "is_malicious": False,
                "error": None,
                "query_status": query_status,
                "malware_info": None,
                "raw_response": api_response
            }
        
        else:
            # Unknown status
            return {
                "success": False,
                "is_malicious": False,
                "error": f"Unknown query status: {query_status}",
                "query_status": query_status,
                "malware_info": None,
                "raw_response": api_response
            }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "is_malicious": False,
            "error": "API request timed out",
            "query_status": "error",
            "malware_info": None,
            "raw_response": None
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "is_malicious": False,
            "error": f"API request failed: {str(e)}",
            "query_status": "error",
            "malware_info": None,
            "raw_response": None
        }


def get_api_status():
    """
    Check if the API key is configured and valid.
    
    Returns:
        dict: API status information
            {
                "configured": bool,
                "valid": bool or None,  # None if not tested
                "error": str or None
            }
    """
    if not API_KEY or API_KEY == "your_api_key_here":
        return {
            "configured": False,
            "valid": None,
            "error": "API key not configured"
        }
    
    # Test with a known hash (empty file SHA256)
    test_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    try:
        headers = {'Auth-Key': API_KEY}
        data = {'query': 'get_info', 'hash': test_hash}
        response = requests.post(API_URL, data=data, headers=headers, timeout=10)
        
        if response.status_code == 401:
            return {
                "configured": True,
                "valid": False,
                "error": "Invalid or expired API key"
            }
        
        response.raise_for_status()
        return {
            "configured": True,
            "valid": True,
            "error": None
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "configured": True,
            "valid": None,
            "error": f"API connection failed: {str(e)}"
        }


if __name__ == "__main__":
    # Example usage - pass a hash as command line argument
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python malware_api.py <hash_value>")
        print("\nExample:")
        print("  python malware_api.py e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        sys.exit(1)
    
    test_hash = sys.argv[1]
    print("Testing Malware Bazaar API Client\n")
    print(f"Checking hash: {test_hash}\n")
    
    # Check API status
    status = get_api_status()
    print(f"API Status: {status}\n")
    
    if status["valid"]:
        # Check the provided hash
        result = check_hash(test_hash)
        
        print(f"Test Hash: {test_hash}")
        print(f"Is Malicious: {result['is_malicious']}")
        print(f"Query Status: {result['query_status']}")
        if result['malware_info']:
            print(f"\nMalware Info:")
            for key, value in result['malware_info'].items():
                if value:
                    print(f"  {key}: {value}")

