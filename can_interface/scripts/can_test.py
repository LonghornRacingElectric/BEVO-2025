import can

def main():
    bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=1000000)
    try:
        print("Listening for CAN messages... Press Ctrl+C to exit.")
        while True:
            message = bus.recv(timeout=1.0)  
            if message:
                print(f"Received: {message}")
    except KeyboardInterrupt:
        print("\nCtrl+C received. Exiting.")
    finally:
        print("Shutting down CAN bus.")
        bus.shutdown()

if __name__ == "__main__":
    main()