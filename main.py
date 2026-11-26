# Main progrman processes orders and manages robot status

import time
import os
import queue
import threading
from dotenv import load_dotenv

from init import initialize_robot
from mqtt_client import GopigoMQTTClient
#from test_navigation6 import navigation
from new_test_nav import navigation 

load_dotenv()

BROKER_HOST = os.getenv("BROKER_HOST")
BROKER_PORT = int(os.getenv("BROKER_PORT"))
USERNAME = os.getenv("USERNAME")
PASSWD = os.getenv("PASSWD")

# Create an instance of the GopigoMQTTClient
mqtt_client = GopigoMQTTClient(BROKER_HOST, BROKER_PORT, USERNAME, PASSWD, client_id="gopigo-main")

def cup_removed_callback(table_id):
    mqtt_client.publish_event(
        "delivery-completed",
        {
            "table_id": table_id,
            "delivery_status": "delivered"
        }
    )


def returned_to_pickup_callback(table_id):
    mqtt_client.publish_event(
        "returned",
        {
            "table_id": table_id,
            "pickup_location": "ur_station",
        }
    )


def main():
    # initialize GoPiGo hardware
    gpg, line_follower, distance_sensor, buzzer, cup_distance_sensor = initialize_robot()

    # connect to the MQTT broker
    mqtt_client.connect()

    stop_event = threading.Event() # event to signal the navigation thread to stop
    navigation_thread = None # thread to run the navigation function

    # add new orders into queue
    order_queue = queue.Queue()

    try:
        while True:
            try:
                # get the next message from the queue with timeout allowing checking for stop_event
                message = mqtt_client.message_queue.get(timeout=0.5)
            except queue.Empty:
                message = None

            # Process the received MQTT message
            event = None

            if message is not None:
                event = mqtt_client.handle_message(
                    message["topic"],
                    message["payload"]
                )

            if event is not None:

                if event["event"] == "drink-ready":

                    order_id = event["order_id"]
                    table_id = event["table_id"]
                    #table_id=1

                    if order_id is None or table_id is None:
                        print("Invalid drink-ready message")
                    else:
                        # Add order to waiting queue
                        order_queue.put({
                            "order_id": order_id,
                            "table_id": table_id
                        })

                        print(f"Order {order_id} added to order queue")

                # Handle other events if needed
                elif event["event"] == "customer-detected":
                    print("GoPiGo received customer-detected event")

                elif event["event"] == "order-completed":
                    print("GoPiGo received order-completed event")

            # don't start another navigation task while one is running
            if (
                not order_queue.empty()
                and (navigation_thread is None or not navigation_thread.is_alive())
            ):
                order = order_queue.get()

                order_id = order["order_id"]
                table_id = order["table_id"]

                print(f"Starting delivery of order {order_id}")
                print(f"Destination: table {table_id}")

                mqtt_client.publish_status(
                    "busy",
                    current_task="delivering-order",
                    order_id=order_id
                )

                # clear stop event before starting navigation
                stop_event.clear()

                # start separate thread for navigation to avoid
                # blocking the main thread that handles MQTT messages
                navigation_thread = threading.Thread(
                    target=navigation, # function to run in the thread
                    args=(
                        gpg,
                        line_follower,
                        distance_sensor,
                        buzzer,
                        cup_distance_sensor,
                        table_id,
                        stop_event,
                        cup_removed_callback,
                        returned_to_pickup_callback
                    )
                )

                navigation_thread.start()

    except KeyboardInterrupt:
        print("Stopping GoPiGo...")

    finally:
        stop_event.set()

        # wait for navigation thread to finish
        if navigation_thread and navigation_thread.is_alive():
            # join means wait for the thread to finish
            navigation_thread.join(timeout=2)

        gpg.stop()
        mqtt_client.disconnect()


if __name__ == "__main__":
    main()
