#!/usr/bin/env python3
import requests, re

resp = requests.post("http://localhost:8191/v1", json={
    "cmd": "request.get",
    "url": "https://coomer.st/onlyfans/user/myla.feet/post/1656935141",
    "maxTimeout": 60000
}, timeout=120)

result = resp.json()
if result.get("status") == "ok":
    html = result.get("solution", {}).get("response", "")
    pattern = r'https://n\d+\.coomer\.st/data/[^"]+\.mp4[^"]*'
    matches = re.findall(pattern, html)
    print(f"Found {len(matches)} video links:")
    for m in matches[:5]:
        print(f"  {m}")
else:
    print(f"Error: {result}")
