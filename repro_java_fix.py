import requests
import json

code = """
public class PrintNumbers {
    public static void main(String[] args) {
        for (int i = 1; i <= 10; i++) {
            System.out.println(i);
        }
    }
}
"""

url = "https://emkc.org/api/v2/piston/execute"
payload = {
    "language": "java",
    "version": "15.0.2",
    "files": [{"content": code}]
}

print("Testing WITHOUT filename...")
response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
print(response.json().get("compile", {}).get("stderr", "No compile error"))
print(response.json().get("run", {}).get("stderr", "No run error"))

payload_fixed = {
    "language": "java",
    "version": "15.0.2",
    "files": [{"name": "PrintNumbers.java", "content": code}]
}

print("\nTesting WITH filename (PrintNumbers.java)...")
response = requests.post(url, json=payload_fixed)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(response.json().get("run", {}).get("stdout", "No output"))
else:
    print(response.text)
