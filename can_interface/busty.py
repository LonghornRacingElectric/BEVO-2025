import can

def main():
    bus = can.interface.Bus(channel='can0', bustype='socketcan')

    # Send CAN FD frame with BRS and no data
    msg = can.Message(
        arbitration_id=0x02,
        data=[],
        is_extended_id=False,
        is_fd=True,
        bitrate_switch=True,
        error=False
    )

    try:
        bus.send(msg)
        print("Sent CAN FD frame successfully.")
    except can.CanError as e:
        print(f"CAN send failed: {e}")

if __name__ == "__main__":
    main()
