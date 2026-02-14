#!/usr/bin/env python3
"""
API Server - Status and control interface
"""

import os
import json
import redis
from flask import Flask, jsonify, request

app = Flask(__name__)

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
DOWNLOADS_DIR = os.environ.get('DOWNLOADS_DIR', '/home/warby/Workspace/jupyter/downloads')

r = redis.from_url(REDIS_URL)


@app.route('/api/status')
def status():
    """Get crawler status"""
    return jsonify({
        'queue_length': r.llen('queue:jobs'),
        'jobs_completed': int(r.get('stats:jobs_completed') or 0),
        'redis_connected': True
    })


@app.route('/api/stats')
def stats():
    """Get download statistics"""
    posts_dir = os.path.join(DOWNLOADS_DIR, 'metadata')

    stats = {
        'creators': {},
        'total_posts': 0,
        'total_videos': 0,
        'total_images': 0,
        'total_size': 0
    }

    if os.path.exists(posts_dir):
        for creator in os.listdir(posts_dir):
            creator_path = os.path.join(posts_dir, creator)
            if os.path.isdir(creator_path):
                posts = []
                videos = 0
                images = 0

                for f in os.listdir(creator_path):
                    if f.endswith('.json'):
                        try:
                            with open(os.path.join(creator_path, f), 'r') as file:
                                data = json.load(file)
                                posts.append(data)
                                videos += data.get('video_count', 0)
                                images += data.get('image_count', 0)
                        except:
                            pass

                stats['creators'][creator] = {
                    'posts': len(posts),
                    'videos': videos,
                    'images': images
                }
                stats['total_posts'] += len(posts)
                stats['total_videos'] += videos
                stats['total_images'] += images

    return jsonify(stats)


@app.route('/api/queue', methods=['GET', 'POST'])
def queue():
    """Get or add to queue"""
    if request.method == 'POST':
        data = request.json
        job_id = f"manual:{int(__import__('time').time())}"

        job_data = {
            'id': job_id,
            'type': data.get('type', 'post'),
            'creator': data['creator'],
            'post_id': data.get('post_id'),
            'priority': data.get('priority', 'normal'),
            'created_at': __import__('time').strftime('%Y-%m-%dT%H:%M:%SZ', __import__('time').gmtime())
        }

        for key, value in job_data.items():
            r.hset(f"job:{job_id}", key, value)

        r.rpush('queue:jobs', json.dumps({'id': job_id}))

        return jsonify({'status': 'queued', 'job_id': job_id})

    # GET - list queued jobs
    jobs = []
    for i in range(min(50, r.llen('queue:jobs'))):
        job_data = r.lindex('queue:jobs', i)
        if job_data:
            try:
                jobs.append(json.loads(job_data))
            except:
                pass

    return jsonify({'jobs': jobs, 'total': r.llen('queue:jobs')})


@app.route('/api/cache')
def cache():
    """Get cache status"""
    cache_dir = '/home/warby/Workspace/jupyter/cache'

    stats = {
        'size_mb': 0,
        'files': 0,
        'creators': []
    }

    if os.path.exists(cache_dir):
        for creator in os.listdir(cache_dir):
            creator_path = os.path.join(cache_dir, creator)
            if os.path.isdir(creator_path):
                files = 0
                size = 0
                for root, dirs, filenames in os.walk(creator_path):
                    for f in filenames:
                        files += 1
                        try:
                            size += os.path.getsize(os.path.join(root, f))
                        except:
                            pass
                stats['creators'].append({
                    'id': creator,
                    'files': files,
                    'size_mb': round(size / 1024 / 1024, 2)
                })
                stats['files'] += files
                stats['size_mb'] += round(size / 1024 / 1024, 2)

    return jsonify(stats)


if __name__ == '__main__':
    port = int(os.environ.get('API_PORT', 8080))
    app.run(host='0.0.0.0', port=port)
