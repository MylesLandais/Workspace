# Assets Duplicate Cleanup Setup Guide

This directory contains a recurring cleanup task for removing duplicate images
from the assets folder that already exist in the cache.

## Files

- `cleanup_assets_duplicates.py` - Main cleanup script
- `cleanup_assets.cron` - Cron job configuration
- `cleanup_assets.timer` - Systemd timer configuration
- `cleanup_assets.service` - Systemd service configuration

## Quick Start

### Option 1: Manual Dry Run (Safe, Default)

```bash
cd /home/warby/Workspace/jupyter
python cleanup_assets_duplicates.py
```

### Option 2: Manual Cleanup

```bash
cd /home/warby/Workspace/jupyter
python cleanup_assets_duplicates.py --cleanup
```

### Option 3: Via Docker Compose

```bash
docker compose exec -T jupyterlab python /home/jovyan/workspaces/cleanup_assets_duplicates.py --cleanup
```

## Setup as Recurring Task

### Option A: Cron Job (Simplest)

```bash
# Edit crontab
crontab -e

# Add this line (daily at 3 AM)
0 3 * * * cd /home/warby/Workspace/jupyter && docker compose exec -T jupyterlab python /home/jovyan/workspaces/cleanup_assets_duplicates.py --cleanup --quiet >> /tmp/assets_cleanup.log 2>&1
```

### Option B: Systemd Timer (Modern, Recommended)

```bash
# Copy timer and service files
sudo cp cleanup_assets.timer /etc/systemd/system/
sudo cp cleanup_assets.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start timer
sudo systemctl enable --now cleanup_assets.timer

# Check status
systemctl list-timers --all
journalctl -u cleanup_assets.service -f
```

### Option C: GitHub Actions (If using CI/CD)

Add to `.github/workflows/assets-cleanup.yml`:

```yaml
name: Assets Cleanup

on:
  schedule:
    - cron: '0 3 * * *'  # Daily at 3 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run cleanup
        run: |
          docker compose exec -T jupyterlab python /home/jovyan/workspaces/cleanup_assets_duplicates.py --cleanup
```

## Configuration

The script uses these defaults (can be changed with flags):

- **Assets dir**: `/home/jovyan/assets` (or `--assets-dir`)
- **Cache dir**: `cache` (relative to workspaces) (or `--cache-dir`)
- **Dry run**: Enabled by default (safe)
- **Quiet mode**: Disabled (use `-q` or `--quiet` for cron)

## Safety

The cleanup script is **safe** because:

1. Only removes files from `assets/` directory
2. Never touches `cache/` directory (HTML references depend on it)
3. Requires `--cleanup` flag to actually delete files (default is dry-run)
4. Checks file contents via SHA256 hash before considering it a duplicate

## Monitoring

### Check cron logs

```bash
tail -f /tmp/assets_cleanup.log
```

### Check systemd logs

```bash
# View recent runs
journalctl -u cleanup_assets.service --since "1 hour ago"

# Follow logs
journalctl -u cleanup_assets.service -f

# Check timer status
systemctl status cleanup_assets.timer
```

## Troubleshooting

### Script not running via cron

1. Check cron is running: `systemctl status cron`
2. Check crontab: `crontab -l`
3. Check logs: `cat /tmp/assets_cleanup.log`
4. Ensure docker compose is in PATH

### Script not running via systemd

1. Check service: `systemctl status cleanup_assets.service`
2. Check timer: `systemctl status cleanup_assets.timer`
3. View logs: `journalctl -xe`
4. Reload if needed: `sudo systemctl daemon-reload`

### Too many/false positives

1. Run dry-run first: `python cleanup_assets_duplicates.py`
2. Verify cache has the files: `ls cache/imageboard/images/<hash>.*`
3. Check your assets folder location

## Testing

Before enabling automatic cleanup, test manually:

```bash
# Test dry-run
python cleanup_assets_duplicates.py

# Review the list, then run actual cleanup
python cleanup_assets_duplicates.py --cleanup
```

## Frequency Recommendations

- **Development**: Daily or hourly dry-run
- **Production**: Weekly or monthly cleanup
- **Heavy usage**: Daily cleanup with quiet mode
- **Light usage**: Monthly or quarterly cleanup

## Uninstalling

### Remove Cron Job

```bash
crontab -e
# Delete the cleanup line
```

### Remove Systemd Timer

```bash
sudo systemctl disable --now cleanup_assets.timer
sudo rm /etc/systemd/system/cleanup_assets.timer
sudo rm /etc/systemd/system/cleanup_assets.service
sudo systemctl daemon-reload
```
