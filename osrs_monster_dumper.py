import requests
import json
import re
import os
import urllib.request
import urllib.parse
import hashlib
import time
from pathlib import Path
from bs4 import BeautifulSoup

BASE_URL = 'https://oldschool.runescape.wiki'
HEADERS = {
    'User-Agent': 'OSRSMonsterDumper/1.0 (https://github.com/warby/Jupyter; warby@github.com)'
}

def get_all_monster_links():
    """Fetch all monster page links via HTML scraping."""
    monster_links = []
    
    # Get the main category page to find all pagination links
    main_page = requests.get(f"{BASE_URL}/w/Category:Monsters", headers=HEADERS)
    soup = BeautifulSoup(main_page.text, 'html.parser')
    
    # Find pagination links (letters A-Z, 0-9)
    pagination_links = set()
    for link in soup.find_all('a', href=re.compile(r'/w/Category:Monsters\?from=')):
        href = link['href']
        if href not in pagination_links:
            pagination_links.add(href)
    
    # Add the main page
    all_pages = ['/w/Category:Monsters'] + list(pagination_links)
    
    print(f"Found {len(all_pages)} category pages to scrape")
    
    # Scrape each page
    for page_url in all_pages:
        full_url = page_url if page_url.startswith('http') else f"{BASE_URL}{page_url}"
        print(f"Scraping {full_url}")
        response = requests.get(full_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract monster links
        for link in soup.find_all('a', href=re.compile(r'^/w/')):
            href = link['href']
            title = link.get_text(strip=True)
            
            # Skip categories, templates, and special pages
            if any(x in href for x in ['/w/Category:', '/w/Template:', '/w/Special:', '/w/User:', '/w/File:', '/w/Help:']):
                continue
            
            # Skip non-monster pages
            if title in ['monsters', 'Monster']:
                continue
                
            # Extract just the page name
            if href.startswith('/w/'):
                page_name = href[3:]
                if page_name and page_name not in monster_links:
                    monster_links.append(page_name)
        
        time.sleep(0.2)  # Polite delay
    
    print(f"Fetched {len(monster_links)} monster links.")
    return monster_links

def parse_infobox(wikitext):
    """Parse Infobox Monster params from wikitext."""
    match = re.search(r'\{\{Infobox\s+Monster\s*(.*?)\}\}', wikitext, re.DOTALL | re.IGNORECASE)
    if not match:
        return {}
    infobox_text = match.group(1)
    params = {}
    for line in infobox_text.split('\n'):
        line = line.strip()
        m = re.match(r'\|\s*([^=]+?)\s*=\s*(.*)', line)
        if m:
            key = m.group(1).strip().lower().replace(' ', '_')
            val = m.group(2).strip()
            # Unescape wiki {{!}} -> |
            val = val.replace('{{!}}', '|')
            params[key] = val
    return params

def get_monster_data(title):
    """Fetch and parse single monster page."""
    url = f"{BASE_URL}/w/{urllib.parse.quote(title)}?action=raw"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            return None
        wikitext = response.text
        infobox = parse_infobox(wikitext)
        if not infobox:
            return None

        # Extract key fields
        combat_level = infobox.get('combat', '').strip()
        models_str = infobox.get('id', '').strip()
        models = [int(m.strip()) for m in models_str.split(',') if m.strip().isdigit()]
        
        npc_ids = []
        # Try to get npc ids from various infobox fields
        for i in range(1, 11):
            id_str = infobox.get(f'id{i}', '').strip()
            if id_str.isdigit():
                npc_ids.append(int(id_str))
        
        # Also try 'id' field which might contain comma-separated IDs
        if models:
            npc_ids.extend(models)
            npc_ids = list(set(npc_ids))  # Remove duplicates
        
        # Extract image from infobox
        image_file = None
        for key in infobox:
            if key.startswith('image'):
                image_match = re.search(r'\[\[File:([^\]|]+)', infobox[key])
                if image_match:
                    image_file = image_match.group(1).strip()
                    break
        
        # Build URLs
        wiki_url = f"{BASE_URL}/w/{urllib.parse.quote(title)}"
        image_url = None
        if image_file:
            # OSRS Wiki image URL format doesn't use MD5 hash prefix
            thumb_name = f"300px-{urllib.parse.quote(image_file)}"
            image_url = f"{BASE_URL}/images/thumb/{urllib.parse.quote(image_file)}/{thumb_name}"
        
        return {
            'name': title,
            'wiki_url': wiki_url,
            'combat_level': combat_level,
            'npc_ids': npc_ids,
            'models': models,
            'image_file': image_file,
            'image_url': image_url
        }
    except Exception as e:
        print(f"Error parsing {title}: {e}")
        return None

def download_image(image_url, filename):
    """Download image to folder."""
    try:
        os.makedirs('images', exist_ok=True)
        clean_filename = re.sub(r'[^\w\-_. ]', '_', filename)
        path = Path('images') / f"{clean_filename}.png"
        if path.exists():
            return True
        urllib.request.urlretrieve(image_url, path)
        return True
    except:
        return False

# MAIN
if __name__ == "__main__":
    print("Fetching monster list...")
    titles = get_all_monster_links()
    
    all_monsters = []
    for i, title in enumerate(titles, 1):
        print(f"Processing {i}/{len(titles)}: {title}")
        data = get_monster_data(title)
        if data:
            all_monsters.append(data)
            if data['image_url']:
                success = download_image(data['image_url'], data['name'])
                if not success:
                    print(f"  Failed to download image for {title}")
        time.sleep(0.2)  # Rate limit ~5 req/sec
    
    # Save JSON
    with open('monsters.json', 'w', encoding='utf-8') as f:
        json.dump(all_monsters, f, indent=2, ensure_ascii=False)
    
    print(f"\nDone! {len(all_monsters)} monsters dumped to monsters.json")
    print(f"Images in ./images/ ({len([m for m in all_monsters if m['image_url']])} downloaded)")
