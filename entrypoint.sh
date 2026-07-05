#!/bin/sh

/streamlit-app/run-cron.sh

if [ "$DOCKER_CRON" = "1" ]; then
    /streamlit-app/run-cron.sh

    echo "Container running in cron mode."
    exec sleep infinity
else
    exec /streamlit-app/run-cron.sh
fi