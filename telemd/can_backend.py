import can
import asyncio
from websockets import serve
from websockets.exceptions import ConnectionClosedOK
import json
import time
import protobuf_i as proto
import paho.mqtt.client as mqtt


MQTT_BROKER = "192.168.1.109"
MQTT_PORT = 1883
MQTT_TOPIC = "data"
import os

os.environ["p_id"] = "0"

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

import requests

res = requests.get("https://lhrelectric.org/webtool/handshake/")
print(res.json()["last_packet"])
os.environ["p_id"] = str(res.json()["last_packet"])
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)


async def send_message(websocket):
    last_tick = time.time()
    bus = can.interface.Bus(bustype="socketcan", channel="can0", bitrate=1000000)
    last_can_time = 0
    can_buffer = []
    try:
        while True:
            try:
                msg = bus.recv(timeout=0.01)
                if(msg and (last_can_time - msg.timestamp < 0.1)):
                    last_can_time = msg.timestamp
                    data = {
                        "id": msg.arbitration_id,
                        "timestamp": msg.timestamp,
                        "data": list(msg.data),
                    }
                    
                    # Debug print for all CAN packets
                    print(f"CAN Packet: 0x{msg.arbitration_id:03X} [{len(msg.data)}] {[f'{b:02X}' for b in msg.data]}")
                    
                    # Special debug for 0x6CA packet
                    if msg.arbitration_id == 0x6CA:
                        print(f"*** SHUTDOWN LEG1 PACKET DETECTED: 0x{msg.arbitration_id:03X} [{len(msg.data)}] {[f'{b:02X}' for b in msg.data]} ***")
                    
                    can_buffer.append(data)

                    # Always transmit immediately on MQTT
                    p_id = int(os.getenv("p_id"))
                    proto.publish_msg(
                        mqtt_client=client, can_buffer=[data], packet_id=p_id
                    )
                    os.environ["p_id"] = str(p_id + 1)

                    # Also send to WebSocket
                    message_to_send = json.dumps(data)
                    await websocket.send(message_to_send)
                    await asyncio.sleep(0.00018)
            except Exception as e:
                print(e)
    except KeyboardInterrupt:
        print("Stopping.")
    finally:
        bus.shutdown()


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
