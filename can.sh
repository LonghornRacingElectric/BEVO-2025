cd ~/Documents/BEVO-2025/
python cell_interface/cell_tools.py

echo "Waiting for internet connection..."

# Loop until ping succeeds
while ! ping -c 1 -W 1 google.com &> /dev/null; do
    echo "No internet yet. Retrying in 2 seconds..."
    sleep 2
done

echo "Internet is up!"