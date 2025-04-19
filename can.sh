#!/bin/bash

MAX_RETRIES=200
RETRY_DELAY=2
TARGET="google.com"

cd ~/Documents/BEVO-2025/
source ./.venv/bin/activate

cvlc BlankBevo.MP4 --fullscreen --play-and-exit

python cell_interface/cell_tools.py

echo "Waiting for internet (DNS + Ping to $TARGET)..."

for ((i=1; i<=MAX_RETRIES; i++)); do
    if getent hosts "$TARGET" > /dev/null && ping -c 1 -W 1 "$TARGET" > /dev/null; then
        echo "Internet is up!"
        exit 0
    fi
    echo "[$i/$MAX_RETRIES] Still waiting..."
    sleep $RETRY_DELAY
done

echo "Failed to connect after $((MAX_RETRIES * RETRY_DELAY)) seconds."
exit 1