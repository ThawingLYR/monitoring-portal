#!/bin/sh
exec streamlit run streamlit_app.py \
    --server.port="$PORT" \
    --server.address=0.0.0.0 \
    --server.baseUrlPath=/ \
    --server.headless=false \
    --browser.serverAddress="$SERVER_ADDRESS"