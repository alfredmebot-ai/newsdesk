#!/bin/bash
# Alfred Newsdesk Update & Sync Script
# Runs every 4 hours via OpenClaw Cron

# 1. Generate fresh data & download images
python3 /root/.openclaw/workspace/privat/projects/newsdesk/scripts/fetch_data.py

# 2. Sync to WordPress Server (.14)
# Explicitly sync data and images, deleting old images on target
sshpass -p 'pool2114059' ssh root@192.168.0.14 "rm -rf /var/www/html/newsdesk/data/images && mkdir -p /var/www/html/newsdesk/data/images"
sshpass -p 'pool2114059' scp -r /root/.openclaw/workspace/privat/projects/newsdesk/data/* root@192.168.0.14:/var/www/html/newsdesk/data/

echo "Newsdesk Sync Completed: $(date)"
