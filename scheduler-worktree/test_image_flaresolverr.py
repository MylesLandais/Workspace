#!/usr/bin/env python3
"""
Test FlareSolverr with direct image URL
"""

import requests
import json

def test_image_download():
    url = "https://n2.coomer.st/data/95/0e/950edd72eb25e2dbf68df53dc8a25a623dd7908fe3235dcb615e2d1aec282bb5.jpg?f=3024x4032_b7898edf0e788b9f3a34d6ab13bc36fa.jpg"
    
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000,
        "headers": {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://coomer.st/'
        }
    }
    
    print("Testing image download via FlareSolverr...")
    
    response = requests.post("http://localhost:8191/v1", json=payload, timeout=120)
    print("Status:", response.status_code)
    
    result = response.json()
    if result.get("status") == "ok":
        solution = result.get("solution", {})
        content = solution.get("response", "")
        print("Content length:", len(content))
        print("Status:", solution.get("status"))
        
        if solution.get("status") == 200:
            # Save to file
            with open("test_image_flare.jpg", "wb") as f:
                f.write(content.encode() if isinstance(content, str) else content)
            print("✅ Image saved as test_image_flare.jpg")
        else:
            print("❌ Failed to get image, status:", solution.get("status"))
    else:
        print("❌ FlareSolverr failed:", result.get("message", "Unknown error"))

if __name__ == '__main__':
    test_image_download()