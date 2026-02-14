#!/bin/bash
# Run the crawler monitor

cd /home/warby/Workspace/jupyter
python3 monitor_crawler.py 2>&1 | tee -a crawler_monitor.log








