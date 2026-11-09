# Main progrman processes orders and manages robot status

import time
import queue
import threading

from robot_setup import initialize_robot
from mqtt_client import GopigoMQTTClient
from navigation import navigate 


# IP address of the MQTT broker (the computer running the broker)
BROKER_HOST = "192.168.1.96" 

# Create an instance of the GopigoMQTTClient
mqtt_client = GopigoMQTTClient(BROKER_HOST)

def main():
    # initialize GoPiGo hardware
    gpg, line_follower, distance_sensor, buzzer = initialize_robot()

    # connect to the MQTT broker
    mqtt_client.connect()
    
    stop_event = threading.Event() # event to signal the navigation thread to stop
    navigation_thread = None # thread to run the navigation function

    try:
        while True:
            try:
                # get the next message from the queue with timeout allowing checking for stop_event
                message = mqtt_client.message_queue.get(timeout=0.5)
            except queue.Empty:
                continue # no message received, continue to check for stop_event
            
            # Process the received MQTT message
            event = mqtt_client.handle_message(
                message["topic"],
                message["payload"]
            )
            if event is None:
                continue

            if event["event"] == "drink-ready":

                order_id = event["order_id"]
                table_id = event["table_id"]

                if order_id is None or table_id is None:
                    print("Invalid drink-ready message")
                    continue

                # don't start another navigation task while one is running
                if navigation_thread and navigation_thread.is_alive():
                    print("GoPiGo is already busy")
                    continue

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
                    target=navigate, # function to run in the thread
                    args=(
                        gpg,
                        line_follower,
                        distance_sensor,
                        buzzer,
                        table_id,
                        stop_event,
                    )
                )

                navigation_thread.start()
            
            # Handle other events if needed
            elif event["event"] == "customer-detected":
                print("GoPiGo received customer-detected event")

            elif event["event"] == "order-completed":
                print("GoPiGo received order-completed event")

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