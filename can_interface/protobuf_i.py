import template_pb2 as pb
import time
import random
from can_map import CAN_MAPPING


def publish_msg(mqtt_client, can_buffer, packet_id, topic="data"):
    sensor_msg = pb.SensorData()
    for can_msg in can_buffer:
        can_id = can_msg["id"]
        data = can_msg["data"]
        # if can_id not in CAN_MAPPING:
        #     print(f"[WARN] Parse failed for CAN 0x{can_id:X}: {e}")
        #     continue

        # field_path, parser = CAN_MAPPING[can_id]
        # try:
        #     value = parser(data)
        # except Exception as e:
        #     print(f"[WARN] Parse failed for CAN 0x{can_id:X}: {e}")
        #     continue
        if(can_id == 0x012):
            sensor_msg.dynamics.fl_ride_height = data[6]

        # Set the value in the nested protobuf structure
        obj = sensor_msg
        parts = field_path.split('.')
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
        sensor_msg.time = int(time.time() * 1000)
        sensor_msg.packet_id = packet_id

    try:
        payload = sensor_msg.SerializeToString()
        mqtt_client.publish(topic, payload)
        # print(f"[MQTT] Published {len(payload)} bytes to {topic}")
    except Exception as e:
        print(f"[ERROR] Failed to publish: {e}")
