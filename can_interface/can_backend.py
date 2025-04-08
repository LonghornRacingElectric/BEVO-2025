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
# import os

# os.environ["p_id"] = "0"

# client = mqtt.Client()
# client.connect(MQTT_BROKER, MQTT_PORT, 60)

import requests

# res = requests.get("https://lhrelectric.org/webtool/handshake/")
# print(res.json()["last_packet"])
# os.environ["p_id"] = str(res.json()["last_packet"])
# client = mqtt.Client()
# client.connect(MQTT_BROKER, MQTT_PORT, 60)
bus = can.interface.Bus(bustype="socketcan", channel="can0", bitrate=1000000)


async def send_message(websocket):
    # last_tick = time.time()
    can_buffer = []
    try:
        while True:
            try:
                msg = bus.recv(timeout=1.0)
                if(msg):
                    data = {
                        "id": msg.arbitration_id,
                        "timestamp": msg.timestamp,
                        "data": list(msg.data),
                    }
                    print(data)
                    can_buffer.append(data)

                    # now = time.time()
                    # if now - last_tick >= 003.0:
                    #     p_id = int(os.getenv("p_id"))
                    #     # proto.publish_msg(
                    #     #     mqtt_client=client, can_buffer=can_buffer, packet_id=p_id
                    #     # )
                    #     os.environ["p_id"] = str(p_id + 1)
                    #     # can_buffer.clear()
                    #     last_tick = now
                    
                    json_data = json.dumps(data)
                    message_to_send = json_data
                    try:
                        print("ttied")
                        await websocket.send(message_to_send)
                        # print(f"Sent message: {message_to_send}")
                        await asyncio.sleep(0.01)
                    except (asyncio.CancelledError, KeyboardInterrupt):
                        print("Connection closed, unable to send message.")
                        break
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
