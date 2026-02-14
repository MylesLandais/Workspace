"""OpenTelemetry-based monitoring for imageboard crawler."""

import os
import sys
import time
import json
import subprocess
import argparse
import signal
import shutil
from datetime import datetime
from pathlib import Path

class OTelMonitor:
    """OTEL-based monitoring orchestrator for imageboard crawler."""
    
    def __init__(self, duration_minutes=240, alert_level="conservative"):
        self.duration_seconds = duration_minutes * 60
        self.alert_level = alert_level
        self.start_time = time.time()
        self.check_count = 0
        self.alerts_history = []
        self.metrics_history = []
        self.session_id = f"monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logs_dir = Path("logs/metrics")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.alert_thresholds = {
            "conservative": {
                "queue_depth": 100,
                "queue_duration": 600,
                "failure_rate": 0.20,
                "failure_duration": 300,
                "no_jobs_duration": 900
            }
        }
        
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown."""
        print("\n\nShutdown signal received. Generating final report...")
        self.stop()
        sys.exit(0)
    
    def check_services_running(self):
        """Check if crawler services are running."""
        services = [
            "imageboard_orchestrator",
            "imageboard_worker",
            "prometheus",
            "pushgateway"
        ]
        
        status = {}
        for service in services:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", service],
                capture_output=True,
                text=True
            )
            status[service] = result.stdout.strip() == "true"
        
        return status
    
    def get_docker_stats(self):
        """Get CPU/memory stats from docker."""
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format",
             "table {{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}"],
            capture_output=True,
            text=True
        )
        
        stats = {}
        lines = result.stdout.split('\n')[1:]  # Skip header
        for line in lines:
            if not line.strip():
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                name = parts[0].strip()
                cpu = float(parts[1].rstrip('%')) if parts[1] != '--' else 0
                mem = float(parts[2].rstrip('%')) if parts[2] != '--' else 0
                if any(s in name for s in ['orchestrator', 'worker', 'prometheus']):
                    stats[name] = {"cpu": cpu, "memory": mem}
        
        return stats
    
    def get_prometheus_metrics(self):
        """Fetch metrics from Prometheus."""
        metrics = {}
        
        queries = {
            "catalog_polls": "imageboard_catalog_polls_total",
            "jobs_processed": "imageboard_jobs_processed_total",
            "jobs_success": "imageboard_jobs_success_total",
            "jobs_failed": "imageboard_jobs_failed_total",
            "queue_depth": "imageboard_queue_depth"
        }
        
        for name, query in queries.items():
            try:
                result = subprocess.run(
                    ["curl", "-s", "http://localhost:9090/api/v1/query",
                     "--data-urlencode", f"query={query}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    if data.get('status') == 'success' and data.get('data', {}).get('result'):
                        metrics[name] = float(data['data']['result'][0].get('value', [0, '0'])[1])
                    else:
                        metrics[name] = 0
            except Exception as e:
                metrics[name] = 0
        
        return metrics
    
    def check_alerts(self, status, stats, prom_metrics):
        """Check for alert conditions."""
        alerts = []
        thresholds = self.alert_thresholds[self.alert_level]
        
        # Service stopped
        for service, running in status.items():
            if not running:
                alerts.append({
                    "timestamp": datetime.now().isoformat(),
                    "level": "CRITICAL",
                    "service": service,
                    "message": f"{service} is not running"
                })
        
        # Queue depth alert
        if prom_metrics.get('queue_depth', 0) > thresholds['queue_depth']:
            alerts.append({
                "timestamp": datetime.now().isoformat(),
                "level": "WARNING",
                "type": "queue_backlog",
                "message": f"Queue depth {prom_metrics['queue_depth']} exceeds threshold {thresholds['queue_depth']}"
            })
        
        # Failure rate alert
        total_jobs = prom_metrics.get('jobs_processed', 0)
        failed_jobs = prom_metrics.get('jobs_failed', 0)
        if total_jobs > 0 and (failed_jobs / total_jobs) > thresholds['failure_rate']:
            alerts.append({
                "timestamp": datetime.now().isoformat(),
                "level": "WARNING",
                "type": "high_failure_rate",
                "message": f"Failure rate {(failed_jobs/total_jobs)*100:.1f}% exceeds threshold {thresholds['failure_rate']*100}%"
            })
        
        return alerts
    
    def export_metrics_to_json(self, status, stats, prom_metrics, alerts):
        """Export metrics to JSON file."""
        data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": int(time.time() - self.start_time),
            "system_status": status,
            "docker_stats": stats,
            "prometheus_metrics": prom_metrics,
            "alerts": alerts,
            "alert_level": self.alert_level
        }
        
        self.metrics_history.append(data)
        
        filename = self.logs_dir / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename
    
    def generate_final_report(self):
        """Generate final monitoring report."""
        if not self.metrics_history:
            return None
        
        # Calculate aggregates
        total_checks = len(self.metrics_history)
        total_catalog_polls = max(m['prometheus_metrics'].get('catalog_polls', 0) for m in self.metrics_history)
        total_jobs = max(m['prometheus_metrics'].get('jobs_processed', 0) for m in self.metrics_history)
        total_alerts = len([a for m in self.metrics_history for a in m['alerts']])
        
        # Success rate
        success = max(m['prometheus_metrics'].get('jobs_success', 0) for m in self.metrics_history)
        failed = max(m['prometheus_metrics'].get('jobs_failed', 0) for m in self.metrics_history)
        success_rate = (success / (success + failed) * 100) if (success + failed) > 0 else 100
        
        report = f"""# Imageboard Crawler - OTEL Monitoring Report

