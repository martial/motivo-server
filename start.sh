#!/bin/bash

# ASCII Art Banner
echo '
███╗   ███╗ ██████╗ ████████╗██╗██╗   ██╗ ██████╗     ███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗ 
████╗ ████║██╔═══██╗╚══██╔══╝██║██║   ██║██╔═══██╗    ██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗
██╔████╔██║██║   ██║   ██║   ██║██║   ██║██║   ██║    ███████╗█████╗  ██████╔╝██║   ██║█████╗  ██████╔╝
██║╚██╔╝██║██║   ██║   ██║   ██║╚██╗ ██╔╝██║   ██║    ╚════██║██╔══╝  ██╔══██╗╚██╗ ██╔╝██╔══╝  ██╔══██╗
██║ ╚═╝ ██║╚██████╔╝   ██║   ██║ ╚████╔╝ ╚██████╔╝    ███████║███████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║
╚═╝     ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═══╝   ╚═════╝     ╚══════╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝
                                                                                                           
███████╗███╗   ██╗████████╗██████╗ ███████╗    ████████╗██████╗  █████╗ ██████╗ ██╗████████╗██╗ ██████╗ ███╗   ██╗
██╔════╝████╗  ██║╚══██╔══╝██╔══██╗██╔════╝    ╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██║╚══██╔══╝██║██╔═══██╗████╗  ██║
█████╗  ██╔██╗ ██║   ██║   ██████╔╝█████╗         ██║   ██████╔╝███████║██║  ██║██║   ██║   ██║██║   ██║██╔██╗ ██║
██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗██╔══╝         ██║   ██╔══██╗██╔══██║██║  ██║██║   ██║   ██║██║   ██║██║╚██╗██║
███████╗██║ ╚████║   ██║   ██║  ██║███████╗       ██║   ██║  ██║██║  ██║██████╔╝██║   ██║   ██║╚██████╔╝██║ ╚████║
╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚══════╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                                                                                                                      
███████╗████████╗    ███╗   ███╗ ██████╗ ██████╗ ███████╗██████╗ ███╗   ██╗██╗████████╗███████╗
██╔════╝╚══██╔══╝    ████╗ ████║██╔═══██╗██╔══██╗██╔════╝██╔══██╗████╗  ██║██║╚══██╔══╝██╔════╝
█████╗     ██║       ██╔████╔██║██║   ██║██║  ██║█████╗  ██████╔╝██╔██╗ ██║██║   ██║   █████╗  
██╔══╝     ██║       ██║╚██╔╝██║██║   ██║██║  ██║██╔══╝  ██╔══██╗██║╚██╗██║██║   ██║   ██╔══╝  
███████╗   ██║       ██║ ╚═╝ ██║╚██████╔╝██████╔╝███████╗██║  ██║██║ ╚████║██║   ██║   ███████╗
╚══════╝   ╚═╝       ╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝   ╚═╝   ╚══════╝'

# Function to find an available display number
find_available_display() {
    local display
    while true; do
        # Generate random number between 99 and 599
        display=$((RANDOM % 500 + 99))
        # Check if display is already in use
        if ! xdpyinfo -display :${display} >/dev/null 2>&1; then
            echo ${display}
            break
        fi
    done
}

# Function to kill existing processes
cleanup() {
    echo "Cleaning up existing processes..."
    
    # Kill any existing Xvfb processes started by this user
    pkill -u $(id -u) Xvfb
    
    # Kill existing Python processes for your specific scripts
    pkill -f "python webserver/webserver.py"
    pkill -f "python motivo/04_ws_example.py"
    
    # Wait a moment to ensure processes are killed
    sleep 2
}

# Function to handle script termination
handle_exit() {
    echo "Shutting down servers..."
    cleanup
    exit 0
}

# Register the cleanup function for script termination
trap handle_exit SIGINT SIGTERM

# Run cleanup at start
cleanup

# Get an available display number
DISPLAY_NUM=$(find_available_display)
export DISPLAY=:${DISPLAY_NUM}

echo "Starting Xvfb on display :${DISPLAY_NUM}"

# Start Xvfb with the random display number
Xvfb :${DISPLAY_NUM} -screen 0 1024x768x24 > /dev/null 2>&1 &

# Wait for Xvfb to start
sleep 5

# Export the display variable for other processes
export DISPLAY=:${DISPLAY_NUM}

# Start Flask server
python webserver/webserver.py &

# Start WebSocket server
python motivo/main.py