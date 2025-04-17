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
        
        if can_id == 0x402:
            sensor_msg.dynamics.fl_unsprung_accel[0] = int.from_bytes(data[0:2], "little", signed=True) * 0.001
            sensor_msg.dynamics.fl_unsprung_accel[1] = int.from_bytes(data[2:4], "little", signed=True) * 0.001
            sensor_msg.dynamics.fl_unsprung_accel[2] = int.from_bytes(data[4:6], "little", signed=True) * 0.001
            print("Parsed 0x402 data:", sensor_msg.dynamics.fl_unsprung_accel[0], sensor_msg.dynamics.fl_unsprung_accel[1], sensor_msg.dynamics.fl_unsprung_accel[2])

        if can_id == 0x403:
            sensor_msg.dynamics.fr_unsprung_accel[0] = int.from_bytes(data[0:2], "little", signed=True) * 0.001
            sensor_msg.dynamics.fr_unsprung_accel[1] = int.from_bytes(data[2:4], "little", signed=True) * 0.001
            sensor_msg.dynamics.fr_unsprung_accel[2] = int.from_bytes(data[4:6], "little", signed=True) * 0.001
            print("Parsed 0x403 data:", sensor_msg.dynamics.fr_unsprung_accel[0], sensor_msg.dynamics.fr_unsprung_accel[1], sensor_msg.dynamics.fr_unsprung_accel[2])

        if can_id == 0x404:
            sensor_msg.dynamics.bl_unsprung_accel[0] = int.from_bytes(data[0:2], "little", signed=True) * 0.001
            sensor_msg.dynamics.bl_unsprung_accel[1] = int.from_bytes(data[2:4], "little", signed=True) * 0.001
            sensor_msg.dynamics.bl_unsprung_accel[2] = int.from_bytes(data[4:6], "little", signed=True) * 0.001
            print("Parsed 0x404 data:", sensor_msg.dynamics.bl_unsprung_accel[0], sensor_msg.dynamics.bl_unsprung_accel[1], sensor_msg.dynamics.bl_unsprung_accel[2])

        if can_id == 0x405:
            sensor_msg.dynamics.br_unsprung_accel[0] = int.from_bytes(data[0:2], "little", signed=True) * 0.001
            sensor_msg.dynamics.br_unsprung_accel[1] = int.from_bytes(data[2:4], "little", signed=True) * 0.001
            sensor_msg.dynamics.br_unsprung_accel[2] = int.from_bytes(data[4:6], "little", signed=True) * 0.001
            print("Parsed 0x405 data:", sensor_msg.dynamics.br_unsprung_accel[0], sensor_msg.dynamics.br_unsprung_accel[1], sensor_msg.dynamics.br_unsprung_accel[2])

        if can_id == 0x500:
            sensor_msg.dynamics.fl_sprung_accel[0] = int.from_bytes(data[0:2], "little", signed=True) * 0.001
            sensor_msg.dynamics.fl_sprung_accel[1] = int.from_bytes(data[2:4], "little", signed=True) * 0.001
            sensor_msg.dynamics.fl_sprung_accel[2] = int.from_bytes(data[4:6], "little", signed=True) * 0.001
            sensor_msg.dynamics.fl_ride_height = int.from_bytes(data[6:8], "little", signed=False) * 0.002
            print("Parsed 0x500 data:", sensor_msg.dynamics.fl_sprung_accel, sensor_msg.dynamics.fl_ride_height)

        if can_id == 0x501:
            sensor_msg.dynamics.fr_sprung_accel[0] = int.from_bytes(data[0:2], "little", signed=True) * 0.001
            sensor_msg.dynamics.fr_sprung_accel[1] = int.from_bytes(data[2:4], "little", signed=True) * 0.001
            sensor_msg.dynamics.fr_sprung_accel[2] = int.from_bytes(data[4:6], "little", signed=True) * 0.001
            sensor_msg.dynamics.fr_ride_height = int.from_bytes(data[6:8], "little", signed=False) * 0.002
            print("Parsed 0x501 data:", sensor_msg.dynamics.fr_sprung_accel, sensor_msg.dynamics.fr_ride_height)

        if can_id == 0x502:
            sensor_msg.dynamics.bl_sprung_accel[0] = int.from_bytes(data[0:2], "little", signed=True) * 0.001
            sensor_msg.dynamics.bl_sprung_accel[1] = int.from_bytes(data[2:4], "little", signed=True) * 0.001
            sensor_msg.dynamics.bl_sprung_accel[2] = int.from_bytes(data[4:6], "little", signed=True) * 0.001
            sensor_msg.dynamics.bl_ride_height = int.from_bytes(data[6:8], "little", signed=False) * 0.002
            print("Parsed 0x502 data:", sensor_msg.dynamics.bl_sprung_accel, sensor_msg.dynamics.bl_ride_height)

        if can_id == 0x503:
            sensor_msg.dynamics.br_sprung_accel[0] = int.from_bytes(data[0:2], "little", signed=True) * 0.001
            sensor_msg.dynamics.br_sprung_accel[1] = int.from_bytes(data[2:4], "little", signed=True) * 0.001
            sensor_msg.dynamics.br_sprung_accel[2] = int.from_bytes(data[4:6], "little", signed=True) * 0.001
            sensor_msg.dynamics.br_ride_height = int.from_bytes(data[6:8], "little", signed=False) * 0.002
            print("Parsed 0x503 data:", sensor_msg.dynamics.br_sprung_accel, sensor_msg.dynamics.br_ride_height)

        if can_id == 0x504:
            sensor_msg.dynamics.fl_sprung_ang_rate[0] = int.from_bytes(data[0:2], "little", signed=True) * 0.03
            sensor_msg.dynamics.fl_sprung_ang_rate[1] = int.from_bytes(data[2:4], "little", signed=True) * 0.03
            sensor_msg.dynamics.fl_sprung_ang_rate[2] = int.from_bytes(data[4:6], "little", signed=True) * 0.03
            print("Parsed 0x504 data:", sensor_msg.dynamics.fl_sprung_ang_rate)

        if can_id == 0x505:
            sensor_msg.dynamics.fr_sprung_ang_rate[0] = int.from_bytes(data[0:2], "little", signed=True) * 0.03
            sensor_msg.dynamics.fr_sprung_ang_rate[1] = int.from_bytes(data[2:4], "little", signed=True) * 0.03
            sensor_msg.dynamics.fr_sprung_ang_rate[2] = int.from_bytes(data[4:6], "little", signed=True) * 0.03
            print("Parsed 0x505 data:", sensor_msg.dynamics.fr_sprung_ang_rate)

        if can_id == 0x506:
            sensor_msg.dynamics.bl_sprung_ang_rate[0] = int.from_bytes(data[0:2], "little", signed=True) * 0.03
            sensor_msg.dynamics.bl_sprung_ang_rate[1] = int.from_bytes(data[2:4], "little", signed=True) * 0.03
            sensor_msg.dynamics.bl_sprung_ang_rate[2] = int.from_bytes(data[4:6], "little", signed=True) * 0.03
            print("Parsed 0x506 data:", sensor_msg.dynamics.bl_sprung_ang_rate)

        if can_id == 0x507:
            sensor_msg.dynamics.br_sprung_ang_rate[0] = int.from_bytes(data[0:2], "little", signed=True) * 0.03
            sensor_msg.dynamics.br_sprung_ang_rate[1] = int.from_bytes(data[2:4], "little", signed=True) * 0.03
            sensor_msg.dynamics.br_sprung_ang_rate[2] = int.from_bytes(data[4:6], "little", signed=True) * 0.03
            print("Parsed 0x507 data:", sensor_msg.dynamics.br_sprung_ang_rate)
        # Set the value in the nested protobuf structure
        # obj = sensor_msg
        # parts = field_path.split('.')
        # for part in parts[:-1]:
        #     obj = getattr(obj, part)
        # setattr(obj, parts[-1], value)
        sensor_msg.time = int(time.time() * 1000)
        sensor_msg.packet_id = packet_id

    try:
        payload = sensor_msg.SerializeToString()
        mqtt_client.publish(topic, payload)
        # print(f"[MQTT] Published {len(payload)} bytes to {topic}")
    except Exception as e:
        print(f"[ERROR] Failed to publish: {e}")