Session ID: {self.session_id}
Monitoring Duration: {int((time.time() - self.start_time) / 60)} minutes
Check Count: {total_checks}
Alert Level: {self.alert_level}

## Summary Statistics

- Total Catalog Polls: {total_catalog_polls}
- Total Jobs Processed: {total_jobs}
- Job Success Rate: {success_rate:.1f}%
- Total Alerts: {total_alerts}

## Alerts History

"""
        
        for entry in self.metrics_history:
            if entry['alerts']:
                report += f"\n### {entry['timestamp']}\n"
                for alert in entry['alerts']:
                    report += f"- [{alert['level']}] {alert['message']}\n"
        
        if total_alerts == 0:
            report += "No alerts detected during monitoring session.\n"
        
        report += f"""

## Metrics Export

Metrics exported to: {self.logs_dir}/
Prometheus UI: http://localhost:9090
"""
        
        report_path = self.logs_dir / f"report_{self.session_id}.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        return report_path
    
    def display_dashboard(self, status, stats, prom_metrics, alerts):
        """Display live dashboard."""
        elapsed = int((time.time() - self.start_time) / 60)
        
        print("\033[2J\033[H", end="")  # Clear screen
        print("=" * 70)
        print("IMAGEBOARD CRAWLER - OTEL MONITORING")
        print("=" * 70)
        print(f"Duration: {elapsed}m | Check #{self.check_count}")
        print("-" * 70)
        
        # Service status
        print("STATUS:")
        for service, running in status.items():
            status_str = "Running" if running else "STOPPED"
            if service in stats:
                cpu = stats[service].get('cpu', 0)
                mem = stats[service].get('memory', 0)
                print(f"  {service:25} {status_str:10} (CPU: {cpu:5.1f}%, MEM: {mem:5.1f}%)")
            else:
                print(f"  {service:25} {status_str:10}")
        
        print()
        print("METRICS SUMMARY (Current):")
        print(f"  Catalog polls: {prom_metrics.get('catalog_polls', 0):.0f}")
        print(f"  Jobs processed: {prom_metrics.get('jobs_processed', 0):.0f}")
        print(f"  Jobs success: {prom_metrics.get('jobs_success', 0):.0f}")
        print(f"  Jobs failed: {prom_metrics.get('jobs_failed', 0):.0f}")
        print(f"  Queue depth: {prom_metrics.get('queue_depth', 0):.0f}")
        
        total_jobs = prom_metrics.get('jobs_processed', 0)
        if total_jobs > 0:
            success_rate = (prom_metrics.get('jobs_success', 0) / total_jobs) * 100
            print(f"  Success rate: {success_rate:.1f}%")
        
        if alerts:
            print()
            print(f"ALERTS ({len(alerts)}):")
            for alert in alerts[-5:]:  # Show last 5 alerts
                print(f"  [{alert['level']}] {alert['message']}")
        else:
            print()
            print("ALERTS: NONE")
        
        print()
        print("EXPORT: Prometheus http://localhost:9090")
        print("       Logs: logs/metrics/")
        print()
        print("Press Ctrl+C to stop monitoring")
        print("=" * 70)
    
    def run(self):
        """Main monitoring loop."""
        print(f"Starting OTEL monitoring for {self.duration_seconds // 60} minutes")
        print(f"Alert level: {self.alert_level}")
        print(f"Session ID: {self.session_id}")
        print()
        
        while time.time() - self.start_time < self.duration_seconds:
            try:
                self.check_count += 1
                
                # Collect data
                status = self.check_services_running()
                stats = self.get_docker_stats()
                prom_metrics = self.get_prometheus_metrics()
                alerts = self.check_alerts(status, stats, prom_metrics)
                
                # Store alerts
                if alerts:
                    self.alerts_history.extend(alerts)
                
                # Export metrics every 10 checks (~5 min)
                if self.check_count % 10 == 0:
                    export_path = self.export_metrics_to_json(status, stats, prom_metrics, alerts)
                    print(f"\nMetrics exported: {export_path}")
                
                # Display dashboard
                self.display_dashboard(status, stats, prom_metrics, alerts)
                
                # Sleep
                time.sleep(30)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(30)
        
        # Generate final report
        print("\nGenerating final report...")
        report_path = self.generate_final_report()
        print(f"Report saved: {report_path}")
    
    def stop(self):
        """Stop monitoring and generate report."""
        self.generate_final_report()


def main():
    parser = argparse.ArgumentParser(description="OTEL-based monitoring for imageboard crawler")
    parser.add_argument("--duration", type=int, default=240, help="Monitoring duration in minutes")
    parser.add_argument("--alerts", choices=["conservative", "moderate", "verbose"], default="conservative",
                       help="Alert sensitivity level")
    
    args = parser.parse_args()
    
    monitor = OTelMonitor(duration_minutes=args.duration, alert_level=args.alerts)
    monitor.run()


if __name__ == "__main__":
    main()
