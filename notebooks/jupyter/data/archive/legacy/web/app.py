from flask import Flask, render_template_string, send_from_directory, request, jsonify
import pandas as pd
from pathlib import Path
import os
from datetime import datetime
import re
import mysql.connector
from archiver_lib import ArchiveLibrary

app = Flask(__name__)

# Configuration
BASE_DIR = Path(os.environ.get('DATA_DIR', '/home/warby/Workspace/jupyter'))
PARQUET_FILE = BASE_DIR / 'datasets' / 'parquet' / 'imageboard_weekly_latest.parquet'
CACHE_DIR = BASE_DIR / 'cache' / 'imageboard'
SHARED_IMAGES_DIR = CACHE_DIR / 'shared_images'

# DB Config for Curation (Legacy MySQL)
DB_CONFIG = {
    'host': 'mysql-scheduler.jupyter.dev.local',
    'user': 'root',
    'password': 'secret',
    'database': 'archive_system'
}

# DB Config for Curation (Converged Postgres)
PG_CONFIG = {
    'host': 'archive_postgres',
    'user': 'postgres',
    'password': 'secret',
    'dbname': 'archive_system'
}

# Initialize Shared Library
archive = ArchiveLibrary(str(PARQUET_FILE), curation_db_config=DB_CONFIG, postgres_config=PG_CONFIG)

