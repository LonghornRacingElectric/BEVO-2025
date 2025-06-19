#!/usr/bin/env python3

import can
import time
import struct
import argparse
import sys
import os

# --- Configuration ---
# Default CAN interface name
DEFAULT_IFACE = 'can0'
# Default CAN IDs (Replace with your target's actual IDs)
# Standard STM32 bootloader often uses 0x7XY, but check your setup
TARGET_REQUEST_ID = 0x111  # Host sends commands to this ID (from AN5405 example)
TARGET_RESPONSE_ID = 0x112  # Target sends responses to this ID (Example, adjust as needed)
# Default target flash start address
DEFAULT_FLASH_ADDR = 0x08000000
# Timeout for waiting for ACK/NACK in seconds
DEFAULT_TIMEOUT = 1.0
# Longer timeout for erase operations
ERASE_TIMEOUT = 30.0
# Max data bytes per FDCAN frame for WRITE command (adjust as needed, <= 60)
# STM32 bootloader might have its own limit (often 256 for standard CAN)
# Check AN2606 for the specific device. Let's use 60 for FDCAN safety.
WRITE_CHUNK_SIZE = 60
# Use FDCAN with Bit Rate Switching (BRS)
USE_BRS = True

# --- Bootloader Commands ---
CMD_SYNC = bytes([0x7F])
CMD_GET_ID = bytes([0x02, 0xFD])  # Command + Checksum
CMD_WRITE_MEM = bytes([0x31, 0xCE])  # Command + Checksum
CMD_ERASE_EXT = bytes([0x44, 0xBB])  # Command + Checksum
CMD_GO = bytes([0x21, 0xDE])  # Command + Checksum

# --- Bootloader Responses ---
RESP_ACK = 0x79
RESP_NACK = 0x1F


# --- Helper Functions ---

def calculate_checksum(data):
    """Calculates the XOR checksum used by the bootloader."""
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum


def address_to_bytes(addr):
    """Converts a 32-bit address to 4 bytes (big-endian)."""
    return struct.pack('>I', addr)


def wait_for_response(bus, expected_id, timeout):
    """Waits for a specific CAN message ID and returns the message or None."""
    start_time = time.monotonic()
    while time.monotonic() - start_time < timeout:
        msg = bus.recv(timeout=0.1)  # Small timeout for non-blocking check
        if msg:
            # print(f"DEBUG: Received: ID={hex(msg.arbitration_id)}, Data={msg.data.hex()}")  # DEBUG
            if msg.arbitration_id == expected_id:
                return msg
        # Add a small delay to prevent busy-waiting if needed
        # time.sleep(0.001)
    return None


def wait_for_ack(bus, timeout=DEFAULT_TIMEOUT):
    """Waits for an ACK (0x79) response from the target."""
    print("Waiting for ACK...", end='', flush=True)
    msg = wait_for_response(bus, TARGET_RESPONSE_ID, timeout)
    if msg and msg.data and msg.data[0] == RESP_ACK:
        print(" OK")
        return True
    elif msg and msg.data and msg.data[0] == RESP_NACK:
        print(" NACK received!")
        return False
    else:
        print(f" Timeout or unexpected response ({msg.data.hex() if msg else 'None'})")
        return False


def send_can_message(bus, arbitration_id, data):
    """Sends an FDCAN message."""
    message = can.Message(
        arbitration_id=arbitration_id,
        data=data,
        is_extended_id=False,  # Standard IDs usually used
        is_fd=True,  # Enable FDCAN frame format
        bitrate_switch=USE_BRS,  # Use BRS as per AN5405
        # error_state_indicator=False # Usually default is fine
    )
    try:
        # print(f"DEBUG: Sending: ID={hex(message.arbitration_id)}, Data={message.data.hex()}")  # DEBUG
        bus.send(message)
        # Small delay might be needed between commands for some targets
        time.sleep(0.01)
    except can.CanError as e:
        print(f"\nError sending CAN message: {e}")
        return False
    return True


# --- Main Flashing Logic ---

