import random
import can
import asyncio
from websockets import serve
from websockets.exceptions import ConnectionClosedOK
import json

bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=1000000)

async def send_message(websocket):
    time = 0
    while True:
        arbitration_id = 0x123
        size = random.randint(1, 8)
        can_data = [random.randint(0, 255)]
        for _ in range(size - 1):
            can_data.append(random.randint(0, 255))
        
        msg = bus.recv(timeout=1.0)  
        data = {
            "id": msg.arbitration_id,
            "timestamp": time + 0.0,
            "data": list(msg.data),
        }
        time += 1
        print(data)
        json_data = json.dumps(data)
        message_to_send = json_data 
        try:
            await websocket.send(message_to_send)
            # print(f"Sent message: {message_to_send}")
            await asyncio.sleep(.01)
        except asyncio.exceptions.CancelledError or KeyboardInterrupt:
            print("Connection closed, unable to send message.")
            break


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

    send_task.cancel()  # stop sending task



async def main():
    try:
        while True:
            print("Websocket server on localhost:8001")
            async with serve(handler, "", 8001):
                await asyncio.get_running_loop().create_future()
    except asyncio.exceptions.CancelledError:
        print("\nProgram interrupted. Exiting...")


if __name__ == "__main__":
    asyncio.run(main())
