import requests
import json

MIRRORS = [
    "https://emkc.org/api/v2/piston/execute",
    "https://piston.pydis.com/api/v2/piston/execute",
    "https://piston.engineer-man.com/api/v2/piston/execute",
    "https://piston.kimb.dev/api/v2/piston/execute",
    "https://api.piston.dev/api/v2/piston/execute"
]

C_CODE = """
#include <stdio.h>
#include <math.h>

int main() {
    double result = pow(2, 3);
    printf("2^3 = %.1f\\n", result);
    return 0;
}
"""

payload = {
    "language": "c",
    "version": "10.2.0",
    "files": [{"name": "main.c", "content": C_CODE}]
}

print("Testing C Math Library (pow) across Piston mirrors...")

for url in MIRRORS:
    print(f"\n--- Testing {url} ---")
    try:
        resp = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            run = data.get("run", {})
            compile_val = data.get("compile", {})
            
            if compile_val.get("stderr"):
                print(f"Compile Error:\n{compile_val['stderr']}")
            elif run.get("stderr"):
                print(f"Run Error:\n{run['stderr']}")
            else:
                print(f"Stdout: {run.get('stdout')}")
        else:
            print(f"Error: {resp.text[:100]}")
    except Exception as e:
        print(f"Exception: {str(e)}")

print("\nTesting complete.")
