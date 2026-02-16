import requests
import json

endpoints = [
    "https://piston.p-as.io/api/v2/piston/execute",
    "https://piston.engineeringman.ga/api/v2/piston/execute",
    "https://piston.sh/api/v2/piston/execute",
    "https://piston.okand.dev/api/v2/piston/execute"
]

payload = {
    "language": "python",
    "version": "3.10.0",
    "files": [{"content": 'print("Test Success")'}]
}

for url in endpoints:
    print(f"Testing {url}...")
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json().get('run', {}).get('stdout', '').strip()}")
            print("WORKING!")
        else:
            print(f"Error: {response.text[:100]}")
    except Exception as e:
        print(f"Failed: {str(e)}")
    print("-" * 20)
