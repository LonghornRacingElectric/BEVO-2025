#!/usr/bin/env python3
"""
Sends a single empty CAN FD frame with BRS enabled to ID 0x02 via can0,
and then attempts to read one incoming frame using the python-can library.

Make sure the 'can0' interface is up and configured for CAN FD
before running this script. For example:
  sudo ip link set can0 up type can bitrate 250000 dbitrate 1000000 fd on sample-point 0.8 dsample-point 0.8

Also, ensure the python-can library is installed:
  pip install python-can
"""

import can
import sys
import time

# Network interface name
INTERFACE = "can0"
# CAN ID to send to
SEND_CAN_ID = 0x02
# Nominal bitrate (ensure this matches the 'ip link' command)
BITRATE = 250000
# Data bitrate (ensure this matches the 'ip link' command)
DATA_BITRATE = 1000000
# Timeout for receiving a message (in seconds)
RECEIVE_TIMEOUT = 1.0

def main():
    """Creates a CAN FD bus interface, sends a frame, and attempts to receive one."""
    bus = None  # Initialize bus to None for finally block
    try:
        # --- 1. Create the CAN bus interface ---
        # bustype='socketcan' specifies the backend
        # channel='can0' specifies the interface name
        # fd=True enables CAN FD mode
        # bitrate and data_bitrate should match the interface configuration
        bus = can.interface.Bus(
            channel=INTERFACE,
            bustype='socketcan',
            fd=True,
            bitrate=BITRATE,
            data_bitrate=DATA_BITRATE
            # Note: Consider adding receive_own_messages=True if using loopback
            # and wanting to receive the message just sent.
            # receive_own_messages=False # Default
        )
        print(f"Bus interface created for {INTERFACE} with FD enabled.")
        print(f"  Nominal Bitrate: {BITRATE}")
        print(f"  Data Bitrate: {DATA_BITRATE}")

        # --- 2. Create the CAN FD message to send ---
        message_to_send = can.Message(
            arbitration_id=SEND_CAN_ID,
            is_fd=True,
            bitrate_switch=True,
            data=[]  # Empty data payload
        )
        print(f"Constructed CAN FD message to send: ID=0x{SEND_CAN_ID:03X}, BRS=True, DLC={message_to_send.dlc}")

        # --- 3. Send the CAN FD message ---
        bus.send(message_to_send)
        print(f"Sent CAN FD frame to ID 0x{SEND_CAN_ID:03X}.")

        # --- 4. Attempt to receive a message ---
        print(f"\nWaiting for a CAN message (timeout: {RECEIVE_TIMEOUT}s)...")
        # bus.recv blocks until a message is received or timeout occurs
        received_message = bus.recv(timeout=RECEIVE_TIMEOUT)

        if received_message:
            print("Message received:")
            print(f"  Timestamp: {received_message.timestamp}")
            print(f"  ID: 0x{received_message.arbitration_id:03X}")
            print(f"  Is Extended ID: {received_message.is_extended_id}")
            print(f"  Is FD: {received_message.is_fd}")
            if received_message.is_fd:
                print(f"  BRS: {received_message.bitrate_switch}")
                print(f"  ESI: {received_message.error_state_indicator}")
            print(f"  DLC: {received_message.dlc}")
            # Format data bytes as hex
            data_hex = ' '.join(f'{b:02X}' for b in received_message.data)
            print(f"  Data: [{data_hex}]")
        else:
            print(f"No message received within the {RECEIVE_TIMEOUT}s timeout.")

    except can.CanError as e:
        print(f"Error communicating with CAN interface {INTERFACE}: {e}", file=sys.stderr)
        print("Ensure the interface exists, is up, and configured correctly.", file=sys.stderr)
        print(f"Example: sudo ip link set {INTERFACE} up type can bitrate {BITRATE} dbitrate {DATA_BITRATE} fd on", file=sys.stderr)
        print("Also ensure the python-can library is installed (`pip install python-can`).", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # --- 5. Shutdown the bus interface ---
        if bus:
            bus.shutdown()
            print("\nBus interface shut down.")

if __name__ == "__main__":
    main()
