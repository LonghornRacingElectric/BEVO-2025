source venv/bin/activate
python celld/celld.py on
sudo ip link set can0 up type can bitrate 1000000
sudo openvpn --config etc/openvpn/client.ovpn
python telemd/main.py