import asyncio
from websockets import serve
from websockets.exceptions import ConnectionClosedOK
import time
import os
import json
import statistics
from typing import Optional
import requests

# Import our modular components
from interfaces.interface import CANInterface
from networking.client import MQTTManager, TelemetryCache
from data_logging.logger import CSVTimeSeriesLogger, LatestValuesCache
from core.field_mappings import CAN_MAPPING, get_protobuf_field_and_index, CellDataAggregator

# Configuration
MQTT_PUBLISH_RATE = 10  # Hz
MQTT_PUBLISH_INTERVAL = 1.0 / MQTT_PUBLISH_RATE  # ~100ms

async def process_can_messages(latest_values_cache: Optional[LatestValuesCache] = None):
    """Process CAN messages independently of WebSocket connections"""
    # Initialize components
    can_interface = CANInterface()
    mqtt_manager = MQTTManager()
    telemetry_cache = TelemetryCache(mqtt_manager, MQTT_PUBLISH_INTERVAL)
    # time_series_logger = CSVTimeSeriesLogger()
    aggregator = CellDataAggregator()
    
    # Initialize connections
    can_interface.initialize()
    mqtt_manager.initialize()
    mqtt_manager.get_packet_id()  # Get initial packet ID
    
    # print(
    #     f"Starting CAN message processing with {MQTT_PUBLISH_RATE}Hz MQTT publishing..."
    # )
    
    publish_lock = asyncio.Lock()

    async def _publish_cached(current_time):
        async with publish_lock:
            await asyncio.to_thread(telemetry_cache.publish_cached_data, current_time)

    try:
        while True:
            try:
                # Offload potentially blocking CAN recv to a thread to avoid
                # stalling the asyncio event loop.
                msg_or_msgs = await asyncio.to_thread(can_interface.recv, 0.01)
                current_time = time.time()
                
                if msg_or_msgs:
                    # Handle both single message and list of messages
                    messages = msg_or_msgs if isinstance(msg_or_msgs, list) else [msg_or_msgs]
                    
                    for msg in messages:
                        can_id = msg.arbitration_id
                        
                        if 0x370 <= can_id <= 0x392:
                            all_vals, avg_val = aggregator.process_voltage(can_id, msg.data)
                            # latest_values_cache.update_value("diagnostics.cells_v", all_vals)
                            # latest_values_cache.update_value("pack.avg_cell_v", avg_val)
                            telemetry_cache.update_value(can_id, "diagnostics.cells_v", all_vals)
                            telemetry_cache.update_value(can_id, "pack.avg_cell_v", avg_val)
                            # time_series_logger.log_value("diagnostics.cells_v", str(all_vals), current_time)
                            # time_series_logger.log_value("pack.avg_cell_v", avg_val, current_time)
                        
                        elif 0x470 <= can_id <= 0x486:
                            all_vals, avg_val = aggregator.process_temperature(can_id, msg.data)
                            # latest_values_cache.update_value("thermal.cells_temp", all_vals)
                            # latest_values_cache.update_value("pack.avg_cell_temp", avg_val)
                            telemetry_cache.update_value(can_id, "thermal.cells_temp", all_vals)
                            telemetry_cache.update_value(can_id, "pack.avg_cell_temp", avg_val)
                            #time_series_logger.log_value("thermal.cells_temp", str(all_vals), current_time)
                            #time_series_logger.log_value("pack.avg_cell_temp", avg_val, current_time)

                        elif can_id in CAN_MAPPING:
                            mapping = CAN_MAPPING[can_id]
                            # Normalize mapping to always be a list of tuples
                            if isinstance(mapping, tuple):
                                mapping = [mapping]
                            
                            try:
                                for field_name, converter in mapping:
                                    try:
                                        value = converter(msg.data)
                                        # Get the protobuf field name and index, if it exists
                                        proto_info = get_protobuf_field_and_index(field_name)
                                        
                                        if proto_info:
                                            proto_field, proto_index, proto_size = proto_info
                                            # Use the protobuf field name for caching for MQTT and WebSocket
                                            latest_values_cache.update_value(proto_field, value, proto_index, proto_size)
                                            telemetry_cache.update_value(can_id, proto_field, value, proto_index, proto_size)
                                            # time_series_logger.log_value(field_name, value, current_time)
                                            #print(f"  -> Logged {proto_field}[{proto_index}]: {value}")
                                        else:
                                            # Fallback to the original field name if no mapping is found
                                            latest_values_cache.update_value(field_name, value)
                                            telemetry_cache.update_value(can_id, field_name, value)
                                            # time_series_logger.log_value(field_name, value, current_time)
                                            # print(f"  -> Logged {field_name}: {value}")
                                            
                                    except Exception as e:
                                        print(f"  -> Error converting {field_name} from CAN 0x{can_id:03X}: {e}")
                                        print(f"  -> Data bytes: {[f'{b:02X}' for b in msg.data]}")
                            except Exception as e:
                                print(f"  -> Error processing CAN 0x{can_id:03X}: {e}")
                                print(f"  -> Data bytes: {[f'{b:02X}' for b in msg.data]}")
                        # else:
                        #     prinit(f"  -> No mapping found for CAN ID 0x{can_id:03X}")
                else:
                    # Print a message every 10 seconds to show the system is running
                    if int(current_time) % 10 == 0 and int(current_time) != int(time.time() - 0.01):
                        print("Waiting for CAN messages...")
                
                # Check if it's time to publish cached data to MQTT
                if telemetry_cache.should_publish(current_time) and not publish_lock.locked():
                    #print(telemetry_cache)
                    asyncio.create_task(_publish_cached(current_time))
                
                # Print summary every 5 seconds
                if current_time - latest_values_cache.last_update_time >= 5.0:
                    latest_values_cache.print_summary()
                    latest_values_cache.last_update_time = current_time
                
                # Small delay to prevent blocking the event loop
                await asyncio.sleep(0.001)
            except Exception as e:
                print(f"CAN processing error: {e}")
    except KeyboardInterrupt:
        print("Stopping CAN processing.")
        # Print final summary and shutdown
        #latest_values_cache.print_summary()
        telemetry_cache.publish_cached_data(time.time())
        # time_series_logger.shutdown()
    finally:
        print("Shutting down CAN processing components...")
        # time_series_logger.shutdown()  # Ensure CSV logger flushes its buffer
        can_interface.shutdown()
        mqtt_manager.shutdown()


