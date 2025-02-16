import template_pb2  # Import the compiled Protobuf module
import paho.mqtt.client as mqtt

# MQTT Broker Settings (Change this to your broker details)
MQTT_BROKER = "mqtt.example.com"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/data"

# Function to create and serialize a SensorData message
def create_sensor_data():
    sensor_data = template_pb2.SensorData()
    sensor_data.time = 1234567890
    sensor_data.packet_id = 42

    # Fill nested Dynamics message
    sensor_data.dynamic_data.acc_pedal.append(0.8)
    sensor_data.dynamic_data.brake_pedal = 0.2
    sensor_data.dynamic_data.steering_angle = 15.0

    # Serialize the data
    return sensor_data.SerializeToString()

# MQTT Publish Function
def publish_message():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    serialized_message = create_sensor_data()
    client.publish(MQTT_TOPIC, serialized_message)
    print("Message sent!")

    client.disconnect()

# MQTT On-Message Callback for Receiving Data
def on_message(client, userdata, msg):
    received_data = template_pb2.SensorData()
    received_data.ParseFromString(msg.payload)

    print(f"Received time: {received_data.time}")
    print(f"Received packet_id: {received_data.packet_id}")

# MQTT Subscriber Setup
def subscribe_to_topic():
    client = mqtt.Client()
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC)

    print("Subscribed to topic. Waiting for messages...")
    client.loop_forever()

# Uncomment one of the following lines to either send or receive messages:
# publish_message()  # Send Protobuf data
# subscribe_to_topic()  # Receive and decode Protobuf data
