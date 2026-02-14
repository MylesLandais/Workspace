from flask import Flask, render_template_string, send_from_directory, request
import pandas as pd
from pathlib import Path
import os

app = Flask(__name__)

# Paths
BASE_DIR = Path('/home/warby/Workspace/jupyter')
CACHE_DIR = BASE_DIR / 'cache' / 'imageboard'
PARQUET_FILE = BASE_DIR / 'datasets' / 'parquet' / 'imageboard_weekly_latest.parquet'
SHARED_IMAGES_DIR = CACHE_DIR / 'shared_images'

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Imageboard Dataset Explorer</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        :root {
            --bg-dark: #0b0d14;
            --card-bg: #151921;
            --sidebar-bg: #0e1117;
            --border-color: #242933;
            --text-main: #e6eef5;
            --text-dim: #8b95a1;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.2);
        }
        body { background: var(--bg-dark); color: var(--text-main); font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        /* Layout */
        .sidebar { width: 280px; background: var(--sidebar-bg); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; flex-shrink: 0; }
        .main-content { flex-grow: 1; overflow-y: auto; padding: 30px; }
        
        .sidebar-header { padding: 25px; border-bottom: 1px solid var(--border-color); }
        .sidebar-menu { padding: 15px; flex-grow: 1; }
        .menu-item { 
            display: flex; 
            align-items: center; 
            padding: 12px 15px; 
            color: var(--text-dim); 
            text-decoration: none; 
            border-radius: 6px; 
            margin-bottom: 5px;
            transition: all 0.2s;
        }
        .menu-item:hover, .menu-item.active { background: var(--card-bg); color: var(--accent); }
        .menu-item i { margin-right: 12px; }
        
        /* New Sidebar Elements */
        .tag-filter-list { padding: 0 10px; margin-top: 15px; }
        .tag-filter-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 12px;
            font-size: 0.75rem;
            color: var(--text-dim);
            cursor: pointer;
            border-radius: 4px;
            text-decoration: none;
        }
        .tag-filter-item:hover { background: rgba(56, 189, 248, 0.1); color: var(--accent); }
        .tag-count { background: var(--border-color); padding: 1px 6px; border-radius: 10px; font-size: 0.65rem; }

        /* Components */
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }
        .stat-card { background: var(--card-bg); border: 1px solid var(--border-color); padding: 15px; border-radius: 8px; }
        .stat-value { font-size: 1.5rem; font-weight: 700; color: var(--accent); display: block; }
        .stat-label { font-size: 0.75rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; }

        .catalog-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }
        .catalog-item { 
            background: var(--card-bg); 
            border: 1px solid var(--border-color); 
            border-radius: 12px; 
            padding: 20px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .catalog-item:hover { border-color: var(--accent); transform: translateY(-4px); box-shadow: 0 10px 30px rgba(0,0,0,0.5); }

        /* Gallery/Stack View Styles */
        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 20px;
        }
        .gallery-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 100%;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .gallery-card:hover {
            transform: scale(1.03);
            box-shadow: 0 12px 30px rgba(0,0,0,0.6);
            z-index: 10;
        }
        .gallery-card.moderated {
            border: 2px solid #ff4757;
        }
        .gallery-card .image-container, .post-card .image-container {
            height: 200px;
            background: #000;
            position: relative;
            overflow: hidden;
        }
        .gallery-card .image-container img, .post-card .image-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .gallery-card .card-body {
            padding: 12px;
            background: var(--card-bg);
            flex-grow: 1;
        }
        .post-number {
            font-family: monospace;
            color: var(--accent);
            font-size: 0.75rem;
            margin-bottom: 5px;
            display: block;
        }
        .thread-header-strip {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
        }
        
        /* Classic Thread View Styles */
        .board { margin: 0 auto; max-width: 100%; padding: 10px; font-family: arial,helvetica,sans-serif; font-size: 14px; }
        .thread { margin-bottom: 40px; }
        .postContainer { display: block; margin-bottom: 8px; }
        .opContainer { display: block; margin-bottom: 20px; }
        .replyContainer { display: table; padding: 2px; }
        .sideArrows { color: #707070; float: left; margin-right: 5px; margin-top: 5px; margin-left: 2px; user-select: none; }
        
        .post { overflow: hidden; padding: 8px; background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 4px; color: var(--text-main); }
        .post.op { background-color: transparent; border: none; padding: 0; }
        .post.reply { background-color: #1d2129; border-color: var(--border-color); display: table; min-width: 400px; max-width: 100%; box-shadow: 0 1px 2px rgba(0,0,0,0.2); }
        .post.moderated { border: 2px solid #ff4757 !important; }
        
        .postInfo { display: block; padding-bottom: 5px; color: var(--text-dim); font-size: 0.85rem; }
        .nameBlock { display: inline-block; font-weight: 700; color: #117743; }
        .nameBlock.anon { color: var(--text-main); }
        .subject { color: #cc6666; font-weight: 700; margin-right: 10px; }
        
        .postNum { font-size: 0.85rem; margin-left: 8px; cursor: pointer; }
        .postNum a { text-decoration: none; color: var(--text-dim); }
        .postNum a:hover { color: var(--accent); }
        
        .file { display: block; margin-bottom: 8px; margin-top: 5px; }
        .fileText { font-size: 0.75rem; color: var(--text-dim); margin-bottom: 5px; margin-left: 2px; }
        .fileThumb { float: left; margin-right: 20px; margin-bottom: 10px; }
        .fileThumb img { max-width: 250px; max-height: 250px; border: 1px solid var(--border-color); object-fit: contain; }
        .fileThumb:hover img { border-color: var(--accent); }
        
        .postMessage { margin: 10px 0; line-height: 1.4; font-size: 1rem; color: var(--text-main); word-wrap: break-word; white-space: pre-wrap; }
        .postMessage .quotelink { color: var(--accent); text-decoration: none; font-weight: bold; }
        .postMessage .quotelink:hover { text-decoration: underline; }
        .postMessage .quote { color: #789922; }
        
        /* List View / Search Styles */
        .search-bar-container {
            background: var(--card-bg);
            padding: 20px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            margin-bottom: 20px;
        }
        .form-control, .form-select {
            background: #0f111a;
            border: 1px solid var(--border-color);
            color: white;
        }
        .form-control:focus, .form-select:focus {
            background: #161925;
            color: white;
            border-color: var(--accent);
            box-shadow: 0 0 0 0.25rem rgba(0, 120, 212, 0.25);
        }
        .post-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-main);
        }
        .post-card.moderated {
            border-color: #ff4757;
        }
        .post-card .card-body {
            padding: 15px;
        }
        .catalog-image-preview {
            height: 180px;
            background: #000;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 15px;
            border: 1px solid var(--border-color);
        }
        .catalog-image-preview img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }
        .catalog-image-preview:hover img {
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h5 class="mb-0" style="color: var(--accent); font-weight: 800; letter-spacing: -0.5px;">INTEL_HUB</h5>
            <small class="text-dim">v2.1.0-stable</small>
        </div>
        <div class="sidebar-menu">
            <a href="/?view=catalog" class="menu-item {% if view == 'catalog' %}active{% endif %}">
                Catalog Explorer
            </a>
            <a href="/?view=list" class="menu-item {% if view == 'list' %}active{% endif %}">
                Live Post Feed
            </a>
            <a href="/?view=stack" class="menu-item {% if view == 'stack' %}active{% endif %}">
                Thread Clusters
            </a>
            
            <div class="mt-4 px-3">
                <small class="text-dim text-uppercase" style="font-size: 0.6rem; letter-spacing: 1px;">Board Filter</small>
                <form action="/" method="GET" class="mt-2">
                    <input type="hidden" name="view" value="{{ view }}">
                    <input type="text" name="board" class="form-control form-control-sm mb-2" placeholder="e.g. b, pol, v" value="{{ board_filter }}">
                    <button type="submit" class="btn btn-sm btn-primary w-100" style="font-size: 0.7rem;">Apply</button>
                </form>
            </div>

            <div class="mt-4 px-3">
                <small class="text-dim text-uppercase" style="font-size: 0.6rem; letter-spacing: 1px;">Intelligence Tags</small>
                <div class="tag-filter-list">
                    {% for tag, count in tag_counts.items() %}
                    <a href="/?view=list&q={{ tag }}" class="tag-filter-item">
                        <span>#{{ tag }}</span>
                        <span class="tag-count">{{ count }}</span>
                    </a>
                    {% endfor %}
                </div>
            </div>
        </div>
        <div class="p-3 border-top border-dark">
            <div class="d-flex justify-content-between align-items-center">
                <span class="text-dim" style="font-size: 0.7rem;">DB_SYNC: OK</span>
                <span class="badge bg-success" style="font-size: 0.5rem;">ONLINE</span>
            </div>
        </div>
    </div>

    <div class="main-content">
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-value">{{ total_posts }}</span>
                <span class="stat-label">Total Ingested</span>
            </div>
            <div class="stat-card">
                <span class="stat-value text-danger">{{ moderated_posts }}</span>
                <span class="stat-label">Flagged Intel</span>
            </div>
            <div class="stat-card">
                <span class="stat-value text-success">{{ total_images }}</span>
                <span class="stat-label">Visual Assets</span>
            </div>
            <div class="stat-card">
                <span class="stat-value text-info">{{ total_threads }}</span>
                <span class="stat-label">Active Vectors</span>
            </div>
        </div>

        {% if view == 'catalog' %}
        <div class="catalog-grid">
            {% for item in catalog_items %}
                <div class="catalog-item">
                    {% if item.preview_image %}
                    <div class="catalog-image-preview">
                        <a href="/?view=stack&thread={{ item.thread_id }}">
                            <img src="/images/{{ item.preview_image }}" loading="lazy" alt="Preview">
                        </a>
                    </div>
                    {% endif %}
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <div>
                            <span class="board-badge mb-2 d-inline-block">{{ item.board }}</span>
                            <h5 class="mb-0">/{{ item.thread_id }}</h5>
                        </div>
                        <a href="/?view=stack&thread={{ item.thread_id }}" class="btn btn-sm btn-outline-primary">Analyze Vector</a>
                    </div>
                    
                    <div class="mb-3">
                        {% for tag in item.tags %}
                            <span class="kw-badge {{ tag.class }}">{{ tag.name }}</span>
                        {% endfor %}
                    </div>
                    
                    <p class="text-dim mb-4" style="font-size: 0.9rem; line-height: 1.4; height: 40px; overflow: hidden;">
                        {{ item.subject or 'Target vector has no primary subject header.' }}
                    </p>

                    <div class="d-flex justify-content-between align-items-center pt-3 border-top border-dark">
                        <div class="d-flex gap-3">
                            <small class="text-dim">IMAGES: <span class="text-white">{{ item.image_count }}</span></small>
                            <small class="text-dim">FLAGGED: <span class="text-danger">{{ item.moderated_count }}</span></small>
                        </div>
                        <span class="badge {% if item.moderated_count > 0 %}bg-danger{% else %}bg-success{% endif %}" style="font-size: 0.6rem;">
                            {% if item.moderated_count > 0 %}RISK_DETECTED{% else %}SECURE{% endif %}
                        </span>
                    </div>
                </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if view == 'list' %}
        <div class="search-bar-container">
            <form action="/" method="GET" class="row g-3">
                <input type="hidden" name="view" value="list">
                <div class="col-md-6">
                    <input type="text" name="q" class="form-control" placeholder="Search comments..." value="{{ query }}">
                </div>
                <div class="col-md-3">
                    <select name="filter" class="form-select">
                        <option value="all" {% if filter == 'all' %}selected{% endif %}>All Posts</option>
                        <option value="clean" {% if filter == 'clean' %}selected{% endif %}>Clean Only</option>
                        <option value="moderated" {% if filter == 'moderated' %}selected{% endif %}>Moderated Only</option>
                    </select>
                </div>
                <div class="col-md-3 d-flex gap-2">
                    <button type="submit" class="btn btn-primary w-100">Apply Filters</button>
                    <a href="/?view=list" class="btn btn-outline-secondary">Reset</a>
                </div>
            </form>
        </div>

        <div class="row">
            {% for _, post in posts.iterrows() %}
            <div class="col-md-3 mb-4">
                <div class="card post-card h-100 shadow-sm {% if post.moderated %}moderated{% endif %}">
                    {% if post.local_path %}
                    <div class="image-container">
                        <img src="/images/{{ post.local_path }}" alt="post image" loading="lazy">
                    </div>
                    {% endif %}
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <span class="badge bg-dark border border-secondary">{{ post.board }}/{{ post.thread_id }}</span>
                            <small class="text-dim">#{{ post.post_no }}</small>
                        </div>
                        <h6 class="card-title text-truncate" style="color: var(--accent);">{{ post.subject or 'No Subject' }}</h6>
                        <div class="post-text mb-3">
                            {{ post.comment | safe }}
                        </div>
                        {% if post.moderated %}
                        <div class="mt-auto">
                            <span class="badge bg-danger w-100">{{ post.moderation_reason }}</span>
                        </div>
                        {% endif %}
                    </div>
                    <div class="card-footer bg-transparent border-top-0 pt-0">
                        <small class="text-dim" style="font-size: 0.7rem;">{{ post.datetime_iso[:16].replace('T', ' ') }}</small>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if view == 'stack' %}
        {% if thread_id %}
            <div class="mb-3">
                <a href="/" class="btn btn-outline-secondary">← Back to Catalog</a>
            </div>
        {% endif %}

        <div class="board">
        {% for thread_id, thread_group in posts.groupby('thread_id') %}
            <div class="thread" id="t{{ thread_id }}">
                {% for post in thread_group.itertuples() %}
                    {% if loop.index == 1 %}
                    <!-- OP Post -->
                    <div class="postContainer opContainer" id="pc{{ post.post_no }}">
                        <div id="p{{ post.post_no }}" class="post op {% if post.moderated %}moderated{% endif %}">
                            
                            {% if post.local_path %}
                            <div class="file" id="f{{ post.post_no }}">
                                <div class="fileText">File: <a href="/images/{{ post.local_path }}" target="_blank">{{ post.local_path.split('/')[-1] }}</a></div>
                                <a class="fileThumb" href="/images/{{ post.local_path }}" target="_blank">
                                    <img src="/images/{{ post.local_path }}" alt="" loading="lazy">
                                </a>
                            </div>
                            {% endif %}
                            
                            <div class="postInfo desktop" id="pi{{ post.post_no }}">
                                {% if post.subject %}<span class="subject">{{ post.subject }}</span>{% endif %}
                                <span class="nameBlock anon"><span class="name">Anonymous</span></span>
                                <span class="dateTime">{{ post.datetime_iso[:16].replace('T', ' ') }}</span>
                                <span class="postNum desktop">
                                    <a href="#p{{ post.post_no }}" title="Link to this post">No.</a><a href="javascript:void(0);">{{ post.post_no }}</a>
                                </span>
                                {% if post.moderated %}
                                <span class="badge bg-danger ms-2">{{ post.moderation_reason }}</span>
                                {% endif %}
                            </div>
                            
                            <blockquote class="postMessage" id="m{{ post.post_no }}">{{ post.comment | safe }}</blockquote>
                        </div>
                    </div>
                    
                    {% else %}
                    <!-- Reply Post -->
                    <div class="postContainer replyContainer" id="pc{{ post.post_no }}">
                        <div class="sideArrows">&gt;&gt;</div>
                        <div id="p{{ post.post_no }}" class="post reply {% if post.moderated %}moderated{% endif %}">
                            <div class="postInfo desktop" id="pi{{ post.post_no }}">
                                <span class="nameBlock anon"><span class="name">Anonymous</span></span>
                                <span class="dateTime">{{ post.datetime_iso[:16].replace('T', ' ') }}</span>
                                <span class="postNum desktop">
                                    <a href="#p{{ post.post_no }}" title="Link to this post">No.</a><a href="javascript:void(0);">{{ post.post_no }}</a>
                                </span>
                                {% if post.moderated %}
                                <span class="badge bg-danger ms-2">{{ post.moderation_reason }}</span>
                                {% endif %}
                            </div>
                            
                            {% if post.local_path %}
                            <div class="file" id="f{{ post.post_no }}">
                                <div class="fileText">File: <a href="/images/{{ post.local_path }}" target="_blank">{{ post.local_path.split('/')[-1] }}</a></div>
                                <a class="fileThumb" href="/images/{{ post.local_path }}" target="_blank">
                                    <img src="/images/{{ post.local_path }}" alt="" loading="lazy">
                                </a>
                            </div>
                            {% endif %}
                            
                            <blockquote class="postMessage" id="m{{ post.post_no }}">{{ post.comment | safe }}</blockquote>
                        </div>
                    </div>
                    {% endif %}
                {% endfor %}
            </div>
            <hr class="border-secondary my-5">
        {% endfor %}
        </div>
        {% endif %}
        
        {% if posts is defined and posts|length == 0 and view != 'catalog' %}
        <div class="text-center py-5">
            <h3>No results found</h3>
            <p>Try adjusting your search or filters</p>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    if not PARQUET_FILE.exists():
        return "Dataset not found. Please run the pipeline first.", 404
    
    df = pd.read_parquet(PARQUET_FILE)
    
    total_posts = len(df)
    moderated_posts = len(df[df['moderated'] == True])
    total_images = len(df[df['local_path'] != ''])
    total_threads = df['thread_id'].nunique()
    
    # Register custom Jinja2 filter
    app.jinja_env.filters['len'] = lambda obj: len(obj) if hasattr(obj, '__len__') else 0
    
    # Tag Configuration
    TAG_CONFIG = {
        'irl': 'kw-irl',
        'zoomer': 'kw-zoomer',
        'feet': 'kw-feet',
        'goon': 'kw-goon',
        'cel': 'kw-cel',
        'panties': 'kw-panties'
    }

    # Calculate tag counts for sidebar
    tag_counts = {}
    for kw in TAG_CONFIG.keys():
        count = len(df[df['comment'].str.lower().str.contains(kw, na=False) | 
                       df['subject'].str.lower().str.contains(kw, na=False)])
        if count > 0:
            tag_counts[kw] = count

    view_mode = request.args.get('view', 'catalog')

    if view_mode == 'catalog':
        board_filter = request.args.get('board', '').upper()
        
        # Build catalog manually to avoid aggregation issues
        threads_dict = {}
        for _, row in df.iterrows():
            tid = str(row['thread_id'])
            if tid not in threads_dict:
                # Detect tags for this thread
                subj = str(row['subject']).lower() if pd.notna(row['subject']) else ""
                comm = str(row['comment']).lower() if pd.notna(row['comment']) else ""
                combined = subj + " " + comm
                
                found_tags = []
                for kw, cls in TAG_CONFIG.items():
                    if kw in combined:
                        found_tags.append({'name': kw, 'class': cls})

                threads_dict[tid] = {
                    'board': str(row['board']),
                    'thread_id': tid,
                    'subject': str(row['subject']) if pd.notna(row['subject']) else 'No Subject',
                    'image_count': 0,
                    'moderated_count': 0,
                    'tags': found_tags,
                    'preview_image': None
                }
            local_path = str(row['local_path']) if pd.notna(row['local_path']) else ''
            if local_path and local_path != '' and local_path != 'nan':
                threads_dict[tid]['image_count'] += 1
                if threads_dict[tid]['preview_image'] is None:
                    threads_dict[tid]['preview_image'] = local_path
            # Check if moderated is True (handles numpy bools)
            if row['moderated'] is True or (hasattr(row['moderated'], '__bool__') and bool(row['moderated']) == True):
                threads_dict[tid]['moderated_count'] += 1
        
        catalog_items = list(threads_dict.values())
        
        if board_filter:
            catalog_items = [t for t in catalog_items if t['board'].upper() == board_filter]
        
        # Sort by image count (most active threads first)
        catalog_items.sort(key=lambda x: x['image_count'], reverse=True)
        
        return render_template_string(
            HTML_TEMPLATE,
            catalog_items=catalog_items,
            total_posts=total_posts,
            moderated_posts=moderated_posts,
            total_images=total_images,
            total_threads=total_threads,
            view=view_mode,
            board_filter=board_filter,
            tag_counts=tag_counts
        )
    
    elif view_mode == 'stack':
        thread_id = request.args.get('thread', None)
        # Sort by Thread ID (desc) then Timestamp (ASCENDING for thread view)
        df = df.sort_values(by=['thread_id', 'timestamp'], ascending=[False, True])
        
        if thread_id:
            df = df[df['thread_id'] == str(thread_id)]
        
        display_df = df
        return render_template_string(
            HTML_TEMPLATE,
            posts=display_df,
            total_posts=total_posts,
            moderated_posts=moderated_posts,
            total_images=total_images,
            total_threads=total_threads,
            view=view_mode,
            query='',
            filter='all',
            thread_id=thread_id,
            tag_counts=tag_counts,
            board_filter=''
        )
    
    else:
        query = request.args.get('q', '')
        filter_type = request.args.get('filter', 'all')
        
        if query:
            df = df[df['comment'].str.lower().str.contains(query, na=False) | 
                    df['subject'].str.lower().str.contains(query, na=False)]
                    
        if filter_type == 'clean':
            df = df[df['moderated'] == False]
        elif filter_type == 'moderated':
            df = df[df['moderated'] == True]
            
        df = df.sort_values(by='timestamp', ascending=False)
        display_df = df.head(100)
        
        return render_template_string(
            HTML_TEMPLATE,
            posts=display_df,
            total_posts=total_posts,
            moderated_posts=moderated_posts,
            total_images=total_images,
            total_threads=total_threads,
            view=view_mode,
            query=query,
            filter=filter_type,
            tag_counts=tag_counts,
            board_filter=''
        )

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(SHARED_IMAGES_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
