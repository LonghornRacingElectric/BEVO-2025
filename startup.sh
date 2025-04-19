name="World"
cd ~/Documents/BEVO-2025/
source ./.venv/bin/activate
python cell_interface/cell_tools.py
sudo ip link set can0 up type can bitrate 1000000
python can_interface/scripts/can_backend.py
mpg123 -q --loop -1 Texas Longhorns Fight Song
