import can

# Create a CAN bus instance (using socketcan for Linux or use 'pcan', 'usb2can', etc.)
bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=500000)

# Create a CAN message
msg = can.Message(arbitration_id=0x123,
                  data=[0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88],
                  is_extended_id=False)
# try:
#     bus.send(msg)
#     print("Message sent on {}".format(bus.channel_info))
# except can.CanError:
#     print("Message NOT sent")

print("Listening for a message...")
message = bus.recv(timeout=10.0)
if message:
    print("Received message:", message)
else:
    print("No message received within timeout")