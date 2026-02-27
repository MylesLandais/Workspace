#!/usr/bin/env python3
"""Health monitor for imageboard monitoring system.

Monitors system health and alerts on performance issues.
Use for recovery validation and ongoing operations monitoring.

Usage:
    python3 monitor_imageboard_health.py              # One-time health check
    python3 monitor_imageboard_health.py --watch      # Continuous monitoring
    python3 monitor_imageboard_health.py --interval 10  # Custom update interval
"""

import argparse
import subprocess
import json
import time
import sys
from datetime import datetime
from pathlib import Path

# Default thresholds (DevOps best practices)
DEFAULT_THRESHOLDS = {
    'max_queue_depth': 100,
    'max_cpu_percent': 80,
    'max_memory_mb': 1024,
    'max_threads_monitored': 500
}

# Containers to monitor
CONTAINERS = [
    'imageboard_orchestrator',
    'imageboard_worker',
    'imageboard_dashboard',
    'imageboard_metrics_collector'
]

def get_container_stats(container_name):
    """Get CPU and memory stats for a container."""
    try:
        cmd = ['docker', 'stats', container_name, '--no-stream', '--format',
               '{{.CPUPerc}}\t{{.MemUsage}}']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return None, None, f"Container not found"
        
        line = result.stdout.strip()
        if not line:
            return None, None, "No stats available"
        
        cpu_str, mem_str = line.split('\t')
        
        # Parse CPU percentage
        cpu_percent = float(cpu_str.rstrip('%'))
        
        # Parse memory (format: "123.45MiB / 2GiB")
        mem_parts = mem_str.split('/')
        mem_used = mem_parts[0].strip()
        mem_used_mb = parse_memory_to_mb(mem_used)
        
        return cpu_percent, mem_used_mb, None
        
    except Exception as e:
        return None, None, str(e)

def parse_memory_to_mb(mem_str):
    """Convert memory string to MB."""
    mem_str = mem_str.strip().lower()
    value = float(mem_str.rstrip('mibgibkibtbpb'))
    
    if 'gib' in mem_str:
        return value * 1024
    elif 'kib' in mem_str:
        return value / 1024
    elif 'tb' in mem_str:
        return value * 1024 * 1024
    elif 'pb' in mem_str:
        return value * 1024 * 1024 * 1024
    else:  # MiB or default
        return value

