#!/usr/bin/env python3
"""
Sends a single empty CAN FD frame with BRS enabled to ID 0x02 via can0,
and then continuously receives and prints incoming frames using the
python-can library.

Press Ctrl+C to stop the receiver loop.

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
# Timeout for receiving loop - use None to block indefinitely until message
# or a small value (e.g., 0.1) to allow periodic checks for KeyboardInterrupt
# Using None is generally fine for simple listeners.
RECEIVE_TIMEOUT = None # Or e.g., 1.0

def print_message_details(msg):
    """Helper function to print details of a received CAN message."""
    print("-" * 20)
    print(f"  Timestamp: {msg.timestamp:.6f}") # More precision for timestamp
    print(f"  ID: 0x{msg.arbitration_id:03X}")
    print(f"  Is Extended ID: {msg.is_extended_id}")
    print(f"  Is Remote Frame: {msg.is_remote_frame}") # Added check
    print(f"  Is Error Frame: {msg.is_error_frame}")   # Added check
    print(f"  Is FD: {msg.is_fd}")
    if msg.is_fd:
        print(f"  BRS: {msg.bitrate_switch}")
        print(f"  ESI: {msg.error_state_indicator}")
    print(f"  DLC: {msg.dlc}")
    # Format data bytes as hex
    data_hex = ' '.join(f'{b:02X}' for b in msg.data)
    print(f"  Data: [{data_hex}]")
    print("-" * 20)


def main():
    """Creates a CAN FD bus interface, sends a frame, and continuously receives."""
    bus = None  # Initialize bus to None for finally block
    try:
        # --- 1. Create the CAN bus interface ---
        bus = can.interface.Bus(
            channel=INTERFACE,
            bustype='socketcan',
            fd=True,
            bitrate=BITRATE,
            data_bitrate=DATA_BITRATE
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

        # --- 4. Continuously receive and print messages ---
        print(f"\nContinuously receiving CAN messages...")
        print("Press Ctrl+C to stop.")
        while True:
            # bus.recv() blocks until a message is received (or timeout if specified)
            received_message = bus.recv(timeout=RECEIVE_TIMEOUT)

            # If timeout is used, recv() might return None. Skip if no message.
            if received_message:
                print_message_details(received_message)
            # If timeout is None, this 'else' block won't be needed/reached
            # unless recv() is interrupted in some other way.
            # else:
            #    pass # Or print a waiting indicator if using a short timeout

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nReceiver loop stopped by user (Ctrl+C).")
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
