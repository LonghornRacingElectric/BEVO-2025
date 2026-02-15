#!/bin/bash
# Telemetry System Startup Script
# This script sets up the environment and starts the telemetry system

echo "Starting BEVO Telemetry System..."

# Set working directory
cd /home/lhre/Documents/BEVO-2025

# Turn on the cellular module
echo "Turning on cellular module..."
/home/lhre/Documents/BEVO-2025/.venv/bin/python celld/celld.py on

sleep 5 # Wait for cellular module to initialize

# Set up CAN interface
echo "Setting up CAN interface..."
ip link set can0 up type can bitrate 1000000

# Start OpenVPN (run in background)
echo "Starting VPN connection..."
openvpn --config /etc/openvpn/client/client.ovpn --daemon

# Wait a moment for VPN to establish 
sleep 5

# Start the telemetry system
echo "Starting telemetry system..."
/home/lhre/Documents/BEVO-2025/.venv/bin/python telemd/main.py

echo "Telemetry system stopped."