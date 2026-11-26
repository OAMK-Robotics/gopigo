
import json
import os
import paho.mqtt.client as mqtt
from mqtt_client import GopigoMQTTClient 
from dotenv import load_dotenv
import time

load_dotenv()

BROKER_HOST = os.getenv("BROKER_HOST")
BROKER_PORT = int(os.getenv("BROKER_PORT"))
USERNAME = os.getenv("USERNAME")
PASSWD = os.getenv("PASSWD")

# Select table for navigation test
TABLE_ID = 1
ORDER_ID = 1

client = GopigoMQTTClient(
    BROKER_HOST, 
    BROKER_PORT, 
    USERNAME, 
    PASSWD,
    client_id="gopigo-test"
)

def on_connect(client, userdata, flags, reason_code, properties):

    if reason_code.is_failure:
        print(f"Connection failed: {reason_code}")
        return

    print("Connected to MQTT broker!")

    topics = [
        ("restaurant/ur/events/drink-ready", 1),
        ("ur16e/commands", 1),
        ("test/topic", 1),
        ("restaurant/tello/events/customer-detected", 1),
        ("restaurant/tello/events/order-completed", 1),
        ("restaurant/ur/events/returned", 1),
        ("restaurant/gopigo/events/delivery-completed", 1)
    ]

    for topic, qos in topics:
        client.subscribe(topic, qos=qos)
        print(f"Subscribed to: {topic}")

    # Publish test message
    client.publish(
        "test/topic",
        json.dumps({"message": "Hello from GoPiGo!"}),
        qos=1
    )

    print("Test message published!")

    # Publish drink-ready event to start navigation in main.py
    test_message = {
        "order_id": 1,
        "data": {
            "table_id": TABLE_ID
        }
    }

    client.publish(
        "restaurant/ur/events/drink-ready",
        json.dumps(test_message),
        qos=1
    )

    '''
    client.publish(
        "restaurant/ur/events/returned",
        json.dumps({
            "order_id": 1,
            "data": {
                "table_id": TABLE_ID,
                "pickup_location": "ur_station"
            }
        }),
        qos=1
    )
    '''

    print(f"Navigation test published for table {TABLE_ID}!")


def on_message(client, userdata, msg):

    print(f"\nMessage received on: {msg.topic}")

    try:
        payload = json.loads(msg.payload.decode("utf-8"))

        print("Payload:")
        print(json.dumps(payload, indent=4))

        if msg.topic == "ur16e/commands":
            print(f"Test message of UR arm: {payload.get('cmd')}")

        elif msg.topic == "test/topic":
            print(f"Test message: {payload.get('message')}")

        elif msg.topic == "restaurant/ur/events/drink-ready":
            print("UR drink-ready event received!")
            print(f"Table ID: {payload.get('data', {}).get('table_id')}")

        elif msg.topic == "restaurant/tello/events/customer-detected":
            print("Tello customer-detected event received!")

        elif msg.topic == "restaurant/tello/events/order-completed":
            print("Tello order-completed event received!")

        elif msg.topic == "restaurant/gopigo/events/delivery-completed":
            print("GoPiGo delivery-completed event received!")
            
        elif msg.topic == "restaurant/ur/events/returned":
            print("UR returned event received!")

    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        print(f"Invalid MQTT message: {error}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f"Disconnected: {reason_code}")

'''
client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="gopigo-test"
)
'''

client.client.on_connect = on_connect
client.client.on_message = on_message
client.client.on_disconnect = on_disconnect


try:
    print(f"Connecting to {BROKER_HOST}:{BROKER_PORT}...")
    client.connect()

    print("Connected to MQTT broker!")

    # Keep the script running to receive messages
    while True:
        time.sleep(1)  

except KeyboardInterrupt:
    print("\nDisconnecting...")

except Exception as error:
    print(f"MQTT error: {error}")

finally:
    client.disconnect()
