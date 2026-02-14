#!/usr/bin/env python3
"""
RunPod Build Retry Script
Automatically detects RISK-001 failures and retries builds with exponential backoff
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

# Import monitor for analysis
# Add parent directory to path to import runpod_monitor
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
try:
    from runpod_monitor import RunPodBuildMonitor
except ImportError:
    # Fallback if import fails
    print("[ERROR] Failed to import RunPodBuildMonitor. Make sure runpod_monitor.py is in the same directory.")
    sys.exit(1)


class RunPodRetry:
    def __init__(self, api_key: str, endpoint_id: str, max_retries: int = 3):
        self.monitor = RunPodBuildMonitor(api_key, endpoint_id)
        self.max_retries = max_retries
        self.retry_delays = [300, 600, 900]  # 5min, 10min, 15min in seconds
        self.state_file = Path.home() / ".runpod_retry_state.json"
    
    def load_retry_state(self) -> Dict:
        """Load retry state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Failed to load retry state: {e}")
        return {}
    
    def save_retry_state(self, state: Dict):
        """Save retry state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[WARN] Failed to save retry state: {e}")
    
    def check_build_log_for_failure(self, log_file: str) -> Optional[Dict]:
        """Check if build log shows RISK-001 failure"""
        try:
            with open(log_file, 'r') as f:
                log_content = f.read()
            findings = self.monitor.detect_registry_push_failure(log_content)
            
            if findings.get('registry_push_failure_detected'):
                return findings
            return None
        except FileNotFoundError:
            print(f"[ERROR] Log file not found: {log_file}")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to analyze log: {e}")
            return None
    
    def should_retry(self, build_id: str) -> bool:
        """Check if we should retry this build (not exceeded max retries)"""
        state = self.load_retry_state()
        build_retries = state.get('build_retries', {})
        retry_count = build_retries.get(build_id, 0)
        return retry_count < self.max_retries
    
    def record_retry(self, build_id: str):
        """Record that we're retrying a build"""
        state = self.load_retry_state()
        if 'build_retries' not in state:
            state['build_retries'] = {}
        if build_id not in state['build_retries']:
            state['build_retries'][build_id] = 0
        state['build_retries'][build_id] += 1
        state['last_retry'] = {
            'build_id': build_id,
            'timestamp': datetime.now().isoformat(),
        }
        self.save_retry_state(state)
    
    def get_retry_count(self, build_id: str) -> int:
        """Get retry count for a build"""
        state = self.load_retry_state()
        return state.get('build_retries', {}).get(build_id, 0)
    
    def retry_build(self, build_id: str, attempt: int, delay: int):
        """Trigger a rebuild with delay"""
        print(f"[INFO] Retry attempt {attempt}/{self.max_retries} for build {build_id}")
        print(f"[INFO] Waiting {delay // 60} minutes before retry...")
        
        # Wait for delay
        for remaining in range(delay, 0, -60):
            minutes = remaining // 60
            print(f"[WAIT] {minutes} minutes remaining...", end='\r')
            time.sleep(60)
        print(f"[WAIT] Retrying now...")
        
        # Trigger rebuild
        try:
            result = self.monitor.trigger_rebuild()
            print(f"[OK] Rebuild triggered: {result}")
            self.record_retry(build_id)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to trigger rebuild: {e}")
            return False
    
    def handle_failed_build(self, log_file: str, build_id: Optional[str] = None):
        """Handle a failed build - analyze and retry if appropriate"""
        print("=" * 60)
        print("RunPod Build Retry Handler")
        print("=" * 60)
        
        # Extract build ID from filename if not provided
        if not build_id:
            build_id = self.monitor.extract_build_id_from_filename(log_file)
            if not build_id:
                print("[ERROR] Could not extract build ID from filename")
                print("Please provide build ID manually or use filename format: build-logs-<build-id>.txt")
                return False
        
        print(f"Build ID: {build_id}")
        
        # Check if build log shows failure
        findings = self.check_build_log_for_failure(log_file)
        if not findings:
            print("[OK] No RISK-001 failure detected in build log")
            return False
        
        print("[FAIL] RISK-001 (Registry Push Failure) detected")
        print(f"  - Build completed: {findings.get('build_completed', False)}")
        print(f"  - Push attempted: {findings.get('push_attempted', False)}")
        print(f"  - Layer locking errors: {findings.get('total_lock_errors', 0)}")
        print(f"  - Max lock duration: {findings.get('max_lock_duration_ms', 0):.2f}ms")
        
        # Check if we should retry
        if not self.should_retry(build_id):
            retry_count = self.get_retry_count(build_id)
            print(f"\n[SKIP] Maximum retries ({self.max_retries}) already reached for this build")
            print(f"  - Previous retry attempts: {retry_count}")
            print("  - Manual intervention required")
            return False
        
        # Determine retry attempt number
        retry_count = self.get_retry_count(build_id)
        attempt = retry_count + 1
        delay = self.retry_delays[min(attempt - 1, len(self.retry_delays) - 1)]
        
        print(f"\n[RETRY] Scheduling retry attempt {attempt}/{self.max_retries}")
        print(f"  - Delay: {delay // 60} minutes")
        print(f"  - Previous attempts: {retry_count}")
        
        # Ask for confirmation (can be disabled with --auto flag)
        return self.retry_build(build_id, attempt, delay)


def main():
    parser = argparse.ArgumentParser(
        description="Automatically retry RunPod builds that fail with RISK-001 (registry push failure)"
    )
    parser.add_argument(
        "log_file",
        help="Path to build log file (format: build-logs-<build-id>.txt)"
    )
    parser.add_argument(
        "--build-id",
        help="Build ID (optional, extracted from filename if not provided)"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retry attempts (default: 3)"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically retry without confirmation (use with caution)"
    )
    parser.add_argument(
        "--api-key",
        help="RunPod API key (or set RUNPOD_API_KEY env var)"
    )
    parser.add_argument(
        "--endpoint-id",
        help="RunPod endpoint ID (or set RUNPOD_ENDPOINT_ID env var)"
    )
    
    args = parser.parse_args()
    
    # Get API key and endpoint ID
    api_key = args.api_key or os.getenv("RUNPOD_API_KEY")
    endpoint_id = args.endpoint_id or os.getenv("RUNPOD_ENDPOINT_ID")
    
    if not api_key:
        print("[ERROR] RunPod API key required")
        print("  Set RUNPOD_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    if not endpoint_id:
        print("[ERROR] RunPod endpoint ID required")
        print("  Set RUNPOD_ENDPOINT_ID environment variable or use --endpoint-id")
        sys.exit(1)
    
    # Create retry handler
    retry_handler = RunPodRetry(api_key, endpoint_id, max_retries=args.max_retries)
    
    # Handle failed build
    success = retry_handler.handle_failed_build(args.log_file, args.build_id)
    
    if success:
        print("\n[OK] Retry scheduled successfully")
        print("Monitor build status with: python scripts/runpod_monitor.py wait")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

