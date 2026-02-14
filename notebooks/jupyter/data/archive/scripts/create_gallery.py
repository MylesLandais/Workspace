"""Create gallery viewer for cached images."""

import sys
import re
from pathlib import Path


def create_gallery_viewer(cache_root: Path = None, output_file: Path = None):
    """Create HTML gallery viewer."""
    if cache_root is None:
        cache_root = Path("cache/imageboard")
    
    html_dir = cache_root / "html"
    images_dir = cache_root / "images"
    
    if output_file is None:
        output_file = html_dir / "gallery.html"
    
    # Create gallery HTML
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Imageboard Archive Gallery</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background: #1a1a1a; color: #ddd; }
        h1 { color: #fff; border-bottom: 2px solid #444; padding-bottom: 10px; }
        .threads { margin-top: 30px; }
        .thread { margin: 20px 0; padding: 20px; background: #2a2a2a; border-radius: 8px; border: 1px solid #444; }
        .thread h2 { margin-top: 0; color: #6cb3d9; }
        .thread h2 a { text-decoration: none; }
        .thread h2 a:hover { text-decoration: underline; }
        .meta { color: #888; font-size: 0.9em; margin: 10px 0; }
        .images { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; margin: 20px 0; }
        .image-card { background: #3a3a3a; border-radius: 4px; padding: 10px; border: 1px solid #444; }
        .image-card img { max-width: 100%; height: auto; display: block; }
        .image-name { font-size: 0.8em; color: #888; margin-top: 5px; word-break: break-all; }
        .more { text-align: center; color: #888; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🖼️ Imageboard Archive Gallery</h1>
    <p style="color: #888;">Locally cached images from monitored threads</p>
    <div class="threads">
"""
    
    # Add each thread
    for html_file in sorted(html_dir.glob("*.html"), reverse=True):
        if "_local" in html_file.name or html_file.name == "index.html" or html_file.name == "gallery.html":
            continue
        
        match = re.match(r'(\w+)_(\d+)', html_file.stem)
        if not match:
            continue
        
        board, thread_id = match.groups()
        
        thread_images_dir = images_dir / board / thread_id
        image_count = 0
        
        if thread_images_dir.exists():
            images = list(thread_images_dir.iterdir())
            image_count = len(images)
            
            html += f"""
        <div class="thread">
            <h2>/{board}/{thread_id}</h2>
            <div class="meta">{image_count} images cached locally</div>
            <div class="images">
"""
            
            for img_file in sorted(images)[:20]:
                rel_path = img_file.relative_to(cache_root)
                html += f"""
                <div class="image-card">
                    <a href="../{rel_path}" target="_blank">
                        <img src="../{rel_path}" loading="lazy" alt="{img_file.name}">
                    </a>
                    <div class="image-name">{img_file.name[:40]}</div>
                </div>
"""
            
            if image_count > 20:
                html += f'<div class="more"><em>+{image_count - 20} more images</em></div>'
            
            html += """
            </div>
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    output_file.write_text(html, encoding='utf-8')
    print(f"Created gallery: {output_file}")
    print(f"Open in browser: file://{output_file.absolute()}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create gallery viewer for cached images"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("cache/imageboard"),
        help="Cache directory"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file"
    )
    
    args = parser.parse_args()
    
    create_gallery_viewer(args.cache_dir, args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
