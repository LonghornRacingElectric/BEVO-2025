#!/bin/bash

# Check if can0 interface is already up
if ! ip link show can0 | grep -q "UP"; then
    echo "Setting up CAN interface..."
    sudo ip link set can0 up type can bitrate 1000000
else
    echo "CAN interface can0 is already up"
fi

# Activate virtual environment
. /home/lhre/Documents/BEVO-2025/.venv/bin/activate

# Run Python script with argument
python /home/lhre/Documents/BEVO-2025/celld/celld.py on

mpv --fs --no-terminal ../startup.MP4
