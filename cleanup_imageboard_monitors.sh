#!/bin/bash

# Find and kill imageboard monitor processes
echo "Looking for monitor_imageboard_thread.py processes..."
pids=$(pgrep -f "monitor_imageboard_thread.py")

if [ -z "$pids" ]; then
    echo "No monitor processes found."
else
    echo "Found $(echo "$pids" | wc -l) processes."
    echo "Killing processes..."
    echo "$pids" | xargs kill
    echo "Done."
fi

# Also check for orchestrator
echo "Looking for orchestrator..."
orch_pid=$(pgrep -f "imageboard_catalog_orchestrator.py")
if [ -n "$orch_pid" ]; then
    echo "Found orchestrator (PID $orch_pid)."
    read -p "Kill orchestrator too? (y/N) " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        kill $orch_pid
        echo "Orchestrator killed."
    fi
fi
