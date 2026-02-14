#!/usr/bin/env bash
#
# Dashboard Setup Script for Bunny
# Cleans build cache and reinstalls dependencies after dashboard merge
#

set -e

echo "🧹 Cleaning Next.js build cache..."
cd app/client
rm -rf .next

echo "Installing dependencies with bun..."
bun install

echo "Setup complete!"
echo ""
echo "To start the dashboard:"
echo "  devenv up                    # Start all services (recommended)"
echo "  bun run dev                  # Just Next.js dev server"
echo "  bun run dev:collab           # Next.js + collaboration server"
echo ""
echo "Visit: http://localhost:3000/dashboard"

