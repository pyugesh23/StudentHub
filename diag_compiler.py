import requests
import json

MIRRORS = [
    "https://piston.pydis.com/api/v2/piston/execute",
    "https://piston.engineer-man.com/api/v2/piston/execute",
    "https://piston.kimb.dev/api/v2/piston/execute",
    "https://api.piston.dev/api/v2/piston/execute",
    "https://emkc.org/api/v2/piston/execute"
]

payload = {
    "language": "python",
    "version": "*",
    "files": [{"content": "print(1+1)"}]
}

headers = {
    "User-Agent": "StudentHub-Compiler/1.1",
    "Accept": "application/json"
}

print("Starting deep diagnostic test...")

for url in MIRRORS:
    print(f"\n--- Testing {url} ---")
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status Code: {resp.status_code}")
        print(f"Response Body: {resp.text[:500]}")
    except requests.exceptions.Timeout:
        print("Error: Connection Timed Out")
    except requests.exceptions.SSLError as e:
        print(f"Error: SSL Verification Failed: {str(e)}")
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Connection Refused or DNS Fail: {str(e)}")
    except Exception as e:
        print(f"Error: Unexpected Exception: {type(e).__name__}: {str(e)}")

print("\nDiagnostic complete.")
