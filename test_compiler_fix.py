import requests
import json

MIRRORS = [
    "https://p-as.io/api/v2/piston/execute",
    "https://piston.sh/api/v2/piston/execute",
    "https://rinstun.com/api/v2/piston/execute",
    "https://emkc.org/api/v2/piston/execute"
]

JUDGE0_URL = "https://ce.judge0.com/submissions?base64_encoded=false&wait=true"

def test_piston(url):
    payload = {
        "language": "python",
        "version": "3.10.0",
        "files": [{"name": "main.py", "content": "print('Piston Success')"}]
    }
    try:
        resp = requests.post(url, json=payload, timeout=5)
        return resp.status_code, resp.text[:100]
    except Exception as e:
        return "Error", str(e)

def test_judge0():
    payload = {
        "source_code": "print('Judge0 Success')",
        "language_id": 71,
        "stdin": ""
    }
    try:
        resp = requests.post(JUDGE0_URL, json=payload, timeout=10)
        return resp.status_code, resp.text[:100]
    except Exception as e:
        return "Error", str(e)

print("--- Testing Piston Mirrors ---")
for url in MIRRORS:
    status, text = test_piston(url)
    print(f"{url}: {status} - {text}")

print("\n--- Testing Judge0 ---")
status, text = test_judge0()
print(f"Judge0: {status} - {text}")
