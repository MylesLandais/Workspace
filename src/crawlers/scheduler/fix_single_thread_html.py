import sys
sys.path.insert(0, '/home/jovyan/workspaces/src')
from pathlib import Path
from bs4 import BeautifulSoup
import re

# Container paths
CACHE_DIR = Path('/home/jovyan/workspaces/cache/imageboard')
BOARD = 'b'
THREAD_ID = '944488457'
HTML_PATH = CACHE_DIR / 'html' / f'{BOARD}_{THREAD_ID}.html'

def rewrite_html_with_local_links(html_text):
    """
    Rewrite HTML to use local images by inferring local filenames from external URLs.
    Uses URL inference, independent of thread.json.
    """
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # Remove base tag
    base_tag = soup.find('base')
    if base_tag:
        base_tag.decompose()

    # HTML is in 'html/' dir, so path is '../shared_images/'
    shared_images_prefix = "../shared_images/"

    # --- Fix CSS/JS links ---
    for tag in soup.find_all(['link', 'script']):
        attr = 'href' if tag.name == 'link' else 'src'
        if tag.has_attr(attr):
            val = tag[attr].split('?')[0]
            if val.startswith('//') or val.startswith('/'):
                path_parts = val.split('/')
                if len(path_parts) >= 2:
                    resource_dir = path_parts[-2]
                    filename = path_parts[-1]
                    
                    if resource_dir in ['css', 'js']:
                        tag[attr] = f"../{resource_dir}/{filename}"

    # --- Fix non-image external links to be absolute to 4chan ---
    for tag in soup.find_all(['a', 'form']):
        for attr in ['href', 'action']:
            if tag.has_attr(attr):
                val = tag[attr]
                # Skip external image URLs
                if re.match(r'^//i\.4cdn\.org/', val):
                    continue

                if val.startswith('//'):
                    tag[attr] = 'https:' + val
                elif val.startswith('/') and not val.startswith('//'):
                    tag[attr] = 'https://boards.4chan.org' + val
                elif not val.startswith('http') and not val.startswith('#') and not val.startswith('javascript'):
                    tag[attr] = f"https://boards.4chan.org/{BOARD}/" + val

    # --- Fix Image Links (URL Inference) ---
    updated_count = 0
    
    for tag in soup.find_all(['a', 'img']):
        attr = 'href' if tag.name == 'a' else 'src'
        
        if tag.has_attr(attr):
            val = tag[attr]
            
            if re.match(r'^//i\.4cdn\.org/', val):
                local_filename = Path(val).name
                tag[attr] = f"{shared_images_prefix}{local_filename}"
                
                if tag.name == 'a' and 'fileThumb' in tag.get('class', []):
                    updated_count += 1
                
            if tag.name == 'img' and tag.has_attr('srcset'):
                del tag['srcset']
    
    return soup.prettify(), updated_count

def main():
    if not HTML_PATH.exists():
        print(f"ERROR: HTML file not found: {HTML_PATH}")
        return

    print(f"Fixing HTML file: {HTML_PATH}")
    
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html_text = f.read()
    
    updated_html, count = rewrite_html_with_local_links(html_text)
    
    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(updated_html)
    
    print(f"Successfully fixed {HTML_PATH.name} ({count} images).")

if __name__ == "__main__":
    main()