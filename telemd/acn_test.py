import asyncio
import random
import time
import sys
import os
import paho.mqtt.client as mqtt
import can

# Add the telemd directory to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.field_mappings import CAN_MAPPING
from protobuf.interface import publish_msg

MQTT_BROKER = "192.168.1.109"
MQTT_PORT = 1883
MQTT_TOPIC = "angelique"

def make_can_msg(arbitration_id, value, scale=1.0):
    """Creates a CAN message with a scaled value."""
    scaled = int(value * scale)
    data = scaled.to_bytes(4, byteorder="little", signed=False)
    return can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)

async def main():
    """Main function to generate and send ACN data."""
    print("Starting ACN data transmission test...")

    # Set up MQTT client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_connected = False
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        mqtt_connected = True
        print(f"Successfully connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        print(f"Warning: Could not connect to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        print(f"MQTT error: {e}")
        print("Exiting.")
        return None

    # Get the last packet ID from the server
    packet_id = 0
    try:
        import requests
        res = requests.get('https://lhrelectric.org/webtool/handshake/')
        packet_id = int(res.json()['last_packet'])
        print(f"Retrieved initial packet ID: {packet_id}")
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not get handshake data: {e}")
        print("Using default packet ID: 0")

    can_buffer = []
    last_tick = time.time()

    while True:
        # Generate a random CAN message from the CAN_MAPPING
        try:
            can_id = 0x344
            fields = CAN_MAPPING[can_id]
            
            for field_path, parser in fields:
                # This is a hacky way to get the scale from the lambda function.
                # A more robust solution would be to refactor the field_mappings.py
                # to make the scale more accessible.
                scale = 1.0
                lambda_str = str(parser)
                if "scale=" in lambda_str:
                    try:
                        scale = float(lambda_str.split("scale=")[1].split(")")[0])
                    except (ValueError, IndexError):
                        pass

                random_value = random.uniform(0, 10)
                
                msg = make_can_msg(can_id, random_value, scale=scale)
                
                data = {
                    "id": msg.arbitration_id,
                    "time_stamp": msg.timestamp,
                    "data": list(msg.data),
                }
                can_buffer.append(data)
        except Exception as e:
            print(f"Error generating CAN data: {e}")
            continue

        now = time.time()
        if now - last_tick >= 0.003:
            if mqtt_connected:
                publish_msg(
                    mqtt_client=client, can_buffer=can_buffer, packet_id=packet_id, topic=MQTT_TOPIC
                )
                packet_id += 1
                print(f"Sent packet {packet_id} with {len(can_buffer)} CAN messages.")
            can_buffer.clear()
            last_tick = now
        
        await asyncio.sleep(0.01)
    return client


if __name__ == "__main__":
    client = None
    try:
        client = asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    finally:
        if client:
            client.loop_stop()
        print("Script finished.")
