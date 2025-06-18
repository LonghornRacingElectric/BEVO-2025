import template_pb2 as pb
import time
import random
from can_map import CAN_MAPPING


def publish_msg(mqtt_client, can_buffer, packet_id, topic="data"):
    sensor_msg = pb.SensorData()
    print(f"[DEBUG] Processing {len(can_buffer)} CAN messages")
    
    for can_msg in can_buffer:
        can_id = can_msg["id"]
        data = can_msg["data"]
        print(f"[DEBUG] Processing CAN 0x{can_id:X} with data {data}")
        
        if can_id not in CAN_MAPPING:
            print(f"[WARN] No mapping found for CAN 0x{can_id:X}")
            continue

        field_path, parser = CAN_MAPPING[can_id]
        print(f"[DEBUG] Found mapping: {field_path}")
        
        try:
            value = parser(data)
            print(f"[DEBUG] Parsed value: {value} (type: {type(value)})")
        except Exception as e:
            print(f"[WARN] Parse failed for CAN 0x{can_id:X}: {e}")
            continue

        # Set the value in the nested protobuf structure
        obj = sensor_msg
        parts = field_path.split('.')
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
        print(f"[DEBUG] Set {field_path} = {value}")
        
        sensor_msg.time = int(time.time() * 1000)
        sensor_msg.packet_id = packet_id

    try:
        payload = sensor_msg.SerializeToString()
        print(f"[DEBUG] Protobuf message size: {len(payload)} bytes")
        print(f"[DEBUG] Protobuf message content: {sensor_msg}")
        
        # Publish to MQTT
        result = mqtt_client.publish(topic, payload)
        print(f"[DEBUG] MQTT publish result: {result}")
        print(f"[DEBUG] MQTT publish return code: {result.rc}")
        print(f"[DEBUG] MQTT publish message ID: {result.mid}")
        
        if result.rc == 0:
            print(f"[MQTT] Successfully published protobuf message ({len(payload)} bytes) to topic '{topic}'")
        else:
            print(f"[ERROR] MQTT publish failed with return code: {result.rc}")
            
    except Exception as e:
        print(f"[ERROR] Failed to publish: {e}")
        print(f"[ERROR] Exception type: {type(e)}")
