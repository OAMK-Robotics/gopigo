import paho.mqtt.client as mqtt

BROKER_HOST = "10.4.3.51"  # broker IP
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
    else:
        print(f"Connection failed: {reason_code}")


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="gopigo-test"
)

client.on_connect = on_connect

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