async def send_message(websocket, latest_values_cache):
    """Send telemetry updates to WebSocket clients"""
    print("WebSocket client connected, sending telemetry updates...")
    try:
        while True:
            # Get latest values from cache
            latest_values = latest_values_cache.get_latest_values()
            
            if latest_values:
                # Organize values by category (dynamics, controls, etc.)
                organized_data = {}
                for field_name, (value, timestamp) in latest_values.items():
                    # Split field name by dot to get category and subfield
                    parts = field_name.split('.')
                    if len(parts) >= 2:
                        category = parts[0]
                        subfield = '.'.join(parts[1:])
                        if category not in organized_data:
                            organized_data[category] = {}
                        organized_data[category][subfield] = value
                
                # Create telemetry update message
                message = {
                    "timestamp": time.time(),
                    "type": "telemetry_update",
                    "data": organized_data
                }
                
                # Send to WebSocket client
                await websocket.send(json.dumps(message))
            
            # Send updates at 30Hz (every 33.33ms)
            await asyncio.sleep(0.033)
    except Exception as e:
        print(f"WebSocket send error: {e}")


async def handler(websocket, latest_values_cache):
    print("client connected")
    send_task = asyncio.create_task(send_message(websocket, latest_values_cache))

    try:
        while True:
            try:
                message = await websocket.recv()
                print(f"Received from client: {message}")
            except ConnectionClosedOK:
                print("ConnectionClosedOK")
                break
    except KeyboardInterrupt:
        print("\n")

    send_task.cancel()  # stop sending task


async def main():
    try:
        latest_values=LatestValuesCache()
        # Start CAN processing task
        can_task = asyncio.create_task(process_can_messages(latest_values))
        
        # print("Websocket server on localhost:8001")
        # async with serve(lambda ws: handler(ws, latest_values), "", 8001):
        await asyncio.get_running_loop().create_future()
    except asyncio.exceptions.CancelledError:
        print("\nProgram interrupted. Exiting...")
    finally:
        can_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
