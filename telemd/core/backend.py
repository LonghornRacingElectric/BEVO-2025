import asyncio
import json
import os
import time
from websockets import serve
from websockets.exceptions import ConnectionClosedOK

# Modular components
from interfaces.interface import CANInterface
from networking.client import MQTTManager, TelemetryCache
from data_logging.logger import CSVTimeSeriesLogger, LatestValuesCache
from core.field_mappings import CAN_MAPPING

# Configuration
MQTT_PUBLISH_RATE = 0.1  # Hz
MQTT_PUBLISH_INTERVAL = 1.0 / MQTT_PUBLISH_RATE

os.environ["p_id"] = "0"


async def process_can_messages(latest_values):
    """Process CAN messages and update caches."""
    can_interface = CANInterface()
    mqtt_manager = MQTTManager()
    telemetry_cache = TelemetryCache(mqtt_manager, MQTT_PUBLISH_INTERVAL)
    time_series_logger = CSVTimeSeriesLogger()

    can_interface.initialize()
    mqtt_manager.initialize()
    mqtt_manager.get_packet_id()

    print(f"[CAN] Listening with MQTT rate {MQTT_PUBLISH_RATE} Hz")

    try:
        while True:
            msg = can_interface.recv(timeout=0.01)
            now = time.time()

            if msg:
                can_id = msg.arbitration_id
                if can_id in CAN_MAPPING:
                    mapping = CAN_MAPPING[can_id]
                    if isinstance(mapping, tuple):
                        mapping = [mapping]

                    for field_name, converter in mapping:
                        try:
                            value = converter(msg.data)
                            latest_values.update_value(field_name, value)
                            telemetry_cache.update_value(can_id, field_name, value)
                            time_series_logger.log_value(field_name, value, now)
                        except Exception as e:
                            print(f"[Error] {field_name}: {e}")
                else:
                    print(f"[CAN] Unknown ID: 0x{can_id:03X}")

            # Periodic MQTT publish
            if telemetry_cache.should_publish(now):
                telemetry_cache.publish_cached_data(now)

    except Exception as e:
        print(f"[CAN Loop Error] {e}")
    finally:
        print("[CAN] Shutting down...")
        time_series_logger.shutdown()
        can_interface.shutdown()
        mqtt_manager.shutdown()


async def send_message(websocket, latest_values):
    """Send latest telemetry values over WebSocket at ~30Hz."""
    print("[WebSocket] Client connected")
    try:
        while True:
            data = latest_values.get_latest_values()
            if data:
                message = {
                    "timestamp": time.time(),
                    "type": "telemetry_update",
                    "data": data,
                }
                await websocket.send(json.dumps(message))
            await asyncio.sleep(1 / 30.0)  # 30Hz
    except Exception as e:
        print(f"[WebSocket Send Error] {e}")


async def websocket_handler(websocket, latest_values):
    send_task = asyncio.create_task(send_message(websocket, latest_values))
    try:
        while True:
            try:
                message = await websocket.recv()
                print(f"[WebSocket] Received: {message}")
            except ConnectionClosedOK:
                print("[WebSocket] Client disconnected")
                break
    finally:
        send_task.cancel()


async def main():
    latest_values = LatestValuesCache()

    # Start CAN processing
    can_task = asyncio.create_task(process_can_messages(latest_values))

    # Start WebSocket server with closure over `latest_values`
    async def ws_handler(ws):
        await websocket_handler(ws, latest_values)

    print("[Main] WebSocket server on ws://localhost:8001")
    async with serve(ws_handler, "", 8001):
        try:
            await asyncio.Future()  # run forever
        except asyncio.CancelledError:
            print("[Main] Shutdown requested")

    can_task.cancel()
    await can_task


if __name__ == "__main__":
    asyncio.run(main())
