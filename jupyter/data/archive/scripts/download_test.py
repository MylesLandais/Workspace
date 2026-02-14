#!/usr/bin/env python3
"""
Simple test to download coomer.st image to /home/warby/Workspace/jupyter/downloads
"""
import requests
import os

def download_test_image():
    test_url = "https://n2.coomer.st/data/95/0e/950edd72eb25e2dbf68df53dc8a25a623dd7908fe3235dcb615e2d1aec282bb5.jpg?f=3024x4032_b7898edf0e788b9f3a34d6ab13bc36fa.jpg"
    local_path = "/home/warby/Workspace/jupyter/downloads/myla.feet_test.jpg"
    
    print(f"Testing download from coomer.st...")
    print(f"URL: {test_url}")
    print(f"Local: {local_path}")
    
    # Create directory if needed
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    try:
        response = requests.get(test_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://coomer.st/',
            'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        }, timeout=30)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            size = len(response.content)
            print(f"✅ Downloaded: {local_path}")
            print(f"Size: {size:,} bytes ({size/1024:.1f} KB)")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    download_test_image()