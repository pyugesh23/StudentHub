import requests
import time

PISTON_MIRRORS = [
    "https://emkc.org/api/v2/piston/execute",
    "https://piston.pydis.com/api/v2/piston/execute",
    "https://piston.engineer-man.com/api/v2/piston/execute",
    "https://piston.kimb.dev/api/v2/piston/execute",
    "https://api.piston.dev/api/v2/piston/execute"
]

payload = {
    "language": "python",
    "version": "3.10.0",
    "files": [{"content": "print('speed test')"}]
}

results = []

for url in PISTON_MIRRORS:
    print(f"Testing {url}...")
    start = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=5)
        duration = time.time() - start
        if resp.status_code == 200:
            print(f"Success: {duration:.2f}s")
            results.append((url, duration))
        else:
            print(f"Failed: {resp.status_code}")
    except Exception as e:
        print(f"Error: {e}")

print("\nResults (Fastest first):")
for url, dur in sorted(results, key=lambda x: x[1]):
    print(f"{dur:.2f}s - {url}")