# HTML Template (High-Quality Archive Aesthetic with Smart Search & Reverse Lookup)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Archive Search</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-body: #1d1f21;
            --bg-panel: #282a2e;
            --text-primary: #c5c8c6;
            --text-secondary: #969896;
            --accent: #81a2be;
            --border: #373b41;
            --soft-red: #f87171;
            --post-bg: #282a2e;
            --reply-bg: #373b41;
            --name-color: #b5bd68;
        }
        body { background-color: var(--bg-body); color: var(--text-primary); font-family: 'Segoe UI', Arial, sans-serif; }
        
        /* Layout */
        .sidebar {
            position: fixed; top: 56px; bottom: 0; left: 0; z-index: 100;
            padding: 20px 15px; overflow-x: hidden; overflow-y: auto;
            background-color: var(--bg-panel); border-right: 1px solid var(--border);
            width: 260px;
        }
        .main-content { margin-left: 260px; padding: 20px; padding-top: 76px; }
        
        /* Navbar */
        .navbar { background-color: var(--bg-panel); border-bottom: 1px solid var(--border); }
        .navbar-brand { font-weight: bold; color: var(--accent) !important; }
        .nav-link { color: var(--text-secondary); }
        .nav-link.active { color: #fff !important; font-weight: bold; }
        
        /* Classic Imageboard Layout (Matched to DOM) */
        #threads { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; padding: 10px; }
        .thread { 
            display: inline-block; 
            vertical-align: top; 
            width: 250px; 
            margin-bottom: 20px; 
            font-size: 0.75rem; 
            text-align: center;
            background-color: var(--bg-panel);
            padding: 10px;
            border-radius: 4px;
            border: 1px solid var(--border);
            position: relative;
        }
        .thumb { 
            max-width: 250px; 
            max-height: 250px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.5); 
            margin-bottom: 5px; 
            border-radius: 4px;
        }
        .meta { 
            margin-bottom: 5px; 
            color: var(--text-secondary);
        }
        .meta b { color: var(--text-primary); }
        .teaser { 
            text-align: left; 
            word-wrap: break-word; 
            max-height: 100px; 
            overflow: hidden; 
            color: var(--text-secondary);
            line-height: 1.2;
        }
        .teaser b { color: var(--accent); }

        /* Trashcan positioning */
        .thread .trash-btn {
            position: absolute; top: 5px; right: 5px;
            background: rgba(0,0,0,0.6); border-radius: 4px; z-index: 10;
        }

        /* Thread View Style */
        .thread-container { max-width: 1200px; margin: 0 auto; }
        .post { background-color: var(--post-bg); border: 1px solid var(--border); margin-bottom: 5px; padding: 10px; display: flex; gap: 15px; border-radius: 4px; }
        .reply { background-color: var(--reply-bg); margin-left: 25px; border-left: 3px solid var(--accent); }
        .post-info { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; font-size: 0.85rem; }
        .post-name { color: var(--name-color); font-weight: bold; }
        .post-id { color: var(--text-secondary); text-decoration: none; }
        .post-subject { color: var(--accent); font-weight: bold; }
        
        .post-thumb-container { flex-shrink: 0; }
        .post-thumb-container img { max-width: 150px; max-height: 150px; border: 1px solid var(--border); }

        /* Inputs & Buttons */
        .trash-btn {
            color: var(--text-secondary); opacity: 0.4; transition: all 0.2s;
            cursor: pointer; border: none; background: none; padding: 2px;
        }
        .trash-btn:hover { color: var(--soft-red); opacity: 1; transform: scale(1.2); }
        .fade-out { opacity: 0; transform: scale(0.9); transition: all 0.4s ease; pointer-events: none; }

        .form-control, .form-select { background-color: #1d1f21; border-color: var(--border); color: #fff; }
        .form-control:focus { background-color: #1d1f21; color: #fff; border-color: var(--accent); box-shadow: none; }
        .hero-icon { width: 1.1rem; height: 1.1rem; vertical-align: middle; }
    </style>
</head>
<body>

    <nav class="navbar navbar-expand fixed-top">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">ARCHIVE</a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link {% if view == 'list' %}active{% endif %}" href="/?view=list">Search</a></li>
                    <li class="nav-item"><a class="nav-link {% if view == 'gallery' %}active{% endif %}" href="/?view=gallery">Gallery</a></li>
                    <li class="nav-item"><a class="nav-link {% if view == 'catalog' %}active{% endif %}" href="/?view=catalog">Catalog</a></li>
                </ul>
                <div class="text-muted small px-3">Last Index: {{ last_updated }}</div>
            </div>
        </div>
    </nav>

    <div class="sidebar">
        <form action="/" method="POST" enctype="multipart/form-data">
            <input type="hidden" name="view" value="{{ view }}">
            <div class="mb-3">
                <label class="form-label small fw-bold text-uppercase">Smart Search</label>
                <div class="input-group input-group-sm">
                    <input type="text" name="q" class="form-control" placeholder="Text, URL, or ID..." value="{{ args.get('q', '') }}">
                    <button class="btn btn-outline-secondary" type="button" onclick="document.getElementById('imageUpload').click()" title="Search by Image">
                        <svg class="hero-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                    </button>
                </div>
                <input type="file" id="imageUpload" name="image" style="display: none;" onchange="this.form.submit()">
                
                <div class="form-text small text-muted mt-2">
                    <b>Examples:</b>
                    <ul class="ps-3 mb-0" style="font-size: 0.7rem;">
                        <li>"Jones" (keyword)</li>
                        <li>"17708209669" (fuzzy ID)</li>
                        <li>"4cdn.org/b/123..." (paste URL)</li>
                    </ul>
                </div>
            </div>
            <div class="mb-3">
                <label class="form-label small fw-bold text-uppercase">Board</label>
                <select name="board" class="form-select form-select-sm">
                    <option value="">All Boards</option>
                    {% for b in boards %}
                    <option value="{{ b }}" {% if args.get('board') == b %}selected{% endif %}>/{{ b }}/</option>
                    {% endfor %}
                </select>
            </div>
            <button type="submit" class="btn btn-primary btn-sm w-100">Apply Filters</button>
            <a href="/?view={{ view }}" class="btn btn-outline-secondary btn-sm w-100 mt-2">Reset</a>
        </form>
    </div>

    <div class="main-content">
        {% if view == 'gallery' or view == 'catalog' %}
            <div id="threads" class="extended-large">
                {% for row in posts %}
                    <div id="container-{{ row.thread_id if view == 'catalog' else row.post_no }}" class="thread">
                        <a href="/?view=thread&id={{ row.thread_id }}#{{ row.post_no }}">
                            <img src="/images/{{ row.local_path }}" loading="lazy" class="thumb" alt="">
                        </a>
                        <button class="trash-btn" onclick="curate('{{ row.board }}', '{{ row.thread_id if view == 'catalog' else row.post_no }}', '{{ 'thread' if view == 'catalog' else 'post' }}')">
                            <svg class="hero-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                        </button>
                        
                        <div class="meta">
                            {% if view == 'catalog' %}
                                R: <b>{{ row.replies or 0 }}</b> / I: <b>{{ row.images or 0 }}</b>
                            {% else %}
                                /{{ row.board }}/ No.<b>{{ row.post_no }}</b>
                            {% endif %}
                        </div>
                        
                        <div class="teaser">
                            <b>{{ row.thread_subject or row.subject or 'No Subject' }}</b>:
                            {{ row.comment | safe }}
                        </div>
                    </div>
                {% endfor %}
            </div>

        {% elif view == 'thread' %}
            <div class="thread-container">
                {% for row in posts %}
                    <div class="post {% if loop.index > 1 %}reply{% endif %}" id="container-{{ row.post_no }}">
                        {% if row.local_path %}
                        <div class="post-thumb-container">
                            <a href="/images/{{ row.local_path }}" target="_blank">
                                <img src="/images/{{ row.local_path }}" loading="lazy">
                            </a>
                        </div>
                        {% endif %}
                        <div class="post-content w-100">
                            <div class="post-info">
                                {% if row.subject %}<span class="post-subject">{{ row.subject }}</span>{% endif %}
                                <span class="post-name">Anonymous</span>
                                <span class="post-date text-muted">{{ row.timestamp_str }}</span>
                                <a href="#container-{{ row.post_no }}" class="post-id">No.{{ row.post_no }}</a>
                                <button class="trash-btn ms-auto" onclick="curate('{{ row.board }}', '{{ row.post_no }}', 'post')">
                                    <svg class="hero-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                </button>
                            </div>
                            <div class="post-message">{{ row.comment | safe }}</div>
                        </div>
                    </div>
                {% else %}
                    <div class="text-center text-muted py-5">No posts found in this thread.</div>
                {% endfor %}
            </div>

        {% else %}
            <div class="thread-container">
                {% for row in posts %}
                    <div class="post" id="container-{{ row.post_no }}">
                        {% if row.local_path %}
                        <div class="post-thumb-container"><img src="/images/{{ row.local_path }}" loading="lazy"></div>
                        {% endif %}
                        <div class="post-content w-100">
                            <div class="post-info">
                                <span class="badge bg-secondary">/{{ row.board }}/</span>
                                {% if row.subject %}<span class="post-subject">{{ row.subject }}</span>{% endif %}
                                <span class="post-name">Anonymous</span>
                                <span>{{ row.timestamp_str }}</span>
                                <a href="/?view=thread&id={{ row.thread_id }}#{{ row.post_no }}" class="post-id">No.{{ row.post_no }}</a>
                                <button class="trash-btn ms-auto" onclick="curate('{{ row.board }}', '{{ row.post_no }}', 'post')">
                                    <svg class="hero-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                </button>
                            </div>
                            <div class="post-message">{{ row.comment | safe }}</div>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    </div>

    <script>
        async function curate(board, itemId, itemType) {
            const container = document.getElementById(`container-${itemId}`);
            if (container) container.classList.add('fade-out');
            try {
                const response = await fetch('/api/curate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ board, item_id: itemId, item_type: itemType, action: 'soft_delete' })
                });
                if (!response.ok) throw new Error('Curation failed');
                setTimeout(() => { if(container) container.remove(); }, 400);
            } catch (err) {
                console.error(err);
                if (container) container.classList.remove('fade-out');
            }
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index() -> str:
    view = request.form.get('view') or request.args.get('view', 'list')
    q = request.form.get('q') or request.args.get('q', '').strip()
    
    # Handle Image Upload
    image_file = request.files.get('image')
    if image_file and image_file.filename != '':
        df = archive.find_by_image(image_file.read())
        q = f"[Reverse Image Search: {image_file.filename}]"
    elif q:
        if q.startswith('http') and (q.endswith('.jpg') or q.endswith('.png') or q.endswith('.gif')):
            df = archive.find_by_image_url(q)
        else:
            df = archive.search(q, board=request.form.get('board') or request.args.get('board'))
    else:
        df = archive.load_data()

    if df.empty:
        # Fallback for boards list if df is empty
        all_boards = sorted(archive.load_data()['board'].unique().tolist()) if not archive.load_data().empty else []
        return render_template_string(HTML_TEMPLATE, posts=[], view=view, args={'q': q}, 
                                      boards=all_boards, total_posts=0, last_updated="N/A")
    
    filtered = df.copy()
    
    if view == 'thread':
        tid = request.args.get('id')
        full_df = archive.load_data()
        posts = full_df[full_df['thread_id'].astype(str) == str(tid)].sort_values('timestamp') if tid else pd.DataFrame()
    elif view == 'catalog':
        thread_stats = filtered.groupby('thread_id').agg(
            replies=('post_no', 'count'),
            images=('local_path', lambda x: (x != '').sum())
        ).reset_index()
        posts = filtered.sort_values('timestamp').groupby('thread_id').first().reset_index()
        posts = posts.merge(thread_stats, on='thread_id', how='left')
        posts = posts.sort_values('timestamp', ascending=False).head(100)
    elif view == 'gallery':
        posts = filtered[filtered['local_path'] != ''].sort_values('timestamp', ascending=False).head(200)
    else:
        posts = filtered.sort_values('timestamp', ascending=False).head(100)

    all_boards = sorted(archive.load_data()['board'].unique().tolist())
    return render_template_string(HTML_TEMPLATE, posts=posts.to_dict('records'), view=view, args={'q': q, 'board': request.args.get('board') or request.form.get('board')}, 
                                 boards=all_boards, total_posts=len(archive.load_data()), 
                                 last_updated=datetime.now().strftime('%H:%M'))

@app.route('/api/curate', methods=['POST'])
def curate():
    data = request.json
    try:
        import psycopg2
        conn = psycopg2.connect(**PG_CONFIG)
        cursor = conn.cursor()
        query = "INSERT INTO control.curation (board, item_id, item_type, action) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (data['board'], data['item_id'], data['item_type'], data['action']))
        conn.commit()
        cursor.close()
        conn.close()
        archive.load_data(force=True)
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Postgres curation failed: {e}")
        # Legacy fallback
        try:
            import mysql.connector
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            query = "INSERT INTO imageboard_curation (board, item_id, item_type, action) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (data['board'], data['item_id'], data['item_type'], data['action']))
            conn.commit()
            cursor.close()
            conn.close()
            archive.load_data(force=True)
            return jsonify({"status": "success", "legacy": True})
        except Exception as e2:
            return jsonify({"error": f"Postgres: {str(e)}, MySQL: {str(e2)}"}), 500

@app.route('/health')
def health() -> dict:
    return {"status": "ok", "parquet_found": Path(archive.parquet_path).exists()}

@app.route('/images/<path:filename>')
def serve_image(filename: str):
    return send_from_directory(SHARED_IMAGES_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
