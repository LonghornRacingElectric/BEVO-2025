#!/usr/bin/env python3
"""
Sends a single empty CAN FD frame with BRS enabled to ID 0x02 via can0.

Make sure the 'can0' interface is up and configured for CAN FD
before running this script. For example:
  sudo ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on
"""

import socket
import struct
import sys

# Constants for SocketCAN
CAN_RAW = 1  # Raw CAN protocol
CAN_FD_FRAMES = 5 # Enable CAN FD frames support
PF_CAN = 29 # Protocol Family CAN
SOL_CAN_RAW = 101 # Socket level for CAN_RAW options

# CAN FD Flags
CAN_FD_BRS = 0x02  # Bit Rate Switch enabled

# Network interface name
INTERFACE = "can0"
# CAN ID to send to
CAN_ID = 0x02
# Data Length Code (0 for empty frame)
DLC = 0
# Frame flags (Enable BRS)
FLAGS = CAN_FD_BRS
# Frame data (empty)
DATA = b''

def main():
    """Creates a CAN FD socket, builds and sends the frame."""
    try:
        # --- 1. Create the CAN socket ---
        # Using SOCK_RAW for raw network protocol access
        # PF_CAN specifies the CAN protocol family
        sock = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        print(f"Socket created for {INTERFACE}")

        # --- 2. Enable CAN FD Frame support ---
        # This socket option is necessary to send/receive CAN FD frames
        sock.setsockopt(socket.SOL_CAN_RAW, CAN_FD_FRAMES, 1)
        print("CAN FD support enabled on socket.")

        # --- 3. Bind the socket to the CAN interface ---
        # Associates the socket with the physical 'can0' interface
        sock.bind((INTERFACE,))
        print(f"Socket bound to interface {INTERFACE}")

        # --- 4. Construct the CAN FD frame ---
        # The format is:
        #   can_id (4 bytes unsigned int): Includes EFF/RTR/ERR flags + ID
        #   len    (1 byte unsigned char): Data Length Code (0-64)
        #   flags  (1 byte unsigned char): CAN FD flags (e.g., BRS, ESI)
        #   res0   (1 byte unsigned char): Reserved, must be 0
        #   res1   (1 byte unsigned char): Reserved, must be 0
        #   data   (up to 64 bytes)      : Payload
        # '<IBBxx' is the struct format:
        #   < : Little-endian
        #   I : unsigned int (4 bytes for can_id)
        #   B : unsigned char (1 byte for len)
        #   B : unsigned char (1 byte for flags)
        #   xx: 2 padding bytes (for res0, res1 which are implicitly 0)
        # The data is appended separately after packing the header.

        # Add CAN FD flag to ID if needed (not needed for standard ID 0x02)
        # can_id = CAN_ID | socket.CAN_EFF_FLAG # Example for extended ID
        can_id = CAN_ID # Standard ID

        # Pack the header structure
        can_pkt_header = struct.pack("<IBBxx", can_id, DLC, FLAGS)
        # Combine header and data (data is empty here)
        can_pkt = can_pkt_header + DATA

        # --- 5. Send the CAN FD frame ---
        bytes_sent = sock.send(can_pkt)
        print(f"Sent {bytes_sent} bytes for the CAN FD frame to ID 0x{CAN_ID:03X} with BRS.")

    except OSError as e:
        print(f"Error communicating with CAN interface {INTERFACE}: {e}", file=sys.stderr)
        print("Ensure the interface exists, is up, and configured for CAN FD.", file=sys.stderr)
        print("Example: sudo ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # --- 6. Close the socket ---
        if 'sock' in locals() and sock:
            sock.close()
            print("Socket closed.")

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
