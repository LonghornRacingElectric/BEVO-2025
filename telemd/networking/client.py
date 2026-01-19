import paho.mqtt.client as mqtt
import os
import requests
import time
import threading
from protobuf import publish_msg

class TelemetryCache:
    """Caches telemetry data and publishes at fixed rate"""
    
    def __init__(self, mqtt_manager, publish_interval=0.003):  # 333Hz default
        self.mqtt_manager = mqtt_manager
        self.cache = {}  # field_name -> latest_value
        self.last_publish_time = time.time()
        self.publish_interval = publish_interval
        self.lock = threading.Lock()
        # Initialize odometer value from file at root of telemd folder
        # self.odometer = self._load_odometer()

    # -------------------------
    # Odometer persistence
    # -------------------------
    def _odometer_file_path(self):
        """Return absolute path to the odometer file at telemd/odometer.
        This file is referenced relative to this file's directory (../odometer).
        """
        here = os.path.dirname(__file__)
        return os.path.abspath(os.path.join(here, "..", "odometer"))

    def _load_odometer(self) -> float:
        """Load odometer value from file. If missing or invalid, return 0.0."""
        path = self._odometer_file_path()
        try:
            with open(path, "r") as f:
                content = f.read().strip()
                if not content:
                    return 0.0
                return float(content)
        except FileNotFoundError:
            # No persisted value yet
            return 0.0
        except Exception as e:
            # Corrupt/invalid content, log and continue with 0.0
            # print(f"[WARN] Failed to read odometer from {path}: {e}. Defaulting to 0.0")
            return 0.0

    def _save_odometer(self):
        """Persist current odometer value to file atomically."""
        path = self._odometer_file_path()
        tmp_path = path + ".tmp"
        try:
            # Ensure parent directory exists (telemd/)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(tmp_path, "w") as f:
                f.write(f"{self.odometer}\n")
                f.flush()
                os.fsync(f.fileno())
            # Atomic replace: move tmp to target so the original file is fully
            # replaced in one operation (avoids partial/corrupt writes on crash)
            os.replace(tmp_path, path)
        except Exception as e:
            print(f"[WARN] Failed to write odometer to {path}: {e}")
        
    def update_value(self, can_id, field_name, value, index=None, size=None):
        """Cache a telemetry value, handling repeated fields."""
        with self.lock:
            if index is not None:
                # It's a repeated field, store it in a list
                if field_name not in self.cache:
                    if size is not None:
                        self.cache[field_name] = [None] * size
                    else:
                        # Fallback if size is not provided, though it should be
                        self.cache[field_name] = []

                if index < len(self.cache[field_name]):
                    self.cache[field_name][index] = value
                else:
                    # Handle cases where index is out of bounds
                    print(f"Warning: index {index} out of bounds for {field_name}")
            else:
                # It's a single value field
                self.cache[field_name] = value
        
    def should_publish(self, current_time):
        """Check if it's time to publish"""
        with self.lock:
            return current_time - self.last_publish_time >= self.publish_interval
        
    def publish_cached_data(self, current_time):
        """Publish all complete cached data to MQTT"""
        with self.lock:
            if not self.cache:
                return

            complete_fields = {}
            for field_name, value in self.cache.items():
                if isinstance(value, list):
                    if all(v is not None for v in value):
                        complete_fields[field_name] = value
                else:
                    complete_fields[field_name] = value

            if not complete_fields:
                return

            #! TESTING REQUIRED ||| compute odometer value
            # speed = complete_fields.get("dynamics.blw_speed")  #! dunno if this is the actual value
            # if speed is not None:
            #     delta_t = current_time - self.last_publish_time
            #     self.odometer += speed * delta_t / 1000  # preserve original scaling
            #     # Keep cache and snapshot in sync
            #     self.cache["diagnostics.odometer"] = self.odometer
            #     complete_fields["diagnostics.odometer"] = self.odometer

            # Get current packet ID (local, not from server)
            packet_id = self.mqtt_manager.get_packet_id()

            telemetry_data = {
                "timestamp": current_time,
                "packet_id": packet_id,
                "fields": complete_fields,
            }

        # Publish via MQTT (this will increment packet ID after successful publish)
        success = self.mqtt_manager.publish(telemetry_data, publish_msg)

        if success:
            with self.lock:
                # Clear only the published fields from the cache
                for field_name in complete_fields:
                    if field_name in self.cache:
                        del self.cache[field_name]

                self.last_publish_time = current_time

            # Persist updated odometer value
            # self._save_odometer() // dont save ts
        else:
            print(f"Failed to publish packet {packet_id}, will retry next cycle")


