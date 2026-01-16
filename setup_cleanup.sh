#!/usr/bin/env bash
"""
Quick setup script for assets duplicate cleanup.
Choose scheduling method and get configured in seconds.
"""

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo "Assets Duplicate Cleanup Setup"
echo "========================================================================"
echo ""
echo "This script will set up periodic cleanup of duplicate images"
echo "from the assets folder (already in cache)."
echo ""
echo "Choose scheduling method:"
echo "  1) Manual only (no automation)"
echo "  2) Cron job (daily at 3 AM)"
echo "  3) Systemd timer (daily, recommended)"
echo "  4) Docker compose restart trigger"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
  1)
    echo ""
    echo "Manual mode selected."
    echo "Run cleanup anytime with:"
    echo "  python cleanup_assets_duplicates.py --cleanup"
    echo ""
    echo "Test dry-run first:"
    echo "  python cleanup_assets_duplicates.py"
    ;;
    
  2)
    echo ""
    echo "Setting up cron job..."
    
    # Check if cron line already exists
    if crontab -l 2>/dev/null | grep -q "cleanup_assets_duplicates.py"; then
      echo "ERROR: Cron job already exists."
      echo "Edit with: crontab -e"
      exit 1
    fi
    
    # Add cron job
    (crontab -l 2>/dev/null; echo "0 3 * * * cd $PWD && docker compose exec -T jupyterlab python /home/jovyan/workspaces/cleanup_assets_duplicates.py --cleanup --quiet >> /tmp/assets_cleanup.log 2>&1") | crontab -
    
    echo "✓ Cron job added!"
    echo "  Schedule: Daily at 3:00 AM"
    echo "  Log file: /tmp/assets_cleanup.log"
    echo ""
    echo "View logs: tail -f /tmp/assets_cleanup.log"
    echo "Edit cron: crontab -e"
    ;;
    
  3)
    echo ""
    echo "Setting up systemd timer..."
    
    # Check if already installed
    if systemctl list-unit-files | grep -q "cleanup_assets.timer"; then
      echo "ERROR: Systemd timer already installed."
      echo "Check status: systemctl status cleanup_assets.timer"
      exit 1
    fi
    
    # Install timer and service
    if [ "$EUID" -ne 0 ]; then
      echo "ERROR: Systemd setup requires sudo."
      echo "Run: sudo ./setup_cleanup.sh"
      exit 1
    fi
    
    cp cleanup_assets.timer /etc/systemd/system/
    cp cleanup_assets.service /etc/systemd/system/
    
    systemctl daemon-reload
    systemctl enable --now cleanup_assets.timer
    
    echo "✓ Systemd timer installed and started!"
    echo "  Schedule: Daily"
    echo "  View status: systemctl status cleanup_assets.timer"
    echo "  View logs: journalctl -u cleanup_assets.service -f"
    echo ""
    echo "List all timers: systemctl list-timers"
    ;;
    
  4)
    echo ""
    echo "Docker compose restart trigger setup..."
    echo ""
    echo "Add this to docker-compose.yml services section:"
    echo ""
    cat << 'EOF'
  cleanup-task:
    image: alpine:latest
    volumes:
      - .:/workspaces
      - /var/run/docker.sock:/var/run/docker.sock
    command: sh -c "cd /workspaces && docker compose exec -T jupyterlab python /home/jovyan/workspaces/cleanup_assets_duplicates.py --cleanup"
    profiles: ["cleanup"]
EOF
    echo ""
    echo "Then run cleanup with:"
    echo "  docker compose --profile cleanup up"
    ;;
    
  *)
    echo "ERROR: Invalid choice"
    exit 1
    ;;
esac

echo ""
echo "========================================================================"
echo "Setup complete!"
echo "========================================================================"
echo ""
echo "Documentation: ASSETS_CLEANUP_SETUP.md"
echo ""
