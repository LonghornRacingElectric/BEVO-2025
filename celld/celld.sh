#!/bin/bash
sudo ip link set can0 up type can bitrate 1000000

# Activate virtual environment
. /home/lhre/Documents/BEVO-2025/.venv/bin/activate

# Run Python script with argument
python /home/lhre/Documents/BEVO-2025/celld/celld.py on
