import json
from pathlib import Path
import template_pb2 as pb
import time
import random
from can_map import CAN_MAPPING

packet_definitions = json.loads(
    Path("../../longhorn-lib-2025/scripts/can_packets.json").read_text()
)
packet_map = {entry["packet_id"]: entry for entry in packet_definitions}


def get_attrs(can_id):
    attrs = []
    packet_def = packet_map.get(can_id)
    for byte_def in packet_def.get("bytes", []):
        # print(byte_def["name"], byte_def["index"])
        # print(byte_def["protobuf"])
        if "bitfield_encoding" in byte_def:
            for field in byte_def["bitfield_encoding"]:
                attrs.append(
                    {
                        "name": byte_def["name"],
                        "start_byte": byte_def["start_byte"],
                        "protobuf_attr": (
                            field["protobuf_field"]
                            if "protobuf_field" in field
                            else None
                        ),
                        "conv_type": "bitfield",
                        "bit_index": field["bit_index"],
                        "proto_type": "bool",
                    }
                )
        else:
            protob = byte_def["protobuf"] if "protobuf" in byte_def else None
            attrs.append(
                {
                    "name": byte_def["name"],
                    "start_byte": byte_def["start_byte"],
                    "protobuf_attr": protob["field"] if protob else None,
                    "repeated_field_index": (
                        protob["field_index"] if (protob and protob["field"]) else None
                    ),
                    "size": int(byte_def["length"]),
                    "conv_type": byte_def["conv_type"],
                    "proto_type": protob["type"] if protob else None,
                    "precision": byte_def["precision"],
                }
            )
    return attrs


def proto_typing(proto_type, val):
    if proto_type == "float":
        return float(val)
    if proto_type == "int32":
        return int(val)
    if proto_type == "bool":
        return bool(val)


def get_proto_attrs(data):
    print(data)
    proto_attrs = get_attrs(data["id"])
    ret = []
    for attr in proto_attrs:
        # print(attr)
        can_field_data = None

        if attr["conv_type"] == "bitfield":
            can_field_data = bool(
                data["data"][attr["start_byte"]] & (0x1 << attr["bit_index"])
            )
        elif attr["conv_type"] == "uint8":
            can_field_data = attr["precision"] * int.from_bytes(
                data["data"][attr["start_byte"]], signed=False
            )
        elif attr["conv_type"] == "uint16":
            can_field_data = attr["precision"] * int.from_bytes(
                data["data"][attr["start_byte"] : (attr["start_byte"] + 2)],
                byteorder="little",
                signed=False,
            )
        elif attr["conv_type"] == "int8":
            can_field_data = attr["precision"] * int.from_bytes(
                data["data"][attr["start_byte"]], signed=True
            )
        elif attr["conv_type"] == "int16":
            can_field_data = attr["precision"] * int.from_bytes(
                data["data"][attr["start_byte"] : (attr["start_byte"] + 2)],
                byteorder="little",
                signed=True,
            )
            # print(attr["name"], attr["protobuf_attr"], can_field_data)
        if attr["protobuf_attr"]:
            to_send = attr["proto_type"]
            if(attr["repeated_field_index"]):
                to_send += f"\[{attr["repeated_field_index"]}\]"
            ret.append(
                (
                    attr["protobuf_attr"],
                    proto_typing(to_send, can_field_data),
                )
            )
    return ret
    # print(ret)


def publish_msg(mqtt_client, can_buffer, packet_id, topic="data"):
    sensor_msg = pb.SensorData()
    # print(can_buffer)
    # Required: time and id
    sensor_msg.time = int(time.time() * 1000)
    sensor_msg.packet_id = packet_id
    try:
        for can_msg in can_buffer:
            # print(can_msg)
            for attr in get_proto_attrs(can_msg):
                print(attr)
                setattr(sensor_msg.dynamics, attr[0], attr[1])
                # print(sensor_msg.fr_strain_gauge_v)
    except Exception as e:
        print(e)

    try:
        payload = sensor_msg.SerializeToString()
        mqtt_client.publish(topic, payload)
        print(sensor_msg)
        print(f"[MQTT] Published {len(payload)} bytes to {topic}")
    except Exception as e:
        print(f"[ERROR] Failed to publish: {e}")
