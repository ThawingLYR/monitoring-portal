#!/bin/bash

echo "Starting cron jobs..."

# Set default repository if THAWINGLYR_CONFIG_REPO is not defined
REPO_URL=${THAWINGLYR_CONFIG_REPO:-"https://github.com/ThawingLYR/monitoring-portal-configuration.git"}
echo "Using repository URL: $REPO_URL"

CONFIG_FOLDER="config"

# Save the initial directory
INITIAL_DIR=$(pwd)



# echo "Making sure we are using the latest configuration..."
# if [ -d "$CONFIG_FOLDER" ]; then
#     # If the folder exists, pull the latest changes
#     echo "Folder '$CONFIG_FOLDER' exists. Pulling the latest changes..."
#     cd "$CONFIG_FOLDER" || exit
#     git pull origin main
#     # Return to the initial directory
#     cd "$INITIAL_DIR" || exit
# else
#     # If the folder does not exist, clone the repository
#     echo "Folder '$CONFIG_FOLDER' does not exist. Cloning the repository..."
#     git clone "$REPO_URL" "$CONFIG_FOLDER"
# fi

echo "Let's run the cron jobs..."

python cron-jobs.py



