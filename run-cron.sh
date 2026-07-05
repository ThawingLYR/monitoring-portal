#!/bin/bash
set -e

LOCKFILE=/tmp/run-cron.lock
exec 200>$LOCKFILE
flock -n 200 || {
  echo "Cron already running. Exiting."
  exit 1
}

echo "Starting cron jobs..."

REPO_URL=${THAWINGLYR_CONFIG_REPO:-"https://github.com/ThawingLYR/monitoring-portal-configuration.git"}
CONFIG_FOLDER="config"

echo "Ensuring latest configuration from: $REPO_URL"

if [ -d "$CONFIG_FOLDER/.git" ]; then
    echo "Updating existing config repo..."
    git -C "$CONFIG_FOLDER" fetch origin
    git -C "$CONFIG_FOLDER" reset --hard origin/main
else
    echo "Cloning config repo..."
    git clone "$REPO_URL" "$CONFIG_FOLDER"
fi

echo "Configuration ready. Running cron jobs..."

python cron-jobs.py