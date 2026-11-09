
import json
import time
import queue
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


class GopigoMQTTClient:

    def __init__(self, broker_host, broker_port=1883):

        self.broker_host = broker_host
        self.broker_port = broker_port

        self.component = "gopigo"
        self.message_id = 0

        # queue for incoming MQTT messages
        self.message_queue = queue.Queue()

        # MQTT client
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="gopigo-client"
        )

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # last Will and Testament
        offline_status = {
            "message_id": 0,
            "event_type": "status-update",
            "timestamp": self.get_timestamp(),
            "source": self.component,
            "data": {
                "status": "offline",
                "current_task": None,
                "order_id": None
            }
        }

        self.client.will_set(
            "restaurant/status/gopigo",
            json.dumps(offline_status),
            qos=1,
            retain=True
        )

    # generate UTC timestamp
    @staticmethod
    def get_timestamp():
        return datetime.now(timezone.utc).isoformat()

    # generate message ID
    def get_message_id(self):
        self.message_id += 1
        return self.message_id

    # connect to broker
    def connect(self):

        print(f"Connecting to MQTT broker: {self.broker_host}")

        self.client.connect(
            self.broker_host,
            self.broker_port,
            keepalive=60
        )

        self.client.loop_start()

    # called when connection is established
    def on_connect(self, client, userdata, flags, reason_code, properties):

        if reason_code.is_failure:
            print(f"MQTT connection failed: {reason_code}")
            return

        print("Connected to MQTT broker!")

        # subscribe to UR events
        client.subscribe(
            "restaurant/ur/events/drink-ready",
            qos=1
        )

         # subscribe to Tello events as test
        client.subscribe("restaurant/tello/events/customer-detected", qos=1)
        client.subscribe("restaurant/tello/events/order-completed", qos=1)

        # publish initial status
        self.publish_status("idle")

    # called when message arrives
    def on_message(self, client, userdata, msg):

        try:
            payload = json.loads(msg.payload.decode("utf-8"))

            print(f"\nMessage received on: {msg.topic}")
            print(json.dumps(payload, indent=4))

            # add message to queue for main program
            self.message_queue.put({
                "topic": msg.topic,
                "payload": payload
            })

        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            print(f"Invalid MQTT message: {error}")

    # process incoming messages in main program
    def handle_message(self, topic, payload):

        if topic == "restaurant/ur/events/drink-ready":
            order_id = payload.get("order_id")
            data = payload.get("data", {})
            print(f"Drink ready for order {order_id}")
            print(f"Table: {data.get('table_id')}")
            print(f"Product: {data.get('product_id')}")
            print(f"Pickup location: {data.get('pickup_location')}")

            return {
                "event": "drink-ready",
                "order_id": order_id,
                "table_id": data.get("table_id"),
                "product_id": data.get("product_id"),
                "pickup_location": data.get("pickup_location")
            }
        
        # tello topics
        elif topic == "restaurant/tello/events/customer-detected":
            order_id = payload.get("order_id")
            data = payload.get("data", {})
            print(f"Customer detected for order {order_id}")
            return {
                "event": "customer-detected",
                "order_id": order_id,
                "table_id": data.get("table_id"),
            }

        elif topic == "restaurant/tello/events/order-completed":
            order_id = payload.get("order_id")
            print(f"Order {order_id} completed")
            return {
                "event": "order-completed",
                "order_id": order_id
            }

        else:
            print(f"Unknown topic: {topic}")
            return None

    # publish event
    def publish_event(self, event_identifier, data, order_id=None):

        topic = f"restaurant/gopigo/events/{event_identifier}"

        message = {
            "message_id": self.get_message_id(),
            "event_type": event_identifier,
            "timestamp": self.get_timestamp(),
            "source": self.component,
            "order_id": order_id,
            "data": data
        }

        result = self.client.publish(
            topic,
            json.dumps(message),
            qos=1,
            retain=False
        )

        print(f"Published event: {topic}")

        return result

    # publish robot status
    def publish_status(
        self,
        status,
        current_task=None,
        order_id=None,
        battery_level=None,
        error=None
    ):

        topic = "restaurant/status/gopigo"
        # data field for message
        data = {
            "status": status,
            "current_task": current_task,
            "order_id": order_id
        }

        if battery_level is not None:
            data["battery_level"] = battery_level

        if error is not None:
            data["error"] = {
                "description": error
            }
        # message to publish
        message = {
            "message_id": self.get_message_id(),
            "event_type": "status-update",
            "timestamp": self.get_timestamp(),
            "source": self.component,
            "data": data
        }

        self.client.publish(
            topic,
            json.dumps(message),
            qos=1,
            retain=True
        )

        print(f"Published status: {status}")

    # publish delivery completed event
    def publish_delivery_completed(self, order_id, table_id):

        return self.publish_event(
            "delivery-completed",
            {
                "table_id": table_id,
                "delivery_status": "delivered"
            },
            order_id=order_id
        )

    # publish returned event
    def publish_returned(self, order_id, location="ur_station"):

        return self.publish_event(
            "returned",
            {
                "location": location
            },
            order_id=order_id
        )

    # called when connection is lost or closed
    def on_disconnect(
        self,
        client,
        userdata,
        disconnect_flags,
        reason_code,
        properties
    ):
        print(f"Disconnected from MQTT broker: {reason_code}")

    # disconnect from broker
    def disconnect(self):

        # publish offline status before graceful disconnect
        self.publish_status("offline")

        time.sleep(0.2)

        self.client.disconnect()
        self.client.loop_stop()

        print("Disconnected from MQTT broker")
