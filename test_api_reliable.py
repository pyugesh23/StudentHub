import requests
import json
import os

log_file = "api_test_results.txt"

with open(log_file, "w") as f:
    f.write("Starting API Tests\n")
    f.write("="*20 + "\n")

endpoints = [
    "https://piston.p-as.io/api/v2/piston/execute",
    "https://piston.sh/api/v2/piston/execute",
    "https://piston.okand.dev/api/v2/piston/execute",
    "https://piston.everythingis.online/api/v2/piston/execute",
    "https://piston.pistonapi.com/api/v2/piston/execute",
]

payload = {
    "language": "python",
    "version": "3.10.0",
    "files": [{"content": 'print("SUCCESS")'}]
}

for url in endpoints:
    msg = f"Testing {url}...\n"
    print(msg)
    with open(log_file, "a") as f:
        f.write(msg)
    try:
        response = requests.post(url, json=payload, timeout=10)
        res_msg = f"Status: {response.status_code}\n"
        if response.status_code == 200:
            res_msg += f"Response: {response.json().get('run', {}).get('stdout', '').strip()}\n"
            res_msg += "WORKING!\n"
        else:
            res_msg += f"Error: {response.text[:200]}\n"
    except Exception as e:
        res_msg = f"Failed: {str(e)}\n"
    
    print(res_msg)
    with open(log_file, "a") as f:
        f.write(res_msg + "-" * 20 + "\n")

print(f"Tests complete. Results written to {log_file}")
