#!/usr/bin/env python3
"""
RunPod Serverless Build Monitor
Monitors build status and provides notifications for CI/CD pipelines
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Optional

class RunPodBuildMonitor:
    def __init__(self, api_key: str, endpoint_id: str):
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.graphql_url = "https://api.runpod.io/graphql"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_endpoint_status(self) -> Dict:
        """Get current endpoint status including build info via GraphQL"""
        query = """
        query {
            myself {
                endpoints {
                    id
                    name
                    templateId
                    workersMax
                    workersMin
                    gpuIds
                    idleTimeout
                }
            }
        }
        """
        payload = {"query": query}
        response = requests.post(self.graphql_url, headers=self.headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Find matching endpoint
        endpoints = data.get("data", {}).get("myself", {}).get("endpoints", [])
        for ep in endpoints:
            if ep.get("id") == self.endpoint_id:
                return ep
        
        # Return summary if endpoint not found
        return {"endpoints": endpoints, "endpoint_id": self.endpoint_id, "state": "NOT_FOUND"}
    
    def get_builds(self, limit: int = 10) -> List[Dict]:
        """Get recent builds for the endpoint"""
        # Note: Adjust this endpoint based on RunPod's actual API
        url = f"{self.base_url}/{self.endpoint_id}/builds"
        params = {"limit": limit}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json().get("builds", [])
    
    def get_build_logs(self, build_id: str) -> str:
        """Get logs for a specific build"""
        url = f"{self.base_url}/{self.endpoint_id}/builds/{build_id}/logs"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get("logs", "")
    
    def wait_for_build(self, timeout: int = 600, poll_interval: int = 10) -> Dict:
        """
        Wait for current build to complete
        Returns build status or raises TimeoutError
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_endpoint_status()
            
            # Check build state
            build_state = status.get("state", "")
            
            if build_state == "READY":
                print(f"[OK] Build completed successfully at {datetime.now()}")
                return status
            elif build_state == "FAILED":
                print(f"[FAIL] Build failed at {datetime.now()}")
                return status
            elif build_state in ["BUILDING", "WAITING"]:
                print(f"[WAIT] Build in progress... ({build_state})")
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Build did not complete within {timeout} seconds")
    
    def check_health(self) -> bool:
        """Run health check on the endpoint"""
        url = f"{self.base_url}/{self.endpoint_id}/health"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    def trigger_rebuild(self) -> Dict:
        """Trigger a manual rebuild"""
        url = f"{self.base_url}/{self.endpoint_id}/rebuild"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def detect_registry_push_failure(self, build_logs: str) -> Dict:
        """
        Detect registry push failure patterns in build logs (RISK-001)
        Returns structured failure report
        """
        import re
        from collections import Counter
        
        patterns = {
            'registry_push_failure': r'Error: neither /app/registry-push/output\.tar found',
            'layer_locking': r'layer-sha256:([a-f0-9]+).*locked for ([\d.]+)([µm]s|s)',
            'build_complete': r'Build complete\.',
            'push_started': r'Pushing image to registry',
            'build_id': r'build-logs-([a-f0-9-]+)\.txt',
            'timestamp': r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)',
        }
        
        findings = {
            'registry_push_failure_detected': False,
            'build_completed': False,
            'push_attempted': False,
            'layer_locking_errors': [],
            'critical_layer_hash': None,
            'max_lock_duration_ms': 0,
            'lock_duration_distribution': {},
            'total_lock_errors': 0,
            'build_id': None,
            'failure_timestamp': None,
        }
        
        # Extract build ID from log content or filename
        build_id_match = re.search(patterns['build_id'], build_logs)
        if build_id_match:
            findings['build_id'] = build_id_match.group(1)
        
        # Check for registry push failure
        if re.search(patterns['registry_push_failure'], build_logs):
            findings['registry_push_failure_detected'] = True
            # Extract timestamp of failure
            failure_matches = list(re.finditer(patterns['timestamp'], build_logs))
            if failure_matches:
                findings['failure_timestamp'] = failure_matches[-1].group(1)
        
        # Check if build completed
        if re.search(patterns['build_complete'], build_logs):
            findings['build_completed'] = True
        
        # Check if push was attempted
        if re.search(patterns['push_started'], build_logs):
            findings['push_attempted'] = True
        
        # Extract layer locking errors
        lock_durations = []
        layer_hash_counts = Counter()
        
        for match in re.finditer(patterns['layer_locking'], build_logs):
            layer_hash = match.group(1)
            duration = float(match.group(2))
            unit = match.group(3)
            
            # Convert to milliseconds
            if unit == 's':
                duration_ms = duration * 1000
            elif unit == 'ms':
                duration_ms = duration
            elif unit == 'µs':
                duration_ms = duration / 1000
            else:
                duration_ms = duration
            
            findings['layer_locking_errors'].append({
                'layer_hash': layer_hash,
                'duration_ms': duration_ms,
            })
            
            lock_durations.append(duration_ms)
            layer_hash_counts[layer_hash] += 1
            
            if duration_ms > findings['max_lock_duration_ms']:
                findings['max_lock_duration_ms'] = duration_ms
                findings['critical_layer_hash'] = layer_hash
        
        findings['total_lock_errors'] = len(findings['layer_locking_errors'])
        
        # Calculate distribution
        if lock_durations:
            findings['lock_duration_distribution'] = {
                'min': min(lock_durations),
                'max': max(lock_durations),
                'avg': sum(lock_durations) / len(lock_durations),
                'median': sorted(lock_durations)[len(lock_durations) // 2],
            }
            findings['layer_hash_frequency'] = dict(layer_hash_counts.most_common())
        
        return findings
    
    def format_failure_report(self, findings: Dict) -> str:
        """Format failure detection findings into readable report"""
        report = []
        report.append("=" * 60)
        report.append("Build Failure Analysis (RISK-001 / RISK-002)")
        report.append("=" * 60)
        
        if findings.get('build_id'):
            report.append(f"Build ID: {findings['build_id']}")
        if findings.get('failure_timestamp'):
            report.append(f"Failure Timestamp: {findings['failure_timestamp']}")
        report.append("")
        
        if findings['registry_push_failure_detected']:
            report.append("[FAIL] Registry Push Failure Detected (RISK-001)")
        else:
            report.append("[OK] No registry push failure detected")
        
        report.append(f"[{'OK' if findings['build_completed'] else 'UNKNOWN'}] Build completed: {findings['build_completed']}")
        report.append(f"[{'YES' if findings['push_attempted'] else 'NO'}] Push attempted: {findings['push_attempted']}")
        
        if findings['layer_locking_errors']:
            report.append(f"\n[WARN] Layer Locking Errors (RISK-002): {findings['total_lock_errors']} occurrences")
            report.append(f"Critical layer hash: {findings['critical_layer_hash']}")
            report.append(f"Max lock duration: {findings['max_lock_duration_ms']:.2f}ms")
            
            # Show distribution if available
            if findings.get('lock_duration_distribution'):
                dist = findings['lock_duration_distribution']
                report.append(f"\nLock Duration Statistics:")
                report.append(f"  Min: {dist['min']:.2f}ms")
                report.append(f"  Max: {dist['max']:.2f}ms")
                report.append(f"  Avg: {dist['avg']:.2f}ms")
                report.append(f"  Median: {dist['median']:.2f}ms")
            
            # Show layer hash frequency
            if findings.get('layer_hash_frequency'):
                report.append(f"\nLayer Hash Frequency:")
                for layer_hash, count in list(findings['layer_hash_frequency'].items())[:5]:
                    report.append(f"  {layer_hash[:16]}...: {count} occurrences")
            
            # Check if lock duration suggests push failure risk
            if findings['max_lock_duration_ms'] > 1000:
                report.append("\n[HIGH RISK] Lock duration >1s - high correlation with push failures")
            elif findings['max_lock_duration_ms'] > 100:
                report.append("\n[MEDIUM RISK] Lock duration >100ms - monitor closely")
            else:
                report.append("\n[LOW RISK] Lock duration acceptable")
        else:
            report.append("\n[OK] No layer locking errors detected")
        
        report.append("=" * 60)
        return "\n".join(report)
    
    def extract_build_id_from_filename(self, filename: str) -> Optional[str]:
        """Extract build ID from log filename"""
        import re
        match = re.search(r'build-logs-([a-f0-9-]+)\.txt', filename)
        return match.group(1) if match else None
    
    def generate_incident_report(self, findings: Dict, build_log_path: str = None) -> str:
        """Generate incident report template for RunPod support"""
        report = []
        report.append("## RunPod Build Failure Incident Report")
        report.append("")
        report.append(f"**Date:** {findings.get('failure_timestamp', datetime.now().isoformat())}")
        report.append(f"**Build ID(s):** {findings.get('build_id', 'UNKNOWN')}")
        report.append("")
        report.append("**Error Type:** Registry Push Failure (RISK-001)")
        report.append("")
        report.append("### Timeline")
        report.append(f"- Build completed: {findings.get('build_completed', 'UNKNOWN')}")
        report.append(f"- Push attempted: {findings.get('push_attempted', 'UNKNOWN')}")
        report.append(f"- Push failed: {findings.get('failure_timestamp', 'UNKNOWN')}")
        report.append("")
        report.append("### Error Details")
        report.append("```")
        report.append("Error: neither /app/registry-push/output.tar found nor /app/registry-push/.output-image/index.json present")
        report.append("Image push finished with wrong exit code")
        report.append("```")
        report.append("")
        
        if findings.get('layer_locking_errors'):
            report.append("### Layer Locking Pattern")
            report.append(f"- Layer hash: `{findings.get('critical_layer_hash', 'UNKNOWN')}`")
            report.append(f"- Total lock errors: {findings.get('total_lock_errors', 0)}")
            report.append(f"- Max lock duration: {findings.get('max_lock_duration_ms', 0):.2f}ms")
            if findings.get('lock_duration_distribution'):
                dist = findings['lock_duration_distribution']
                report.append(f"- Lock duration range: {dist['min']:.2f}ms - {dist['max']:.2f}ms")
            report.append("")
        
        report.append("### Build Details")
        report.append("- Dockerfile: `Dockerfile.runpod`")
        report.append("- Branch: `feature/runpod-worker`")
        if build_log_path:
            report.append(f"- Build log: `{build_log_path}`")
        report.append("")
        report.append("### Impact")
        report.append("- Deployments blocked: Yes")
        report.append("- Build time wasted: ~30+ minutes")
        report.append("")
        report.append("### Supporting Evidence")
        report.append(f"- Build logs available: {'Yes' if build_log_path else 'No'}")
        report.append(f"- Pattern observed in previous builds: Yes (RISK-001)")
        report.append("- Related risks: RISK-001, RISK-002")
        
        return "\n".join(report)
    
    def format_status_report(self, status: Dict) -> str:
        """Format status into readable report"""
        report = []
        report.append("=" * 60)
        report.append(f"RunPod Endpoint Status Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        if "endpoints" in status:
            # List all endpoints
            report.append(f"Looking for Endpoint ID: {self.endpoint_id}")
            report.append(f"Found {len(status['endpoints'])} endpoints:")
            for ep in status["endpoints"]:
                report.append(f"  - {ep.get('id')}: {ep.get('name', 'unnamed')}")
        else:
            # Single endpoint details
            report.append(f"Endpoint ID: {status.get('id', self.endpoint_id)}")
            report.append(f"Name: {status.get('name', 'N/A')}")
            report.append(f"Template ID: {status.get('templateId', 'N/A')}")
            report.append(f"GPU IDs: {status.get('gpuIds', [])}")
            report.append(f"Workers Min/Max: {status.get('workersMin', 0)}/{status.get('workersMax', 0)}")
            report.append(f"Idle Timeout: {status.get('idleTimeout', 'N/A')}s")
            
            workers = status.get("workers", [])
            if workers:
                report.append(f"Active Workers: {len(workers)}")
                for w in workers:
                    report.append(f"  - {w.get('id')}: {w.get('status')} ({w.get('gpuType')})")
            else:
                report.append("Active Workers: 0 (scaled down)")
            
            jobs = status.get("jobs", [])
            if jobs:
                report.append(f"Recent Jobs: {len(jobs)}")
                for j in jobs:
                    report.append(f"  - {j.get('id')}: {j.get('status')}")
        
        report.append("=" * 60)
        return "\n".join(report)


def main():
    """Main execution function"""
    # Configuration - replace with your actual values or use environment variables
    import os
    
    API_KEY = os.getenv("RUNPOD_API_KEY", "your-api-key-here")
    ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID", "jx1jkdf7ozhpmm")
    
    if API_KEY == "your-api-key-here":
        print("[WARN] Please set RUNPOD_API_KEY environment variable")
        sys.exit(1)
    
    monitor = RunPodBuildMonitor(API_KEY, ENDPOINT_ID)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            status = monitor.get_endpoint_status()
            print(monitor.format_status_report(status))
        
        elif command == "wait":
            print("Waiting for build to complete...")
            try:
                status = monitor.wait_for_build()
                print(monitor.format_status_report(status))
                sys.exit(0 if status.get("state") == "READY" else 1)
            except TimeoutError as e:
                print(f"[FAIL] {e}")
                sys.exit(1)
        
        elif command == "health":
            is_healthy = monitor.check_health()
            print(f"Health check: {'[OK] PASSED' if is_healthy else '[FAIL] FAILED'}")
            sys.exit(0 if is_healthy else 1)
        
        elif command == "rebuild":
            print("Triggering rebuild...")
            result = monitor.trigger_rebuild()
            print(f"Rebuild triggered: {result}")
        
        elif command == "logs":
            if len(sys.argv) > 2:
                build_id = sys.argv[2]
                logs = monitor.get_build_logs(build_id)
                print(logs)
            else:
                print("Usage: script.py logs <build_id>")
                sys.exit(1)
        
        elif command == "analyze":
            if len(sys.argv) > 2:
                log_file = sys.argv[2]
                try:
                    with open(log_file, 'r') as f:
                        log_content = f.read()
                    findings = monitor.detect_registry_push_failure(log_content)
                    print(monitor.format_failure_report(findings))
                    
                    # If failure detected, offer to generate incident report
                    if findings.get('registry_push_failure_detected'):
                        print("\n" + "=" * 60)
                        print("To generate an incident report for RunPod support, run:")
                        print(f"  python scripts/runpod_monitor.py incident {log_file}")
                        print("=" * 60)
                except FileNotFoundError:
                    print(f"[ERROR] Log file not found: {log_file}")
                    sys.exit(1)
            else:
                print("Usage: script.py analyze <log_file_path>")
                print("Analyzes build logs for RISK-001 (registry push failure) and RISK-002 (layer locking) patterns")
                sys.exit(1)
        
        elif command == "incident":
            if len(sys.argv) > 2:
                log_file = sys.argv[2]
                try:
                    with open(log_file, 'r') as f:
                        log_content = f.read()
                    findings = monitor.detect_registry_push_failure(log_content)
                    incident_report = monitor.generate_incident_report(findings, log_file)
                    print(incident_report)
                except FileNotFoundError:
                    print(f"[ERROR] Log file not found: {log_file}")
                    sys.exit(1)
            else:
                print("Usage: script.py incident <log_file_path>")
                print("Generates incident report template for RunPod support")
                sys.exit(1)
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: status, wait, health, rebuild, logs, analyze, incident")
            sys.exit(1)
    else:
        # Default: show status
        status = monitor.get_endpoint_status()
        print(monitor.format_status_report(status))


if __name__ == "__main__":
    main()

