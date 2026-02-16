import requests
import re

def get_java_filename(code):
    public_class_match = re.search(r'public\s+class\s+([a-zA-Z0-9_$]+)', code)
    if public_class_match:
        return f"{public_class_match.group(1)}.java"
    class_match = re.search(r'class\s+([a-zA-Z0-9_$]+)', code)
    if class_match:
        return f"{class_match.group(1)}.java"
    return "Main.java"

code = """
public class AddTwoNumbers {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
"""

filename = get_java_filename(code)
print(f"Detected filename: {filename}")

PISTON_MIRRORS = [
    "https://emkc.org/api/v2/piston/execute",
    "https://piston.p-as.io/api/v2/piston/execute",
    "https://piston.sh/api/v2/piston/execute",
    "https://piston.rinstun.com/api/v2/piston/execute"
]

payload = {
    "language": "java",
    "version": "15.0.2",
    "files": [{"name": filename, "content": code}]
}

for url in PISTON_MIRRORS:
    print(f"\nTesting {url}...")
    try:
        resp = requests.post(url, json=payload, timeout=5)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print("Output:", data.get("run", {}).get("stdout", "No stdout"))
            print("Error:", data.get("run", {}).get("stderr", "No stderr"))
            print("Compile Error:", data.get("compile", {}).get("stderr", "No compile error"))
        else:
            print(f"Response: {resp.text[:100]}")
    except Exception as e:
        print(f"Failed: {e}")
