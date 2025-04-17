import can

def main():
    bus = can.interface.Bus(channel='can0', bustype='socketcan')

    msg = can.Message(
        arbitration_id=0x02,
        is_extended_id=False,
        is_fd=True,
        bitrate_switch=True,
        data=[]  # No data
    )

    try:
        bus.send(msg)
        print("CAN FD frame sent successfully.")
    except can.CanError as e:
        print(f"Error sending CAN FD frame: {e}")

if __name__ == "__main__":
    main()
