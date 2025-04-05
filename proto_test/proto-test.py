import template_pb2 
import paho.mqtt.client as mqtt

MQTT_BROKER = "192.168.1.109"
MQTT_PORT = 8080
MQTT_TOPIC = "data"

def create_sensor_data():
    sensor_data = template_pb2.SensorData()
    sensor_data.time = 1234567890

    return sensor_data.SerializeToString()

def publish_message():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    serialized_message = create_sensor_data()
    client.publish(MQTT_TOPIC, serialized_message)
    print("Message sent!")

    client.disconnect()

# subscribe 

# def on_message(client, userdata, msg):
#     received_data = template_pb2.SensorData()
#     received_data.ParseFromString(msg.payload)

#     print(f"Received time: {received_data.time}")
#     print(f"Received packet_id: {received_data.packet_id}")

# def subscribe_to_topic():
#     client = mqtt.Client()
#     client.on_message = on_message

#     client.connect(MQTT_BROKER, MQTT_PORT, 60)
#     client.subscribe(MQTT_TOPIC)

#     print("Subscribed to topic. Waiting for messages...")
#     client.loop_forever()

publish_message() 
# subscribe_to_topic()  # Receive and decode Protobuf data
