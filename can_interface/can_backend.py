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
    
    # try:
    #     while True:
    #         async with serve(handler, "", 8001):
    #             print("bonk")
    #             await asyncio.get_running_loop().create_future()  # run forever
    # except KeyboardInterrupt:
    #     print("\nProgram interrupted. Exiting...")
    # finally:
    #     can_bus.shutdown()  # Cleanup and close the bus

if __name__ == '__main__':
    asyncio.run(main())
    
