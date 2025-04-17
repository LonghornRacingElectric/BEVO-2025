#!/usr/bin/env python3
"""
Sends a single empty CAN FD frame with BRS enabled to ID 0x02 via can0
using the python-can library.

Make sure the 'can0' interface is up and configured for CAN FD
before running this script. For example:
  sudo ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on

Also, ensure the python-can library is installed:
  pip install python-can
"""

import can
import sys
import time

# Network interface name
INTERFACE = "can0"
# CAN ID to send to
CAN_ID = 0x02
# Nominal bitrate (ensure this matches the 'ip link' command)
BITRATE = 500000
# Data bitrate (ensure this matches the 'ip link' command)
DATA_BITRATE = 2000000

def main():
    """Creates a CAN FD bus interface, builds and sends the frame."""
    bus = None  # Initialize bus to None for finally block
    try:
        # --- 1. Create the CAN bus interface ---
        # bustype='socketcan' specifies the backend
        # channel='can0' specifies the interface name
        # fd=True enables CAN FD mode
        # bitrate and data_bitrate should match the interface configuration
        # Note: python-can attempts basic configuration, but pre-configuring
        # the interface with 'ip link' is recommended for reliability.
        bus = can.interface.Bus(
            channel=INTERFACE,
            bustype='socketcan',
            fd=True,
            bitrate=BITRATE,
            data_bitrate=DATA_BITRATE
        )
        print(f"Bus interface created for {INTERFACE} with FD enabled.")
        print(f"  Nominal Bitrate: {BITRATE}")
        print(f"  Data Bitrate: {DATA_BITRATE}")

        # --- 2. Create the CAN FD message ---
        # arbitration_id: The CAN identifier
        # is_fd=True: Marks the message as a CAN FD message
        # bitrate_switch=True: Enables the Bit Rate Switch (BRS)
        # data=[]: Empty payload (DLC=0)
        message = can.Message(
            arbitration_id=CAN_ID,
            is_fd=True,
            bitrate_switch=True,
            data=[]  # Empty data payload
        )
        print(f"Constructed CAN FD message for ID 0x{CAN_ID:03X} with BRS, DLC={message.dlc}")

        # --- 3. Send the CAN FD message ---
        bus.send(message)
        print(f"Sent CAN FD frame to ID 0x{CAN_ID:03X}.")

        # Add a small delay to ensure the message is sent before shutdown
        time.sleep(0.1)

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
        # --- 4. Shutdown the bus interface ---
        if bus:
            bus.shutdown()
            print("Bus interface shut down.")

if __name__ == "__main__":
    main()


# import can

# def main():
#     bus = can.interface.Bus(channel='can0', bustype='socketcan')

#     # Send CAN FD frame with BRS and no data
#     msg = can.Message(
#         arbitration_id=0x02,
#         data=[],
#         is_extended_id=False,
#         is_fd=True,
#         bitrate_switch=True
#     )

#     try:
#         bus.send(msg)
#         print("Sent CAN FD frame successfully.")
#     except can.CanError as e:
#         print(f"CAN send failed: {e}")

# if __name__ == "__main__":
#     main()
