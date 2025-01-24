#!/bin/bash

# Start Xvfb
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &

# Wait for Xvfb to start
sleep 5

# Start Flask server
python webserver/webserver.py &

# Start WebSocket server
python motivo/04_ws_example.py