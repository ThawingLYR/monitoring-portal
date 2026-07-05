#!/bin/sh

# Check if DOCKER-CRON is set
if [ -n "$DOCKER_CRON" ]; then
    # Run the Python script once (with instance check)
    /streamlit-app/run-cron.sh

    # Add an alias for run-cron
    echo "alias run-cron='/streamlit-app/run-cron.sh'" >> ~/.bashrc
    echo "Container is now waiting for commands. You can use 'run-cron' to re-run the script."

    # Keep the container running, but respect termination signals
    exec sh -c "sleep infinity & wait"

    export DOCKER_CRON=1
else
    # Default behavior: just run the Python script
    exec /streamlit-app/run-cron.sh
fi