def flash_stm32_fdcan(interface, firmware_path, start_address, target_id, response_id, bitrates):
    """Performs the flashing sequence."""

    print(f"--- STM32 FDCAN Flasher ---")
    print(f"Interface: {interface}")
    print(f"Firmware: {firmware_path}")
    print(f"Target Address: {hex(start_address)}")
    print(f"Target Request ID: {hex(target_id)}")
    print(f"Target Response ID: {hex(response_id)}")
    print(f"Bitrates (nominal, data): {bitrates}")
    print(f"Using BRS: {USE_BRS}")

    # --- 1. Configure SocketCAN Interface (Manual Step Recommended) ---
    # IMPORTANT: This script assumes the interface is already configured and up.
    # You typically need root privileges to do this. Example commands:
    # sudo ip link set {interface} down
    # sudo ip link set {interface} type can bitrate {bitrates[0]} dbitrate {bitrates[1]} fd on
    # sudo ip link set {interface} up
    # Verify the interface configuration before running the script.
    print(f"\nACTION: Ensure CAN interface '{interface}' is configured and up:")
    print(
        f"  sudo ip link set {interface} type can bitrate {bitrates[0]} dbitrate {bitrates[1]} fd on")
    print(f"  sudo ip link set {interface} up")
    input("Press Enter when the interface is ready...")

    # --- 2. Initialize CAN Bus ---
    try:
        bus = can.interface.Bus(channel=interface, bustype='socketcan',
                                fd=True)  # Use fd=True
        print(f"Successfully opened CAN bus on {interface}")
    except (OSError, can.CanError) as e:
        print(f"Error initializing CAN bus: {e}")
        print(
            "Ensure the interface exists, is configured correctly (FDCAN), and you have permissions.")
        sys.exit(1)

    try:
        # --- 3. Synchronize with Bootloader ---
        print("\nAttempting synchronization...")
        sync_attempts = 5
        synced = False
        for _ in range(sync_attempts):
            if not send_can_message(bus, target_id, CMD_SYNC):
                continue  # Try again if send fails

            # Wait for ACK or NACK after sending sync
            msg = wait_for_response(bus, response_id, DEFAULT_TIMEOUT)
            if msg and msg.data and msg.data[0] == RESP_ACK:
                print("Sync ACK received!")
                synced = True
                break
            elif msg and msg.data and msg.data[0] == RESP_NACK:
                print("Sync NACK received, retrying...")
                time.sleep(0.2)
            else:
                print("Sync timeout/unexpected, retrying...")
                time.sleep(0.2)

        if not synced:
            print("Failed to synchronize with bootloader after multiple attempts.")
            bus.shutdown()
            sys.exit(1)

        # --- 4. Get Bootloader Version and Chip ID ---
        print("\nGetting Bootloader Info...")
        if send_can_message(bus, target_id, CMD_GET_ID) and wait_for_ack(bus):
            resp_id = wait_for_response(bus, response_id, DEFAULT_TIMEOUT)
            if resp_id:
                # First byte is len(N-1), next N bytes are PID, last byte is ACK
                if len(resp_id.data) >= 3 and resp_id.data[-1] == RESP_ACK:
                    pid_len = resp_id.data[0] + 1
                    pid = resp_id.data[1:1 + pid_len].hex().upper()
                    print(f"Chip ID (PID): 0x{pid}")
                else:
                    print(
                        f"GET_ID response format unexpected: {resp_id.data.hex()}")
        else:
            print("Failed to execute GET_ID command.")
            # Decide if this is critical

        # --- 5. Erase Flash Memory (Using Extended Erase) ---
        # Extended Erase (0x44) is needed for H7 and many modern MCUs
        # Global Erase Code: 0xFFFF
        print("\nSending Extended Erase (Full Chip)...")
        erase_payload = bytes([0xFF, 0xFF])  # Special code for full erase
        checksum = calculate_checksum(erase_payload)
        full_erase_cmd = CMD_ERASE_EXT + erase_payload + bytes([checksum])  # Include Checksum

        if send_can_message(bus, target_id, full_erase_cmd) and wait_for_ack(bus, ERASE_TIMEOUT):
            print("Flash erase command acknowledged. Erasing can take time...")
            # The ACK here just confirms the command was received.
            # Some bootloaders might send another ACK after erase is *done*.
            # We rely on the long timeout for the initial ACK.
            print("Erase likely successful (command accepted).")
        else:
            print("Failed to initiate flash erase.")
            bus.shutdown()
            sys.exit(1)

        # --- 6. Write Firmware ---
        print("\nWriting firmware...")
        try:
            with open(firmware_path, 'rb') as f:
                firmware_data = f.read()
        except IOError as e:
            print(f"Error opening firmware file {firmware_path}: {e}")
            bus.shutdown()
            sys.exit(1)

        current_address = start_address
        total_bytes = len(firmware_data)
        bytes_written = 0

        while bytes_written < total_bytes:
            chunk = firmware_data[bytes_written:bytes_written + WRITE_CHUNK_SIZE]
            chunk_len = len(chunk)
            if chunk_len == 0:
                break  # Should not happen if loop condition is correct

            print(f"Writing {chunk_len} bytes to {hex(current_address)} ({bytes_written}/{total_bytes})")

            # a) Send WRITE MEMORY command + Address + Length
            addr_bytes = address_to_bytes(current_address)
            # Calculate checksum of address
            addr_checksum = calculate_checksum(addr_bytes)
            # N-1 for length
            length_bytes = bytes([chunk_len - 1])
            # Combine command, address, address checksum, and length.
            write_command_frame = CMD_WRITE_MEM + addr_bytes + bytes([addr_checksum]) + length_bytes

            if not (send_can_message(bus, target_id, write_command_frame) and wait_for_ack(bus)):
                print(f"Error sending WRITE command for address {hex(current_address)}")
                bus.shutdown()
                sys.exit(1)

            # b) Send Data with Checksum.
            data_checksum = calculate_checksum(chunk)
            data_payload = chunk + bytes([data_checksum])

            # Send the data chunk
            if not (send_can_message(bus, target_id, data_payload) and wait_for_ack(bus)):
                print(f"Error writing data chunk at address {hex(current_address)}")
                bus.shutdown()
                sys.exit(1)

            bytes_written += chunk_len
            current_address += chunk_len

        print("\nFirmware writing apparently complete.")

        # --- 7. Jump to Application ---
        print(f"\nAttempting to jump to application at {hex(start_address)}...")
        # a) Send GO command
        if not (send_can_message(bus, target_id, CMD_GO) and wait_for_ack(bus)):
            print("Failed to send GO command.")
            # Don't exit, flashing might still be okay, just didn't jump
        else:
            # b) Send Address + Address Checksum
            addr_bytes = address_to_bytes(start_address)
            addr_checksum = calculate_checksum(addr_bytes)
            addr_payload = addr_bytes + bytes([addr_checksum])
            # The target might jump immediately after receiving address, ACK might not come
            print("Sending jump address...")
            send_can_message(bus, target_id, addr_payload)
            # Optional: Wait briefly for a potential final ACK, but don't rely on it
            time.sleep(0.2)
            print("GO command sent. Target should be running the application now.")
            print("NOTE: An ACK for the GO address is often NOT sent as the MCU jumps immediately.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        # --- 8. Clean up ---
        if 'bus' in locals() and bus:
            print("Shutting down CAN bus.")
            bus.shutdown()

    print("\n--- Flashing process finished ---")


# --- Command Line Argument Parsing ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Flash STM32H7 via FDCAN Bootloader using SocketCAN.")
    parser.add_argument("firmware", help="Path to the firmware binary (.bin) file.")
    parser.add_argument("-i", "--interface", default=DEFAULT_IFACE,
                        help=f"SocketCAN interface name (default: {DEFAULT_IFACE})")
    parser.add_argument("-a", "--address", type=lambda x: int(x, 0), default=DEFAULT_FLASH_ADDR,
                        help=f"Target flash start address (hex or dec, default: {hex(DEFAULT_FLASH_ADDR)})")
    parser.add_argument("-t", "--target-id", type=lambda x: int(x, 0), default=TARGET_REQUEST_ID,
                        help=f"CAN ID for Host->Target communication (hex or dec, default: {hex(TARGET_REQUEST_ID)})")
    parser.add_argument("-r", "--response-id", type=lambda x: int(x, 0), default=TARGET_RESPONSE_ID,
                        help=f"CAN ID for Target->Host communication (hex or dec, default: {hex(TARGET_RESPONSE_ID)})")
    parser.add_argument("-b", "--bitrate", type=int, default=500000,
                        help="Nominal CAN bitrate (e.g., 500000)")
    parser.add_argument("-d", "--dbitrate", type=int, default=2000000,
                        help="Data phase CAN bitrate for FDCAN (e.g., 2000000)")

    args = parser.parse_args()

    if not os.path.exists(args.firmware):
        print(f"Error: Firmware file not found: {args.firmware}")
        sys.exit(1)

    flash_stm32_fdcan(
        interface=args.interface,
        firmware_path=args.firmware,
        start_address=args.address,
        target_id=args.target_id,
        response_id=args.response_id,
        bitrates=(args.bitrate, args.dbitrate)
    )

