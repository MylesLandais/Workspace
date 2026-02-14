from flask import Flask, render_template_string, send_from_directory, request, jsonify
import pandas as pd
from pathlib import Path
import os
import json

app = Flask(__name__)

BASE_DIR = Path('/home/warby/Workspace/jupyter')
CACHE_DIR = BASE_DIR / 'cache' / 'imageboard'
PARQUET_FILE = BASE_DIR / 'datasets' / 'parquet' / 'imageboard_weekly_latest.parquet'
SHARED_IMAGES_DIR = CACHE_DIR / 'shared_images'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Imageboard Dataset Explorer - Gridstack Dashboard</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/gridstack@7.5.1/dist/gridstack.min.css">
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
        body { background: var(--bg-dark); color: var(--text-main); font-family: 'Inter', sans-serif; margin: 0; height: 100vh; overflow: hidden; }
        
        .sidebar { width: 280px; background: var(--sidebar-bg); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; flex-shrink: 0; }
        .main-content { flex-grow: 1; overflow-y: auto; padding: 20px; }
        
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

        .grid-stack { background: var(--bg-dark); min-height: calc(100vh - 40px); }
        .grid-stack-item-content {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            height: 100%;
            overflow-y: auto;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            transition: box-shadow 0.2s;
        }
        .grid-stack-item-content:hover {
            box-shadow: 0 4px 16px rgba(0,0,0,0.4);
        }
        
        .widget-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border-color);
            cursor: grab;
        }
        .widget-header:active {
            cursor: grabbing;
        }
        .widget-title {
            font-weight: 700;
            color: var(--accent);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .widget-actions {
            display: flex;
            gap: 8px;
        }
        .widget-btn {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-dim);
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.75rem;
            transition: all 0.2s;
        }
        .widget-btn:hover {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }
        
        .stat-card { 
            background: var(--card-bg); 
            border: 1px solid var(--border-color); 
            padding: 12px;
            border-radius: 6px;
            text-align: center;
            margin-bottom: 10px;
        }
        .stat-value { font-size: 1.5rem; font-weight: 700; display: block; }
        .stat-label { font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; }
        
        .catalog-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); 
            gap: 10px; 
        }
        .catalog-item { 
            background: var(--card-bg); 
            border: 1px solid var(--border-color); 
            border-radius: 6px; 
            padding: 10px;
            transition: all 0.2s;
        }
        .catalog-item:hover { border-color: var(--accent); transform: translateY(-2px); }
        
        .catalog-image-preview {
            height: 100px;
            background: #000;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 8px;
            border: 1px solid var(--border-color);
        }
        .catalog-image-preview img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 10px;
        }
        .gallery-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 100%;
            transition: transform 0.2s;
        }
        .gallery-card:hover { transform: scale(1.02); }
        .gallery-card.moderated { border: 2px solid #ff4757; }
        .gallery-card .image-container { height: 100px; background: #000; overflow: hidden; }
        .gallery-card .image-container img { width: 100%; height: 100%; object-fit: cover; }
        .gallery-card .card-body { padding: 6px; background: var(--card-bg); flex-grow: 1; }
        
        .board { font-family: arial,helvetica,sans-serif; font-size: 13px; }
        .thread { margin-bottom: 15px; }
        .post { overflow: hidden; padding: 5px; background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 4px; margin-bottom: 6px; }
        .post.op { background-color: transparent; border: none; }
        .post.reply { background-color: #1d2129; }
        .post.moderated { border: 2px solid #ff4757 !important; }
        
        .postInfo { display: block; padding-bottom: 4px; color: var(--text-dim); font-size: 0.75rem; }
        .subject { color: #cc6666; font-weight: 700; margin-right: 6px; }
        .postNum { font-size: 0.75rem; margin-left: 6px; cursor: pointer; }
        .postNum a { text-decoration: none; color: var(--text-dim); }
        
        .file { display: block; margin-bottom: 5px; }
        .fileText { font-size: 0.7rem; color: var(--text-dim); margin-bottom: 3px; }
        .fileThumb { float: left; margin-right: 8px; }
        .fileThumb img { max-width: 120px; max-height: 120px; border: 1px solid var(--border-color); object-fit: contain; }
        
        .postMessage { margin: 6px 0; line-height: 1.3; font-size: 0.85rem; color: var(--text-main); word-wrap: break-word; white-space: pre-wrap; }
        
        .badge-custom { 
            padding: 2px 6px; 
            border-radius: 3px; 
            font-size: 0.65rem;
            display: inline-block;
            margin: 1px;
        }
        .kw-irl { background: rgba(56, 189, 248, 0.2); color: #38bdf8; }
        .kw-feet { background: rgba(168, 85, 247, 0.2); color: #a855f7; }
        .kw-goon { background: rgba(236, 72, 153, 0.2); color: #ec4899; }
        .kw-cel { background: rgba(234, 179, 8, 0.2); color: #eab308; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h5 class="mb-0" style="color: var(--accent); font-weight: 800; letter-spacing: -0.5px;">INTEL_HUB</h5>
            <small class="text-dim">Gridstack v4.0</small>
        </div>
        <div class="sidebar-menu">
            <div class="mb-4">
                <small class="text-dim text-uppercase" style="font-size: 0.6rem; letter-spacing: 1px;">View Modes</small>
                <a href="/?view=catalog" class="menu-item {% if view == 'catalog' %}active{% endif %}">
                    🔍 Catalog Explorer
                </a>
                <a href="/?view=list" class="menu-item {% if view == 'list' %}active{% endif %}">
                    📡 Live Post Feed
                </a>
                <a href="/?view=stack" class="menu-item {% if view == 'stack' %}active{% endif %}">
                    🧵 Thread Clusters
                </a>
            </div>
            
            <div class="mb-4">
                <small class="text-dim text-uppercase" style="font-size: 0.6rem; letter-spacing: 1px;">Layout Controls</small>
                <button class="widget-btn w-100 mt-2" id="saveLayoutBtn">💾 Save Layout</button>
                <button class="widget-btn w-100 mt-1" id="resetLayoutBtn">🔄 Reset Layout</button>
            </div>
            
            <div class="mb-4">
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
            
            <div class="mb-4">
                <small class="text-dim text-uppercase" style="font-size: 0.6rem; letter-spacing: 1px;">Board Filter</small>
                <form action="/" method="GET" class="mt-2">
                    <input type="hidden" name="view" value="catalog">
                    <input type="text" name="board" class="widget-btn w-100" style="text-align: left;" placeholder="e.g. b, pol, v" value="{{ board_filter }}">
                    <button type="submit" class="widget-btn w-100 mt-1">Apply</button>
                </form>
            </div>
        </div>
        <div class="p-3 border-top border-dark">
            <div class="d-flex justify-content-between align-items-center">
                <span class="text-dim" style="font-size: 0.65rem;">DB_SYNC: OK</span>
                <span class="badge bg-success" style="font-size: 0.5rem;">ONLINE</span>
            </div>
        </div>
    </div>

    <div class="main-content">
        <div class="grid-stack" id="dashboardGrid"></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/gridstack@7.5.1/dist/gridstack-all.js"></script>
    <script>
        // Default widget layout configuration
        const defaultLayout = [
            { id: 'stats', x: 0, y: 0, w: 3, h: 4, title: '📊 Overview Stats' },
            { id: 'catalog', x: 3, y: 0, w: 5, h: 8, title: '🔍 Catalog Explorer' },
            { id: 'feed', x: 8, y: 0, w: 4, h: 8, title: '📡 Live Feed' },
            { id: 'threads', x: 0, y: 4, w: 8, h: 10, title: '🧵 Thread Clusters' }
        ];

        let grid = null;

        // Widget content renderers (business components)
        const widgetContent = {
            stats: function() {
                return `
                    <div class="stat-card">
                        <span class="stat-value" style="color: var(--accent)">{{ total_posts }}</span>
                        <span class="stat-label">Total Ingested</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value" style="color: #ff4757">{{ moderated_posts }}</span>
                        <span class="stat-label">Flagged Intel</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value" style="color: #10b981">{{ total_images }}</span>
                        <span class="stat-label">Visual Assets</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value" style="color: #3b82f6">{{ total_threads }}</span>
                        <span class="stat-label">Active Vectors</span>
                    </div>
                `;
            },
            catalog: function() {
                return `
                    <div class="catalog-grid">
                        ${catalogItemsData.slice(0, 12).map(item => `
                            <div class="catalog-item">
                                ${item.preview_image ? `
                                    <div class="catalog-image-preview">
                                        <a href="/?view=stack&thread=${item.thread_id}">
                                            <img src="/images/${item.preview_image}" loading="lazy" alt="Preview">
                                        </a>
                                    </div>
                                ` : ''}
                                <div class="mb-2">
                                    <small style="color: var(--accent); font-weight: 600;">/${item.thread_id}</small>
                                    <small class="text-dim ms-2">${item.image_count} img</small>
                                </div>
                                ${item.tags.slice(0, 3).map(tag => 
                                    `<span class="badge-custom kw-${tag.name}">${tag.name}</span>`
                                ).join('')}
                            </div>
                        `).join('')}
                    </div>
                    ${catalogItemsData.length > 12 ? `
                        <div class="text-center mt-3">
                            <button class="widget-btn" onclick="window.location.href='/?view=catalog'">Load More</button>
                        </div>
                    ` : ''}
                `;
            },
            feed: function() {
                return `
                    <div class="gallery-grid">
                        ${postsData.slice(0, 20).map(post => `
                            <div class="gallery-card ${post.moderated ? 'moderated' : ''}">
                                ${post.local_path ? `
                                    <div class="image-container">
                                        <img src="/images/${post.local_path}" alt="post" loading="lazy">
                                    </div>
                                ` : ''}
                                <div class="card-body">
                                    <small style="color: var(--accent);">#${post.post_no}</small>
                                    ${post.subject ? `<div style="font-size: 0.7rem; margin-top: 3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${post.subject}</div>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            },
            threads: function() {
                const threads = {};
                postsData.forEach(post => {
                    if (!threads[post.thread_id]) {
                        threads[post.thread_id] = [];
                    }
                    threads[post.thread_id].push(post);
                });

                return `
                    <div class="board">
                        ${Object.entries(threads).slice(0, 10).map(([threadId, posts]) => `
                            <div class="thread">
                                ${posts.slice(0, 1).map(post => `
                                    <div class="post op">
                                        ${post.local_path ? `
                                            <div class="file">
                                                <a class="fileThumb" href="/images/${post.local_path}" target="_blank">
                                                    <img src="/images/${post.local_path}" alt="" loading="lazy">
                                                </a>
                                            </div>
                                        ` : ''}
                                        <div class="postInfo">
                                            ${post.subject ? `<span class="subject">${post.subject}</span>` : ''}
                                            <span class="postNum">#${post.post_no}</span>
                                            <span class="text-dim">${posts.length} replies</span>
                                        </div>
                                        <div class="postMessage" style="max-height: 70px; overflow: hidden;">${post.comment ? post.comment.substring(0, 200) : ''}...</div>
                                    </div>
                                `).join('')}
                            </div>
                        `).join('')}
                    </div>
                `;
            }
        };

        // Initialize grid and widgets
        function initGrid() {
            grid = GridStack.init({
                column: 12,
                cellHeight: 100,
                margin: 10,
                animate: true,
                float: false,
                disableOneColumnMode: false
            });

            // Load saved or default layout
            loadLayout();

            // Listen for layout changes and auto-save
            grid.on('change', function(event, items) {
                if (!items) return;
                const layout = items.map(item => ({
                    id: item.id,
                    x: item.x,
                    y: item.y,
                    w: item.w,
                    h: item.h
                }));
                localStorage.setItem('dashboardLayout', JSON.stringify(layout));
            });

            // Setup button handlers
            document.getElementById('saveLayoutBtn').addEventListener('click', function() {
                const layout = grid.save();
                localStorage.setItem('dashboardLayout', JSON.stringify(layout));
                alert('Layout saved!');
            });

            document.getElementById('resetLayoutBtn').addEventListener('click', function() {
                if (confirm('Reset to default layout?')) {
                    localStorage.removeItem('dashboardLayout');
                    location.reload();
                }
            });
        }

        function loadLayout() {
            const saved = localStorage.getItem('dashboardLayout');
            let layout = saved ? JSON.parse(saved) : defaultLayout;

            // Create widgets from layout data
            layout.forEach(widgetConfig => {
                createWidget(widgetConfig);
            });
        }

        function createWidget(config) {
            const widgetEl = document.createElement('div');
            widgetEl.className = 'grid-stack-item';
            widgetEl.setAttribute('gs-id', config.id);
            
            // If position is not specified, let Gridstack auto-position
            if (config.x !== undefined && config.y !== undefined) {
                widgetEl.setAttribute('gs-x', config.x);
                widgetEl.setAttribute('gs-y', config.y);
            } else {
                widgetEl.setAttribute('gs-auto-position', 'true');
            }
            
            widgetEl.setAttribute('gs-w', config.w);
            widgetEl.setAttribute('gs-h', config.h);
            
            // Render widget header and content
            widgetEl.innerHTML = `
                <div class="grid-stack-item-content">
                    <div class="widget-header">
                        <span class="widget-title">${config.title}</span>
                        <div class="widget-actions">
                            <button class="widget-btn" onclick="refreshWidget('${config.id}')">🔄</button>
                        </div>
                    </div>
                    <div id="widget-content-${config.id}"></div>
                </div>
            `;
            
            // Add widget to grid
            grid.addWidget(widgetEl);
            
            // Render widget content
            const contentEl = document.getElementById(`widget-content-${config.id}`);
            if (contentEl && widgetContent[config.id]) {
                contentEl.innerHTML = widgetContent[config.id]();
            }
        }

        function refreshWidget(id) {
            const contentEl = document.getElementById(`widget-content-${id}`);
            if (contentEl && widgetContent[id]) {
                contentEl.innerHTML = widgetContent[id]();
            }
        }

        // Data injected from Flask
        const catalogItemsData = {{ catalog_items | tojson | safe }};
        const postsData = {{ posts_json | safe }};
        
        // Initialize on DOM ready
        document.addEventListener('DOMContentLoaded', function() {
            initGrid();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    if not PARQUET_FILE.exists():
        return "Dataset not found. Please run pipeline first.", 404
    
    df = pd.read_parquet(PARQUET_FILE)
    
    total_posts = len(df)
    moderated_posts = len(df[df['moderated'] == True])
    total_images = len(df[df['local_path'] != ''])
    total_threads = df['thread_id'].nunique()
    
    app.jinja_env.filters['len'] = lambda obj: len(obj) if hasattr(obj, '__len__') else 0
    app.jinja_env.filters['tojson'] = lambda obj: json.dumps(obj, default=str)
    
    TAG_CONFIG = {
        'irl': 'kw-irl',
        'zoomer': 'kw-zoomer',
        'feet': 'kw-feet',
        'goon': 'kw-goon',
        'cel': 'kw-cel',
        'panties': 'kw-panties'
    }

    tag_counts = {}
    for kw in TAG_CONFIG.keys():
        count = len(df[df['comment'].str.lower().str.contains(kw, na=False) | 
                       df['subject'].str.lower().str.contains(kw, na=False)])
        if count > 0:
            tag_counts[kw] = count

    view_mode = request.args.get('view', 'catalog')
    board_filter = request.args.get('board', '').upper()
    query = request.args.get('q', '')
    thread_id = request.args.get('thread', None)
    
    # Build catalog items once for all views
    threads_dict = {}
    for _, row in df.iterrows():
        tid = str(row['thread_id'])
        if tid not in threads_dict:
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
        if row['moderated'] is True or (hasattr(row['moderated'], '__bool__') and bool(row['moderated']) == True):
            threads_dict[tid]['moderated_count'] += 1
    
    catalog_items = list(threads_dict.values())
    
    if board_filter:
        catalog_items = [t for t in catalog_items if t['board'].upper() == board_filter]
    
    catalog_items.sort(key=lambda x: x['image_count'], reverse=True)
    
    # Filtering for posts view
    posts_df = df.copy()
    if query:
        posts_df = posts_df[posts_df['comment'].str.lower().str.contains(query.lower(), na=False) |
                           posts_df['subject'].str.lower().str.contains(query.lower(), na=False)]
    
    if thread_id:
        posts_df = posts_df[posts_df['thread_id'] == str(thread_id)]
        posts_df = posts_df.sort_values(by='timestamp', ascending=True)
    else:
        posts_df = posts_df.sort_values(by='timestamp', ascending=False)
        posts_df = posts_df.head(100)
    
    # Prepare posts data for client-side rendering
    posts_json = json.dumps(posts_df.to_dict(orient='records'), default=str)
    
    return render_template_string(
        HTML_TEMPLATE,
        catalog_items=catalog_items,
        posts=posts_df,
        posts_json=posts_json,
        total_posts=total_posts,
        moderated_posts=moderated_posts,
        total_images=total_images,
        total_threads=total_threads,
        view=view_mode,
        board_filter=board_filter,
        tag_counts=tag_counts
    )

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(SHARED_IMAGES_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
