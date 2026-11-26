import time
import threading
import config

from init import initialize_robot

from functions_fix import (
    handle_obstacle,
    follow_line_proportional,
    navigate_fork_smooth2,
    wait_for_cup_removal,
    stop_at_table,
    read_obstacle_distance,
    is_obstacle_close,
    wait_until_obstacle_cleared,
    retry,
    turn_around
)


# Slower speed on return once the second black line is encountered
RETURN_LINE_SPEED = min(config.SPEED, 130)


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

        # Check for obstacles immediately from the start of navigation
        if not wait_until_obstacle_cleared(gpg, distance_sensor, buzzer, stop_event):
            return False

        for turn in turn_direction:

            if stop_event.is_set():
                print("Navigation stopped.")
                return False

            print(f"Approaching junction: turning {turn}")

            turn_success = navigate_fork_smooth2(
                gpg,
                line_follower,
                turn,
                stop_event=stop_event,
                distance_sensor=distance_sensor,
                buzzer=buzzer
            )

            if not turn_success:
                print("Junction navigation failed.")
                return False

        # ------------------------------------------
        # 2. Follow the line to the destination
        # ------------------------------------------

        print("Following line to destination...")

        while not stop_event.is_set():

            # Check whether the first black marker (table) is detected
            if stop_at_table(gpg, line_follower):
                print("Reached the table. Robot stopped.")
                gpg.stop()
                break

            # Check for obstacles using the I2C sensor and wait until cleared
            distance = read_obstacle_distance(distance_sensor)
            print(f"Obstacle sensor: {distance} cm")

            while is_obstacle_close(distance):
                print(f"Obstacle detected at {distance} cm!")

                gpg.stop()

                if not wait_until_obstacle_cleared(
                    gpg, distance_sensor, buzzer, stop_event
                ):
                    return False

                if stop_event.is_set():
                    break

                # Check whether the destination marker is detected
                if stop_at_table(gpg, line_follower):
                    print("Reached the table. Robot stopped.")
                    gpg.stop()
                    break

                # Check whether the obstacle has actually cleared
                distance = read_obstacle_distance(distance_sensor)
                print(f"Obstacle sensor after handling: {distance} cm")

                """if distance is not None and 0 < distance < 10:
                    print("Obstacle is still present. Stopping navigation.")
                    gpg.stop()

                   return False"""

                if not is_obstacle_close(distance):
                    print("Path is clear. Continuing navigation.")

            if stop_event.is_set():
                return False

            if stop_at_table(gpg, line_follower):
                print("Reached the table. Robot stopped.")
                gpg.stop()
                break

            # Follow the black line without line follower errors breaking navigation
            if not follow_line_proportional(gpg, line_follower):
                gpg.forward()

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
        if turn_direction == "left":
            gpg.turn_degrees(-10)
        else:
            gpg.turn_degrees(10)
        gpg.set_speed(250)
        gpg.forward()
        time.sleep(0.3)
        gpg.stop()

        print("Continuing return navigation...")
        second_black_line_seen = False

        # Continue return navigation: detect obstacles continuously,
        # slow down at the second black line, and stop at obstacle after it
        while not stop_event.is_set():

            position = retry(line_follower.position)
            if position == "black" and not second_black_line_seen:
                second_black_line_seen = True
                print("Second black line encountered on return: slowing down.")

            # Check for obstacles using the I2C sensor
            distance = read_obstacle_distance(distance_sensor)
            print(f"Obstacle sensor: {distance} cm")

            if is_obstacle_close(distance):
                if second_black_line_seen:
                    # Final stop at obstacle after the second black line for UR arm reload
                    print(
                        f"Obstacle detected at {distance} cm after second black line! "
                        "Stopping for accurate UR arm position."
                    )
                    gpg.stop()
                    handle_obstacle(gpg, buzzer)
                    gpg.stop()
                    returned_to_pickup_callback(table_id)
                    return True
                else:
                    # Before the second black line: handle obstacle and wait until cleared
                    if not wait_until_obstacle_cleared(
                        gpg, distance_sensor, buzzer, stop_event
                    ):
                        return False
                    continue

            # Follow the black line (slower once second black line is encountered)
            active_speed = RETURN_LINE_SPEED if second_black_line_seen else config.SPEED
            if not follow_line_proportional(gpg, line_follower, speed=active_speed):
                gpg.forward()

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

    TABLE_ID = 2

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
        print(f"Starting navigation test for table {TABLE_ID}")

        success = navigation(
            gpg,
            line_follower,
            distance_sensor,
            buzzer,
            cup_distance_sensor,
            TABLE_ID,
            stop_event,
            cup_removed_callback=lambda table_id: print(
                f"TEST: Cup removed from table {table_id}"
            ),
            returned_to_pickup_callback=lambda tid: print(
                f"TEST: Returned to pickup point for table {tid}"
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