class MQTTManager:
    """Manages MQTT connection and publishing"""
    
    def __init__(self, broker="192.168.1.109", port=1883, topic="angelique"):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = None
        self.connected = False
        self.packet_id = 0
        
    def initialize(self):
        """Initialize MQTT connection and fetch initial packet ID"""
        try:
            # Use the newer MQTT client API to avoid deprecation warning
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.client.connect(self.broker, self.port, 60)
            self.connected = True
            print(f"Successfully connected to MQTT broker at {self.broker}:{self.port}")
            
            # Fetch initial packet ID from server
            self._fetch_initial_packet_id()
            
            return True
        except Exception as e:
            print(f"Warning: Could not connect to MQTT broker at {self.broker}:{self.port}")
            print(f"MQTT error: {e}")
            print("Continuing with WebSocket functionality only...")
            self.connected = False
            return False
    
    def _fetch_initial_packet_id(self):
        """Fetch initial packet ID from server (only called once during initialization)"""
        try:
            #res = requests.get("https://lhrelectric.org/webtool/handshake/")
            self.packet_id = 0
            print(f"Retrieved initial packet ID: {self.packet_id}")
        except Exception as e:
            print(f"Warning: Could not get handshake data: {e}")
            print("Using default packet ID: 0")
            self.packet_id = 0
    
    def get_packet_id(self):
        """Get current packet ID (does not fetch from server)"""
        return self.packet_id
    
    def increment_packet_id(self):
        """Increment the packet ID"""
        self.packet_id += 1
        return self.packet_id
    
    def is_connected(self):
        """Check if MQTT is connected"""
        return self.connected and self.client
    
    def get_client(self):
        """Get the MQTT client instance"""
        return self.client
    
    def publish(self, telemetry_data, protobuf_func):
        """Publish telemetry data via MQTT"""
        if not self.is_connected():
            print(f"MQTT not connected, skipping publish for packet {telemetry_data.get('packet_id', 'unknown')}")
            return False
        
        try:
            packet_id = telemetry_data.get('packet_id', self.packet_id)
            fields = telemetry_data.get('fields', {})
            print(f"Attempting to publish packet {packet_id} with {len(fields)} fields")
            
            # Import protobuf directly to populate with telemetry data
            from protobuf import generated as pb
            
            # Create protobuf message and populate with telemetry data
            sensor_msg = pb.AngeliqueSensorData()
            sensor_msg.time = int(telemetry_data.get('timestamp', time.time()) * 1000)
            sensor_msg.packet_id = packet_id
            
            # Set each field in the protobuf
            for field_name, value in fields.items():
                try:
                    # Navigate to the nested object and set the field
                    obj = sensor_msg
                    parts = field_name.split('.')
                    for part in parts[:-1]:
                        obj = getattr(obj, part)
                    
                    field_name_on_obj = parts[-1]
                    field_descriptor = obj.DESCRIPTOR.fields_by_name[field_name_on_obj]
                    is_integer_field = field_descriptor.type in [
                        field_descriptor.TYPE_INT32, field_descriptor.TYPE_INT64,
                        field_descriptor.TYPE_UINT32, field_descriptor.TYPE_UINT64,
                        field_descriptor.TYPE_SINT32, field_descriptor.TYPE_SINT64,
                        field_descriptor.TYPE_FIXED32, field_descriptor.TYPE_FIXED64,
                        field_descriptor.TYPE_SFIXED32, field_descriptor.TYPE_SFIXED64
                    ]
                    
                    if isinstance(value, list):
                        field = getattr(obj, field_name_on_obj)
                        if is_integer_field:
                            field.extend([int(item) for item in value if item is not None])
                        else:
                            field.extend([float(item) for item in value if item is not None])
                    else: 
                        if is_integer_field:
                            setattr(obj, field_name_on_obj, int(value))
                        else:
                            setattr(obj, field_name_on_obj, float(value))

                except Exception as e:
                    print(f"[WARN] Failed to set {field_name}: {e}")
            
            # Serialize and publish
            payload = sensor_msg.SerializeToString()
            # print(f"[DEBUG] Protobuf message size: {len(payload)} bytes")
            
            result = self.client.publish(self.topic, payload)
            # print(f"[DEBUG] MQTT publish result: {result}")
            # print(f"[DEBUG] MQTT publish return code: {result.rc}")
            # print(f"[DEBUG] MQTT publish message ID: {result.mid}")
            
            if result.rc == 0:
                # print(f"[MQTT] Successfully published protobuf message ({len(payload)} bytes) to topic '{self.topic}'")
                # Only increment packet ID after successful publish
                self.increment_packet_id()
                # print(f"Successfully published packet {packet_id}")
                return True
            else:
                print(f"[ERROR] MQTT publish failed with return code: {result.rc}")
                return False
                
        except Exception as e:
            print(f"MQTT publish error: {e}")
            self.connected = False
            return False
    
    def shutdown(self):
        """Clean shutdown of MQTT connection"""
        if self.client:
            try:
                self.client.disconnect()
                print("MQTT connection closed")
            except Exception as e:
                print(f"Error closing MQTT connection: {e}") 
