#!/usr/bin/env python3
"""
Debug FlareSolverr response
"""

import requests
import json

def test_flaresolverr():
    url = "http://localhost:8191/v1"
    
    payload = {
        "cmd": "request.get",
        "url": "https://coomer.st/api/v1/onlyfans/user/myla.feet/posts",
        "maxTimeout": 60000,
        "headers": {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://coomer.st/'
        }
    }
    
    print("Sending to FlareSolverr:", json.dumps(payload, indent=2))
    
    response = requests.post(url, json=payload, timeout=120)
    print("Status:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))
    
    # Check if we can parse the solution content
    result = response.json()
    if result.get("status") == "ok":
        solution = result.get("solution", {})
        content = solution.get("response", "")
        print("Content length:", len(content))
        print("Content preview:", content[:500])
        
        # Try to parse as JSON
        try:
            parsed = json.loads(content)
            print("✅ JSON is valid")
            print("Keys:", list(parsed.keys()) if isinstance(parsed, dict) else "Not a dict")
        except json.JSONDecodeError as e:
            print("❌ JSON decode error:", e)
            print("First 1000 chars:", content[:1000])

if __name__ == '__main__':
    test_flaresolverr()