# import platform
# import random
# import can
# import asyncio
# import websockets

# isMock = False  

# # CAN Bus selection
# def get_can_bus():
#     global isMock
#     if platform.system() == "Linux":  
#         print("Using Hardware CAN")
#         return can.interface.Bus(channel="can0", interface="socketcan", bitrate=1000000)
#     else: 
#         print("Using Mock CAN")
#         isMock = True
#         return can.interface.Bus('test', interface='virtual')

# # Mock CAN message generator
# async def mock_can(bus):
#     while True:
#         try:
#             arbitration_id = random.randint(0x100, 0x1FF)  # Random CAN ID
#             data = bytes([random.randint(0, 255) for _ in range(8)])  # 8 random bytes
#             message = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)
#             bus.send(message)
#             print(f"Sent CAN message: ID={hex(message.arbitration_id)}, Data={message.data}")
#         except can.CanError as e:
#             print(f"CAN send error: {e}")
#         await asyncio.sleep(1)  

# # Future CAN parsing implementation
# def parse_can_message(msg):
#     # Example parsing logic (extend as needed)
#     if msg.arbitration_id == 0x123: 
#         speed = int.from_bytes(msg.data[:2], byteorder="big") / 10.0 
#         return {"speed": speed}
#     return None

# # WebSocket server to send CAN data to Electron
# async def websocket_handler(websocket):
#     print("WebSocket client connected")
#     try:
#         while True:
#             msg = bus.recv(timeout=1.0) 
#             if(msg):
#                 await websocket.send(str(msg.arbitration_id))
#             # if msg:
#             #     parsed_data = parse_can_message(msg)
#             #     if parsed_data:
#             #         await websocket.send(str(msg.arbitration_id)) 
#     except websockets.exceptions.ConnectionClosed:
#         print("WebSocket client disconnected")

# # Main async function
# async def main():
#     global bus
#     bus = get_can_bus()  # Initialize CAN bus
#     print("Starting WebSocket server...")

#     # Start mock CAN task if in mock mode
#     sender_task = None
#     if isMock:
#         sender_task = asyncio.create_task(mock_can(bus))

#     try:
#         # Start WebSocket server
#         async with websockets.serve(websocket_handler, "localhost", 8080):
#             print("WebSocket server running on ws://localhost:8080")
#             await asyncio.Future()  # Keep running until interrupted
#     finally:
#         # Cleanup
#         if sender_task:
#             sender_task.cancel()  # Stop mock CAN messages
#             await sender_task
#         bus.shutdown()  # Shutdown CAN bus properly
#         print("Shutting down CAN bus...")

# if __name__ == "__main__":
#     asyncio.run(main())


import can
import platform
import asyncio
from websockets import serve
from websockets.exceptions import ConnectionClosedOK
import json

# CAN Bus selection
def get_can_bus():  
    bus = None
    
    if platform.system() == "Linux":  
        try:
            bus = can.interface.Bus(interface="socketcan", channel="can0")
        except:
            print("WARNING: hardware not active, falling back to vcan0")
            
        if not bus:
            try:
                bus = can.interface.Bus(interface="socketcan", channel="vcan0")
            except:
                print("WARNING: vcan not active, falling back to virtual python-can")
        
    if not bus:
        print("Using virtual python-can")
        bus = can.interface.Bus('test', interface='virtual')
        
    return bus

def on_message_received(msg):
    print(f"Message received")
    print("")

can_bus = get_can_bus()
async def send_message(websocket):
    try:
        while True:
            msg = can_bus.recv() 
            on_message_received(msg)
            data = {
                "id": msg.arbitration_id,
                "timestamp": msg.timestamp,
                "data": int.from_bytes(msg.data, "big"),
            }
            json_data = json.dumps(data)
            print(json_data)
            message_to_send = data # str(json_data)
            try:
                await websocket.send(message_to_send)
                # print(f"Sent message: {message_to_send}")
                await asyncio.sleep(.000001)  
            except ConnectionClosedError:
                print("Connection closed, unable to send message.")
                break
    except KeyboardInterrupt:
        print("\n")
    
async def handler(websocket):
    print("client connected")
    send_task = asyncio.create_task(send_message(websocket))
    
    try:
        while True:
            try:
                message = await websocket.recv()
            except ConnectionClosedOK:
                print("ConnectionClosedOK")
                break
            print(message)
    except KeyboardInterrupt:
        print("\n")
        
    send_task.cancel() # stop sending task


async def main():
    can_bus = get_can_bus()
    
    try:
        while True:
            async with serve(handler, "", 8001):
                print("bonk")
                await asyncio.get_running_loop().create_future()  # run forever
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    finally:
        can_bus.shutdown()  # Cleanup and close the bus

if __name__ == '__main__':
    asyncio.run(main())
    
