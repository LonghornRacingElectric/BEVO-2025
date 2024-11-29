import platform
import can
import asyncio
import websockets

# CAN Bus selection
def get_can_bus():
    if platform.system() == "Linux":  
        print("Using Hardware CAN")
        return can.interface.Bus(channel="can0", interface="socketcan", bitrate=1000000)
    else: 
        print("Using Mock CAN")
        return can.interface.Bus('test', interface='virtual')

#future CAN parsing implementation
def parse_can_message(msg):
    # if msg.arbitration_id == 0x123: 
    #     speed = int.from_bytes(msg.data[:2], byteorder="big") / 10.0 
    #     return {"speed": speed}
    return None

# WebSocket server to send CAN data to Electron
async def websocket_handler(websocket, path):
    print("WebSocket client connected")
    while True:
        try:
            msg = bus.recv(timeout=1.0) 
            if msg:
                parsed_data = parse_can_message(msg)
                if parsed_data:
                    await websocket.send(str(parsed_data)) 
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket client disconnected")
            break


if __name__ == "__main__":
    bus = get_can_bus()
    
    print("Starting WebSocket server...")
    websocket_server = websockets.serve(websocket_handler, "localhost", 8765)
    asyncio.get_event_loop().run_until_complete(websocket_server)
    asyncio.get_event_loop().run_forever()

    bus.shutdown()
    
    
async def main():
    print("Starting WebSocket server...")
    async with websockets.serve(websocket_handler, "localhost", 8765):
        await asyncio.Future() 

if __name__ == "__main__":
    bus = get_can_bus()
    asyncio.run(main())
    bus.shutdown()

