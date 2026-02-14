#!/bin/bash
# Setup Playwright for Creepy Crawly spider
# This script installs Playwright and its browsers in the Docker container

echo "=========================================="
echo "Installing Playwright for Creepy Crawly"
echo "=========================================="

# Install Playwright
docker exec -w /home/jovyan/workspace jupyter pip install playwright

# Install Chromium browser
docker exec -w /home/jovyan/workspace jupyter playwright install chromium

echo ""
echo "✅ Playwright installed successfully!"
echo ""
echo "You can now run the RSS inbox checker:"
echo "  python3 check_rss_inbox.py --help"
echo ""
