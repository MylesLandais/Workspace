"""System metrics collector for imageboard crawler."""

import time
import subprocess
import json
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PUSHGATEWAY_URL = os.environ.get("PUSHGATEWAY_URL", "http://localhost:9091")
COLLECTION_INTERVAL = int(os.environ.get("COLLECTION_INTERVAL", 30))

# Global counter for cycle tracking
cycle_count = 0

def get_container_stats(container_name):
    """Get CPU and memory stats for a container."""
    return 0.0, 0.0  # Disabled in host network mode

def get_queue_depth(redis_url):
    """Get Redis queue depth."""
    try:
        result = subprocess.run(
            "redis-cli -p 6379 LLEN queue:monitors",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
    except Exception as e:
        logger.error(f"Error getting queue depth: {e}")
    return 0

def push_to_pushgateway(job_name, metrics):
    """Push metrics to Prometheus Pushgateway."""
    try:
        metrics_text = "\n".join(f"{k} {v}" for k, v in metrics.items())
        # Use full curl path to avoid PATH issues
        result = subprocess.run(
            ["/run/current-system/sw/bin/curl", "-X", "POST", "-s", 
             f"{PUSHGATEWAY_URL}/metrics/job/{job_name}",
             "--data-binary", metrics_text],
            capture_output=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.error(f"Failed to push metrics to Pushgateway: {result.stderr}")
    except Exception as e:
        logger.error(f"Error pushing to Pushgateway: {e}")

def export_metrics_to_json(metrics):
    """Export metrics to JSON file for later analysis."""
    try:
        output_dir = "/var/lib/prometheus/metrics"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"metrics_{timestamp}.json")
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics
            }, f, indent=2)
        
        logger.info(f"Metrics exported to {filename}")
    except Exception as e:
        logger.error(f"Error exporting metrics to JSON: {e}")

def collect_loop():
    """Main collection loop."""
    global cycle_count
    logger.info(f"Starting metrics collector (interval: {COLLECTION_INTERVAL}s)")
    logger.info(f"Pushgateway URL: {PUSHGATEWAY_URL}")
    
    while True:
        try:
            # Collect system metrics (just queue depth, no docker stats in host mode)
            queue_depth = get_queue_depth("redis://localhost:6379")
            
            metrics = {
                "timestamp": int(time.time()),
                "orchestrator_cpu_percent": 0.0,
                "orchestrator_memory_percent": 0.0,
                "worker_cpu_percent": 0.0,
                "worker_memory_percent": 0.0,
                "queue_depth": queue_depth,
                "collection_interval": COLLECTION_INTERVAL
            }
            
            # Push to Pushgateway
            push_to_pushgateway("imageboard_system", metrics)
            
            # Export to JSON every 10 collection cycles (5 min default)
            cycle_count += 1
            
            if cycle_count % 10 == 0:
                export_metrics_to_json(metrics)
            
            logger.info(f"Metrics collected: Queue: {queue_depth}")
            
        except Exception as e:
            logger.error(f"Error in collection loop: {e}")
        
        time.sleep(COLLECTION_INTERVAL)

if __name__ == "__main__":
    try:
        collect_loop()
    except KeyboardInterrupt:
        logger.info("Metrics collector stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in metrics collector: {e}")
        raise
