import requests
import json

targets = [
    ("Official Piston", "https://emkc.org/api/v2/piston/execute"),
    ("P-AS Mirror", "https://piston.p-as.io/api/v2/piston/execute"),
    ("Judge0 Public", "https://ce.judge0.com/submissions?base64_encoded=false&wait=true")
]

payload_piston = {
    "language": "python",
    "version": "3.10.0",
    "files": [{"content": "print('SUCCESS')"}]
}

payload_judge0 = {
    "source_code": "print('SUCCESS')",
    "language_id": 71
}

for name, url in targets:
    print(f"Testing {name} at {url}...")
    try:
        if "piston" in url or "emkc" in url:
            p = payload_piston
        else:
            p = payload_judge0
            
        response = requests.post(url, json=p, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)
