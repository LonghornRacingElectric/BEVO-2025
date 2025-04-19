import random
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


def make_can_msg(arbitration_id, value, scale=1.0):
    scaled = int(value * scale)
    data = scaled.to_bytes(8, byteorder="little", signed=False)
    return can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)


test_can_messages = [
    # make_can_msg(1286,  [65, 0, 182, 255, 191, 255], scale=100.0),  # dynamics.flw_speed = 40.0
    # make_can_msg(1031, 38.0, scale=100.0),  # dynamics.frw_speed = 38.0
    # make_can_msg(1032, 39.0, scale=100.0),  # dynamics.blw_speed = 39.0
    # make_can_msg(1033, 39.5, scale=100.0),  # dynamics.brw_speed = 39.5
    # make_can_msg(1280, 12.5, scale=100.0),  # dynamics.fl_ride_height = 12.5
    # make_can_msg(1281, 13.0, scale=100.0),  # dynamics.fr_ride_height = 13.0
    # make_can_msg(0x11B, 2.5, scale=100.0),  # dynamics.fl_strain_gauge_v = 2.5
    # make_can_msg(0x11C, 2.45, scale=100.0),  # dynamics.fr_strain_gauge_v = 2.45
    # make_can_msg(0x127, 55.0, scale=100.0),  # dynamics.dash_speed = 55.0
]


async def send_message(websocket):
    last_tick = time.time()
    can_buffer = []
    test_i = 0
    try:
        while True:

            if test_i >= len(test_can_messages):
                test_i = 0

            msg = test_can_messages[test_i]
            # data = {
            #     "id": msg.arbitration_id,
            #     "time_stamp": msg.timestamp,
            #     "data": list(msg.data),
            # }
            data = {
                "id" : 1286,
                'data' : bytes([65, 0, 182, 255, 191, 255])
            }
            can_buffer.append(data)

            now = time.time()
            if now - last_tick >= 0.003:
                print("sending to server")
                p_id = int(os.getenv("p_id"))
                proto.publish_msg(
                    mqtt_client=client, can_buffer=can_buffer, packet_id=p_id
                )
                os.environ["p_id"] = str(p_id + 1)
                can_buffer.clear()
                last_tick = now

            # print(data)
            json_data = json.dumps(data)
            message_to_send = json_data

            test_i += 1

            try:
                await websocket.send(message_to_send)
                # print(f"Sent message: {message_to_send}")
                await asyncio.sleep(0.01)
            except asyncio.exceptions.CancelledError or KeyboardInterrupt:
                print("Connection closed, unable to send message.")
                break
    except Exception as e:
        print(e)


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
