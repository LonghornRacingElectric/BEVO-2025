import random
import can
import asyncio
from websockets import serve
from websockets.exceptions import ConnectionClosedOK
import json
import time

import template_pb2 
import paho.mqtt.client as mqtt

MQTT_BROKER = "192.168.1.109"
MQTT_PORT = 1883
MQTT_TOPIC = "data"

eid = 0

bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=1000000)

def create_sensor_data(id):
    sensor_data = template_pb2.SensorData()
    sensor_data.time = 1234
    # sensor_data.packet_id = id
    

    return sensor_data.SerializeToString()

def publish_message(data):
    
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    serialized_message = create_sensor_data(eid)
    client.publish(MQTT_TOPIC, serialized_message)
    print("Message sent!")
    eid += 1
    client.disconnect()

# async def send_message(websocket):
#     last_tick = time.time()
#     while True:

#         msg = bus.recv(timeout=1.0)  
#         now = time.time()
#         if now - last_tick >= 1.0:
#                 print("sent to server")
#                 publish_message(msg.data[0]/10)
#                 last_tick = now
                
#         data = {
#             "id": msg.arbitration_id,
#             "timestamp": time + 0.0,
#             "data": list(msg.data),
#         }
#         time += 1
#         # print(data)
#         json_data = json.dumps(data)
#         message_to_send = json_data 
#         try:
#             await websocket.send(message_to_send)
#             # print(f"Sent message: {message_to_send}")
#             await asyncio.sleep(.01)
#         except asyncio.exceptions.CancelledError or KeyboardInterrupt:
#             print("Connection closed, unable to send message.")
#             break

async def send_message(websocket):
    last_tick = time.time()
    while True:
        msg = bus.recv(timeout=1.0)  
        data = {
            "id": msg.arbitration_id,
            "timestamp": msg.timestamp,
            "data": list(msg.data),
        }
        now = time.time()
        if now - last_tick >= 1.0:
                print("sent to server")
                publish_message(list(msg.data)[0]/10)
                last_tick = now
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
