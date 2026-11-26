
import time
import threading

from init import initialize_robot

from fun2 import (
    handle_obstacle,
    follow_line_proportional_2,
    navigate_fork_smooth2,
    wait_for_cup_removal,
    stop_at_table,
    retry,
    turn_around
)


def navigation(
    gpg,
    line_follower,
    distance_sensor,
    buzzer,
    cup_distance_sensor,
    table_id,
    stop_event,
    cup_removed_callback,
    returned_to_pickup_callback
):
    """
    Navigates to the selected table, stops at the destination marker,
    and waits for cup removal.

    Returns:
        True: cup removal was confirmed.
        False: navigation failed or was interrupted.
    """

    routes = {
        1: ["right"],
        2: ["left"]
    }
    
    turn_direction = routes.get(table_id)

    if turn_direction is None:
        print(f"No route defined for table {table_id}")
        return False

    print(f"Starting navigation to table {table_id}")
    print(f"Route: {turn_direction}")

    try:
        # ------------------------------------------
        # 1. Navigate through the junction
        # ------------------------------------------

        turn_around(gpg)  # Turn around before navigating to the table

        for turn in turn_direction:

            if stop_event.is_set():
                print("Navigation stopped.")
                return False

            print(f"Approaching junction: turning {turn}")

            turn_success = navigate_fork_smooth2(
                gpg,
                line_follower,
                turn,
                stop_event
            )

            if not turn_success:
                print("Junction navigation failed.")
                return False

        # ------------------------------------------
        # 2. Follow the line to the destination
        # ------------------------------------------

        print("Following line to destination...")

        while not stop_event.is_set():

            # Check whether the destination marker is detected
            if stop_at_table(gpg, line_follower):
                print("Reached the table. Robot stopped.")
                gpg.stop()
                break

            # Check for obstacles using the I2C sensor
            distance = retry(distance_sensor.read)

            print(f"Obstacle sensor: {distance} cm")

            while distance is not None and 0 < distance < 10:
                print(f"Obstacle detected at {distance} cm!")

                gpg.stop()

                obstacle_handled = handle_obstacle(gpg, buzzer)

                if not obstacle_handled:
                    print("Obstacle handling interrupted or failed.")
                    break

                if stop_event.is_set():
                    break

                # Check whether the destination marker is detected
                if stop_at_table(gpg, line_follower):
                    print("Reached the table. Robot stopped.")
                    gpg.stop()
                    break

                # Check whether the obstacle has actually cleared
                distance = retry(distance_sensor.read)

                print(f"Obstacle sensor after handling: {distance} cm")

                """if distance is not None and 0 < distance < 10:
                    print("Obstacle is still present. Stopping navigation.")
                    gpg.stop()
                   
                   return False"""

                print("Path is clear. Continuing navigation.")

                continue

            # Follow the black line
            follow_line_proportional_2(gpg, line_follower)

            time.sleep(0.05)

        # ------------------------------------------
        # 3. Wait for cup removal at the table
        # ------------------------------------------

        if stop_event.is_set():
            return False

        print("Waiting for cup removal...")
        #buzzer removed from params
        collected = wait_for_cup_removal(
            cup_distance_sensor,
            stop_event
        )

        if not collected:
            print("Cup removal was not confirmed.")
            return False

        print("Drink collection confirmed!")
        cup_removed_callback(table_id)

        # Turn slightly to align with the return line
        gpg.turn_degrees(-10)
        gpg.forward()
        time.sleep(0.3)
        gpg.stop()

        # set speed sligthly faster for return navigation 
        # to avoid getting stuck at the junction 
        start_time = time.time()
        while time.time() - start_time < 5:
            gpg.set_speed(250)

        print("Continuing line following...")

        # Continue following the line
        while not stop_event.is_set():

            # Check whether the pickup marker is detected
            if stop_at_table(gpg, line_follower):
                print("Returned to pickup location")
                gpg.stop()
                returned_to_pickup_callback(table_id)
                return True

            # Check for obstacles using the I2C sensor
            distance = retry(distance_sensor.read)

            print(f"Obstacle sensor: {distance} cm")

            if distance is not None and 0 < distance < 10:
                print(f"Obstacle detected at {distance} cm!")

                gpg.stop()

                obstacle_handled = handle_obstacle(gpg, buzzer)

                if not obstacle_handled:
                    print("Obstacle handling interrupted or failed.")
                    break

                if stop_event.is_set():
                    break

                # Check whether the pickup marker is detected
                if stop_at_table(gpg, line_follower):
                    print("Returned to pickup location")
                    gpg.stop()
                    returned_to_pickup_callback(table_id)
                    return True

                # Check whether the obstacle has actually cleared
                distance = retry(distance_sensor.read)

                print(f"Obstacle sensor after handling: {distance} cm")

                if distance is not None and 0 < distance < 10:
                    print("Obstacle is still present. Stopping navigation.") 
                    gpg.stop()
                    return False

                print("Path is clear. Continuing navigation.")

                continue

            # Follow the black line
            follow_line_proportional_2(gpg, line_follower)

            time.sleep(0.05)

        return False

    finally:
        # Always stop the robot when this function exits
        gpg.stop()
        buzzer.sound_off()


# ==================================================
# Standalone navigation test (without main.py or MQTT)
# ==================================================

if __name__ == "__main__":

    gpg = None
    buzzer = None
    stop_event = threading.Event()

    table_id = 1

    try:
        print("Initializing GoPiGo...")
        (
            gpg,
            line_follower,
            distance_sensor,
            buzzer,
            cup_distance_sensor
        ) = initialize_robot()

        print("Distance sensor:", distance_sensor)
        print("Cup distance sensor:", cup_distance_sensor)

        print("Hardware initialized successfully.")
        print(f"Starting navigation test for table {table_id}")

        success = navigation(
            gpg,
            line_follower,
            distance_sensor,
            buzzer,
            cup_distance_sensor,
            table_id,
            stop_event,
            cup_removed_callback=lambda table_id: print(
                f"TEST: Cup removed from table {table_id}"
            ),
            returned_to_pickup_callback=lambda table_id: print(
                f"TEST: Returned to pickup point {table_id}" 
                
            )
        )

        if success:
            print("TEST SUCCESSFUL!")
            print("Cup removal was detected.")
            print("Robot returned to pickup point.")
        else:
            print("TEST FAILED or navigation was stopped.")

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")

    except Exception as error:
        print(f"Test error: {error}")
        raise

    finally:
        stop_event.set()

        if gpg is not None:
            gpg.stop()
        if buzzer is not None:
            buzzer.sound_off()

        print("Test finished. Robot stopped.")
