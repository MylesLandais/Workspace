#!/bin/bash

# Start services with build if needed
echo "Starting Docker Compose services..."
docker compose up --build -d

if [ $? -ne 0 ]; then
  echo "Error: Failed to start services. Check 'docker compose logs' for details."
  exit 1
fi

echo "Services started successfully."

# Wait briefly for Jupyter to start, then retrieve token
sleep 5
echo "Retrieving JupyterLab access token..."
JUPYTER_TOKEN=$(docker logs $(docker compose ps -q jupyterlab) 2>&1 | grep -oP '(?<=token=)[a-f0-9]+' | head -1)

if [ -z "$JUPYTER_TOKEN" ]; then
  echo "Error: Could not retrieve token. Check 'docker compose logs jupyterlab'."
  exit 1
fi

URL="http://127.0.0.1:8888/?token=$JUPYTER_TOKEN"
echo "JupyterLab is running. Open in browser: $URL"

# Optional: auto-open in browser (uncomment for macOS/Linux)
# xdg-open "$URL" || open "$URL"

echo ""
echo "To stop: docker compose down"
echo "Logs: docker compose logs -f"
echo "Shell into jupyterlab: docker compose exec jupyterlab bash"