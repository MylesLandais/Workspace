#!/bin/bash
# Bunny Client Setup Script
# Run inside Docker container to install dependencies

set -e

echo "=== Bunny Client Setup ==="

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "Error: package.json not found!"
    exit 1
fi

# Install dependencies
echo "Installing dependencies with Bun..."
bun install

echo "=== Setup Complete ==="
echo "Starting development server..."
