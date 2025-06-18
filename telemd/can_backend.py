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

# Initialize MQTT client with error handling
global mqtt_connected, client
mqtt_connected = False
client = None

try:
    # Use the newer MQTT client API to avoid deprecation warning
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_connected = True
    print(f"Successfully connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
except Exception as e:
    print(f"Warning: Could not connect to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    print(f"MQTT error: {e}")
    print("Continuing with WebSocket functionality only...")
    mqtt_connected = False

import requests

try:
    res = requests.get("https://lhrelectric.org/webtool/handshake/")
    print(res.json()["last_packet"])
    os.environ["p_id"] = str(res.json()["last_packet"])
    
    # Only try to reconnect MQTT if we have a valid packet ID
    if not mqtt_connected and client:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            mqtt_connected = True
            print(f"Successfully connected to MQTT broker after handshake")
        except Exception as e:
            print(f"Still cannot connect to MQTT broker: {e}")
            mqtt_connected = False
except Exception as e:
    print(f"Warning: Could not get handshake data: {e}")
    print("Using default packet ID: 0")


async def process_can_messages():
    """Process CAN messages independently of WebSocket connections"""
    global mqtt_connected, client
    
    bus = can.interface.Bus(bustype="socketcan", channel="can0", bitrate=1000000)
    last_can_time = 0
    
    print("Starting CAN message processing...")
    
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

                    # Always transmit immediately on MQTT if connected
                    if mqtt_connected and client:
                        try:
                            p_id = int(os.getenv("p_id"))
                            proto.publish_msg(
                                mqtt_client=client, can_buffer=[data], packet_id=p_id
                            )
                            os.environ["p_id"] = str(p_id + 1)
                        except Exception as e:
                            print(f"MQTT publish error: {e}")
                            mqtt_connected = False
                            
            except Exception as e:
                print(f"CAN processing error: {e}")
    except KeyboardInterrupt:
        print("Stopping CAN processing.")
    finally:
        bus.shutdown()


async def send_message(websocket):
    """Send CAN messages to WebSocket clients"""
    print("WebSocket client connected, starting message forwarding...")
    try:
        while True:
            # This will be populated with CAN data when available
            await asyncio.sleep(0.1)
    except Exception as e:
        print(f"WebSocket send error: {e}")


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
        # Start CAN processing task
        can_task = asyncio.create_task(process_can_messages())
        
        print("Websocket server on localhost:8001")
        async with serve(handler, "", 8001):
            await asyncio.get_running_loop().create_future()
    except asyncio.exceptions.CancelledError:
        print("\nProgram interrupted. Exiting...")
    finally:
        can_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
