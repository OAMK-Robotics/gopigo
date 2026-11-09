# pip install paho-mqtt
import paho.mqtt.client as mqtt

BROKER_HOST = "192.168.1.96"  # broker IP
BROKER_PORT = 1883

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT broker!")

        client.publish(
            "test/topic",
            '{"message": "Hello from GoPiGo!"}',
            qos=1
        )
        print("Test message published!")

        client.subscribe("restaurant/ur/events/drink-ready", qos=1)
        # Subscribe to Tello events for testing purposes
        client.subscribe("restaurant/tello/events/customer-detected", qos=1)
        client.subscribe("restaurant/tello/events/order-completed", qos=1)

        print("Subscriptions successful!")

    else:
        print(f"Connection failed: {reason_code}")


def on_message(client, userdata, msg):
    print(f"\nMessage received on: {msg.topic}")
    print(f"Payload: {msg.payload.decode('utf-8')}")

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="gopigo-test"
)

client.on_connect = on_connect
client.on_message = on_message

try:
    print(f"Connecting to {BROKER_HOST}:{BROKER_PORT}...")
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_forever() 

except KeyboardInterrupt:
    print("Disconnecting...")

except Exception as error:
    print(f"MQTT error: {error}")

finally:
    client.disconnect()