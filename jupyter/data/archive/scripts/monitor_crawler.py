#!/usr/bin/env python3
"""Monitor the slow Reddit crawler with 5-minute intervals and bot detection."""

import subprocess
import time
import re
from datetime import datetime
from collections import defaultdict


def run_docker_command(cmd):
    """Run a docker exec command and return output."""
    try:
        result = subprocess.run(
            ["docker", "exec", "jupyter"] + cmd.split(),
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1


def check_crawler_running():
    """Check if crawler process is running."""
    stdout, _, _ = run_docker_command("ps aux")
    return "slow_reddit_crawler.py" in stdout


def get_recent_logs(lines=100):
    """Get recent docker logs."""
    result = subprocess.run(
        ["docker", "logs", "jupyter", "--tail", str(lines)],
        capture_output=True,
        text=True,
        timeout=10
    )
    return result.stdout + result.stderr


def analyze_logs_for_issues(logs):
    """Analyze logs for signs of bot detection or rate limiting."""
    issues = []
    warnings = []
    
    # Bot detection patterns
    patterns = {
        "rate_limit": [
            r"429",
            r"rate.?limit",
            r"too.?many.?requests",
            r"try.?again.?later",
        ],
        "captcha": [
            r"captcha",
            r"verify.?you.?are.?human",
            r"challenge",
        ],
        "blocked": [
            r"403",
            r"forbidden",
            r"blocked",
            r"access.?denied",
        ],
        "timeout": [
            r"timeout",
            r"timed.?out",
            r"connection.?reset",
        ],
        "error_5xx": [
            r"50[0-9]",
            r"internal.?server.?error",
            r"service.?unavailable",
        ],
    }
    
    log_lower = logs.lower()
    
    for issue_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.findall(pattern, log_lower, re.IGNORECASE)
            if matches:
                if issue_type in ["rate_limit", "blocked", "captcha"]:
                    issues.append(f"{issue_type.upper()}: Found {len(matches)} occurrences of '{pattern}'")
                else:
                    warnings.append(f"{issue_type.upper()}: Found {len(matches)} occurrences of '{pattern}'")
    
    return issues, warnings


def analyze_activity(logs):
    """Analyze crawler activity patterns."""
    stats = {
        "subreddits_processed": len(re.findall(r"Processing r/(\w+)", logs)),
        "posts_collected": len(re.findall(r"Collected \d+ posts", logs)),
        "cycles_completed": len(re.findall(r"CYCLE \d+", logs)),
        "errors": len(re.findall(r"ERROR", logs, re.IGNORECASE)),
        "delays": len(re.findall(r"\[DELAY\]", logs)),
    }
    
    # Extract recent subreddits
    recent_subreddits = re.findall(r"Processing r/(\w+)", logs)[-10:]
    
    # Check for stuck patterns (same subreddit repeated many times)
    subreddit_counts = defaultdict(int)
    for subreddit in re.findall(r"Processing r/(\w+)", logs):
        subreddit_counts[subreddit] += 1
    
    stuck_subreddits = [s for s, count in subreddit_counts.items() if count > 5]
    
    return stats, recent_subreddits, stuck_subreddits


def get_process_stats():
    """Get process CPU/memory stats."""
    stdout, _, _ = run_docker_command("ps aux | grep slow_reddit_crawler | grep -v grep")
    if not stdout.strip():
        return None
    
    parts = stdout.split()
    if len(parts) >= 11:
        return {
            "cpu": parts[2],
            "memory": parts[3],
            "rss": parts[5],
            "vsz": parts[4],
        }
    return None


def main():
    """Main monitoring loop."""
    print("=" * 80)
    print("REDDIT CRAWLER MONITOR")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Checking every 5 minutes...")
    print("=" * 80)
    print()
    
    check_count = 0
    
    try:
        while True:
            check_count += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"\n[{timestamp}] Check #{check_count}")
            print("-" * 80)
            
            # Check if crawler is running
            is_running = check_crawler_running()
            
            if not is_running:
                print("STATUS: CRAWLER NOT RUNNING")
                print("The crawler process has stopped!")
                print("\nTo restart:")
                print("  docker exec -d -w /home/jovyan/workspace jupyter python3 slow_reddit_crawler.py")
                break
            
            print("STATUS: RUNNING")
            
            # Get process stats
            proc_stats = get_process_stats()
            if proc_stats:
                print(f"Process: CPU={proc_stats['cpu']}% MEM={proc_stats['memory']}%")
            
            # Get and analyze logs
            logs = get_recent_logs(200)
            
            # Analyze for issues
            issues, warnings = analyze_logs_for_issues(logs)
            
            # Analyze activity
            stats, recent_subreddits, stuck_subreddits = analyze_activity(logs)
            
            # Print activity stats
            print(f"\nActivity Summary:")
            print(f"  Cycles completed: {stats['cycles_completed']}")
            print(f"  Subreddits processed: {stats['subreddits_processed']}")
            print(f"  Posts collected: {stats['posts_collected']}")
            print(f"  Errors encountered: {stats['errors']}")
            print(f"  Delays executed: {stats['delays']}")
            
            if recent_subreddits:
                print(f"\nRecent subreddits (last 10):")
                for subreddit in recent_subreddits[-10:]:
                    print(f"  - r/{subreddit}")
            
            if stuck_subreddits:
                print(f"\nWARNING: Possible stuck subreddits (processed >5 times):")
                for subreddit in stuck_subreddits:
                    print(f"  - r/{subreddit}")
            
            # Print warnings
            if warnings:
                print(f"\nWarnings ({len(warnings)}):")
                for warning in warnings[:5]:  # Limit to 5 most recent
                    print(f"  - {warning}")
            
            # Check for critical issues
            if issues:
                print(f"\nCRITICAL ISSUES DETECTED ({len(issues)}):")
                for issue in issues:
                    print(f"  !!! {issue}")
                
                # Check if we should stop
                critical_issues = [i for i in issues if any(x in i.upper() for x in ["RATE_LIMIT", "BLOCKED", "CAPTCHA"])]
                
                if critical_issues:
                    print("\n" + "=" * 80)
                    print("BOT DETECTION DETECTED - STOPPING CRAWLER")
                    print("=" * 80)
                    
                    # Stop the crawler
                    stdout, stderr, code = run_docker_command("pkill -f slow_reddit_crawler.py")
                    if code == 0:
                        print("Crawler stopped successfully")
                    else:
                        print(f"Error stopping crawler: {stderr}")
                    
                    print("\nIssues detected:")
                    for issue in critical_issues:
                        print(f"  - {issue}")
                    print("\nReview logs and adjust delays before restarting.")
                    break
            else:
                print("\nNo critical issues detected - crawler appears healthy")
            
            print("\n" + "-" * 80)
            print(f"Next check in 5 minutes...")
            print()
            
            # Wait 5 minutes
            time.sleep(300)  # 5 minutes
            
    except KeyboardInterrupt:
        print("\n" + "=" * 80)
        print("Monitoring stopped by user")
        print("=" * 80)
    except Exception as e:
        print(f"\nERROR in monitor: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()