def get_queue_depth():
    """Get Redis queue depth using docker exec."""
    try:
        # Try to find a redis container
        cmd = ['docker', 'ps', '--filter', 'name=redis', '--format', '{{.Names}}']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        redis_containers = result.stdout.strip().split('\n')
        redis_container = None
        
        for container in redis_containers:
            if container and 'redis' in container.lower():
                redis_container = container
                break
        
        if not redis_container:
            # Try valkey
            cmd = ['docker', 'ps', '--filter', 'name=valkey', '--format', '{{.Names}}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            valkey_containers = result.stdout.strip().split('\n')
            for container in valkey_containers:
                if container and 'valkey' in container.lower():
                    redis_container = container
                    break
        
        if not redis_container:
            return None, "No Redis/Valkey container found"
        
        # Get queue depth
        cmd = ['docker', 'exec', redis_container, 'redis-cli', 'LLEN', 'queue:monitors']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode != 0:
            return None, f"Redis exec failed: {result.stderr.strip()}"
        
        depth = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        return depth, None
        
    except Exception as e:
        return None, str(e)

def get_thread_stats():
    """Get statistics on monitored threads."""
    try:
        cache_dir = Path('/home/warby/Workspace/jupyter/cache/imageboard/threads')
        if not cache_dir.exists():
            return None, None, "Cache directory not found"
        
        # Count threads
        thread_dirs = [d for d in cache_dir.rglob('*/') if d.is_dir()]
        total_threads = sum(1 for d in thread_dirs if (d / 'thread.json').exists())
        
        # Count images
        images_dir = Path('/home/warby/Workspace/jupyter/cache/imageboard/shared_images')
        if images_dir.exists():
            image_files = list(images_dir.glob('*'))
            image_count = len([f for f in image_files if f.is_file()])
        else:
            image_count = None
        
        return total_threads, image_count, None
        
    except Exception as e:
        return None, None, str(e)

def check_container_health(container_name, thresholds):
    """Check if a container is healthy based on thresholds."""
    cpu, mem_mb, error = get_container_stats(container_name)
    
    if error:
        return {'status': 'error', 'message': error}
    
    alerts = []
    
    if cpu > thresholds['max_cpu_percent']:
        alerts.append(f"High CPU: {cpu:.1f}%")
    
    if mem_mb > thresholds['max_memory_mb']:
        alerts.append(f"High Memory: {mem_mb:.0f}MB")
    
    if alerts:
        return {
            'status': 'warning',
            'cpu': cpu,
            'memory_mb': mem_mb,
            'alerts': alerts
        }
    
    return {
        'status': 'ok',
        'cpu': cpu,
        'memory_mb': mem_mb
    }

def print_health_report(thresholds, queue_depth, thread_stats, container_statuses):
    """Print formatted health report."""
    print("=" * 70)
    print(f"IMAGEBOARD HEALTH CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    # Queue status
    print("Queue Status:")
    if queue_depth[0] is not None:
        depth = queue_depth[0]
        status = "OK" if depth <= thresholds['max_queue_depth'] else "WARNING"
        if depth > thresholds['max_queue_depth']:
            print(f"  Depth: {depth} [WARNING - exceeds threshold {thresholds['max_queue_depth']}]")
        else:
            print(f"  Depth: {depth} [{status}]")
    else:
        print(f"  Depth: Unable to check ({queue_depth[1]})")
    print()
    
    # Thread stats
    print("Collection Stats:")
    total_threads, image_count, error = thread_stats
    if error:
        print(f"  Error: {error}")
    else:
        print(f"  Monitored threads: {total_threads}")
        if image_count is not None:
            print(f"  Collected images: {image_count}")
        if total_threads > thresholds['max_threads_monitored']:
            print(f"  [WARNING - exceeds threshold {thresholds['max_threads_monitored']}]")
    print()
    
    # Container status
    print("Container Health:")
    all_ok = True
    for container in CONTAINERS:
        status = container_statuses.get(container)
        print(f"  {container}:")
        
        if status['status'] == 'error':
            print(f"    ERROR: {status['message']}")
            all_ok = False
        elif status['status'] == 'warning':
            print(f"    CPU: {status['cpu']:.1f}%")
            print(f"    Memory: {status['memory_mb']:.0f}MB")
            print(f"    Alerts: {', '.join(status['alerts'])}")
            all_ok = False
        else:
            print(f"    CPU: {status['cpu']:.1f}% [OK]")
            print(f"    Memory: {status['memory_mb']:.0f}MB [OK]")
    print()
    
    # Overall status
    print("=" * 70)
    if all_ok and queue_depth[0] is not None and queue_depth[0] <= thresholds['max_queue_depth']:
        print("OVERALL STATUS: HEALTHY")
    else:
        print("OVERALL STATUS: ISSUES DETECTED")
    print("=" * 70)

def monitor_loop(thresholds, interval):
    """Continuous monitoring loop."""
    print(f"Starting continuous monitoring (interval: {interval}s)")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            # Get all stats
            queue_depth = get_queue_depth()
            thread_stats = get_thread_stats()
            
            container_statuses = {}
            for container in CONTAINERS:
                container_statuses[container] = check_container_health(container, thresholds)
            
            # Print report
            print_health_report(thresholds, queue_depth, thread_stats, container_statuses)
            print()
            
            # Wait for next cycle
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")

def main():
    parser = argparse.ArgumentParser(description='Health monitor for imageboard system')
    parser.add_argument('--watch', action='store_true', help='Continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=10, help='Update interval in seconds (default: 10)')
    parser.add_argument('--max-queue', type=int, dest='max_queue_depth', help='Max queue depth threshold')
    parser.add_argument('--max-cpu', type=int, dest='max_cpu_percent', help='Max CPU percentage threshold')
    parser.add_argument('--max-memory', type=int, dest='max_memory_mb', help='Max memory MB threshold')
    
    args = parser.parse_args()
    
    # Apply custom thresholds
    thresholds = DEFAULT_THRESHOLDS.copy()
    if args.max_queue_depth:
        thresholds['max_queue_depth'] = args.max_queue_depth
    if args.max_cpu_percent:
        thresholds['max_cpu_percent'] = args.max_cpu_percent
    if args.max_memory_mb:
        thresholds['max_memory_mb'] = args.max_memory_mb
    
    if args.watch:
        monitor_loop(thresholds, args.interval)
    else:
        # Single health check
        queue_depth = get_queue_depth()
        thread_stats = get_thread_stats()
        
        container_statuses = {}
        for container in CONTAINERS:
            container_statuses[container] = check_container_health(container, thresholds)
        
        print_health_report(thresholds, queue_depth, thread_stats, container_statuses)

if __name__ == "__main__":
    main()
