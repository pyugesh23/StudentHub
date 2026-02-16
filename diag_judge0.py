import requests
import json

url = "https://ce.judge0.com/submissions?wait=true"
payload = {
    "source_code": 'print("Hello")',
    "language_id": 71,
    "stdin": ""
}

print("Testing WITHOUT base64_encoded=false...")
try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("-" * 20)
print("Testing WITH base64_encoded=false...")
try:
    url_v2 = "https://ce.judge0.com/submissions?base64_encoded=false&wait=true"
    response = requests.post(url_v2, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
