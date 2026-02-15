source venv/bin/activate
python /home/lhre/Documents/BEVO-2025/celld/celld.py on
sudo ip link set can0 up type can bitrate 1000000
sudo openvpn --config etc/openvpn/client/client.ovpn