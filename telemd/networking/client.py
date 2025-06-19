import paho.mqtt.client as mqtt
import os
import requests
import time
from protobuf import publish_msg


class TelemetryCache:
    """Caches telemetry data and publishes at fixed rate"""
    
    def __init__(self, mqtt_manager, publish_interval=0.003):  # 333Hz default
        self.mqtt_manager = mqtt_manager
        self.cache = {}  # field_name -> latest_value
        self.last_publish_time = time.time()
        self.publish_interval = publish_interval
        
    def update_value(self, can_id, field_name, value):
        """Cache a telemetry value"""
        self.cache[field_name] = value
        
    def should_publish(self, current_time):
        """Check if it's time to publish"""
        return current_time - self.last_publish_time >= self.publish_interval
        
    def publish_cached_data(self, current_time):
        """Publish all cached data to MQTT"""
        if not self.cache:
            return
            
        # Get current packet ID (local, not from server)
        packet_id = self.mqtt_manager.get_packet_id()
        
        # Create telemetry packet with all cached values
        telemetry_data = {
            "timestamp": current_time,
            "packet_id": packet_id,
            "fields": self.cache.copy(),
        }
        
        # Publish via MQTT (this will increment packet ID after successful publish)
        success = self.mqtt_manager.publish(telemetry_data, publish_msg)
        
        if success:
            # Clear cache and update timestamp only on successful publish
            self.cache.clear()
            self.last_publish_time = current_time
            
            print(
                f"Published {len(telemetry_data['fields'])} fields to MQTT (packet {packet_id})"
            )
        else:
            print(f"Failed to publish packet {packet_id}, will retry next cycle")


class MQTTManager:
    """Manages MQTT connection and publishing"""
    
    def __init__(self, broker="192.168.1.109", port=1883, topic="data"):
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
            res = requests.get("https://lhrelectric.org/webtool/handshake/")
            self.packet_id = res.json()["last_packet"]
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
            sensor_msg = pb.SensorData()
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
                    setattr(obj, parts[-1], value)
                    print(f"[DEBUG] Set {field_name} = {value}")
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
                print(f"[MQTT] Successfully published protobuf message ({len(payload)} bytes) to topic '{self.topic}'")
                # Only increment packet ID after successful publish
                self.increment_packet_id()
                print(f"Successfully published packet {packet_id}")
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