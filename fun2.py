import time
import config


def retry(fn, retries=10, delay=0.02):
    """Call a sensor read function; retry on transient I2C errors."""
    last = None
    for _ in range(retries):
        try:
            return fn()
        except OSError as e:      # periphery's I2CError is an OSError
            last = e
            time.sleep(delay)
    raise last                    # still failing after all retries


def turn_around(gpg):
    
    try:
        gpg.set_speed(200)
        time.sleep(0.1)    
        gpg.stop()
        time.sleep(0.5)
        gpg.backward()
        time.sleep(0.5)
        gpg.stop()
        gpg.turn_degrees(190)
        gpg.stop()
        time.sleep(0.1)
    

    except KeyboardInterrupt:
        pass
    finally:
        gpg.stop()

def stop_at_table(gpg, line_follower):
    """Stops when the destination marker is detected."""

    position = line_follower.position()

    if position == "black":
        print("Black marker detected!")
        gpg.stop()
        return True

    return False

def handle_obstacle(gpg, buzzer):
    """Executes obstacle avoidance behavior (buzzer sound, stopping, backing up)."""
    try:
        gpg.stop()
        buzzer.sound_on()
        time.sleep(0.5)
        buzzer.sound_off()
        time.sleep(0.5)
        gpg.stop()

        print("Obstacle handling completed.")
        return True

    finally:
        gpg.stop()
        buzzer.sound_off()

def follow_line_proportional_old(gpg, line_follower):
    """Performs proportional line following based on the sensor position value."""
    p = line_follower.position_val() - config.P_CENTER_OFFSET

    print(f"Position value: {line_follower.position_val()}, error: {p}")

    if -5 <= p <= 5:
        gpg.set_motor_dps(gpg.MOTOR_LEFT, config.SPEED + p * config.P_GAIN)
        gpg.set_motor_dps(gpg.MOTOR_RIGHT, config.SPEED - p * config.P_GAIN)

    return p


def follow_line_proportional(gpg, line_follower):
    """Performs proportional line following with I2C error handling."""

    try:
        position = line_follower.position_val()
        p = position - config.P_CENTER_OFFSET

        print(f"Position value: {position}, error: {p}")

        if -5 <= p <= 5:
            left_speed = config.SPEED + p * config.P_GAIN
            right_speed = config.SPEED - p * config.P_GAIN

            gpg.set_motor_dps(gpg.MOTOR_LEFT, left_speed)
            gpg.set_motor_dps(gpg.MOTOR_RIGHT, right_speed)

        return True

    except OSError as error:
        if error.errno == 5:
            print("I2C communication error. Retrying...")
            gpg.stop()
            time.sleep(0.2)
            return False

        raise

def follow_line_proportional_2(gpg, line_follower):
    """Performs proportional line following with I2C error handling."""

    try:
        position = line_follower.position_val()
        p = position - config.P_CENTER_OFFSET

        print(f"Position value: {position}, error: {p}")

        if -5 <= p <= 5:
            left_speed = config.SPEED + p * config.P_GAIN
            right_speed = config.SPEED - p * config.P_GAIN

            gpg.set_motor_dps(gpg.MOTOR_LEFT, left_speed)
            gpg.set_motor_dps(gpg.MOTOR_RIGHT, right_speed)

        return True

    except OSError as error:
        if error.errno == 5:
            print("I2C communication error. Retrying...")
            gpg.stop()
            time.sleep(0.2)
            return False

        raise

def navigate_fork_smooth(gpg, line_follower, turn_right=True):
    """Fork navigation (SMOOTH): Drives smoothly using proportional line following until reaching the junction."""
    gpg.forward()

    while line_follower.position() != "white":
        follow_line_proportional(gpg, line_follower)
        time.sleep(0.05)

    gpg.stop()
    turn_angle = 90 if turn_right else -90
    gpg.turn_degrees(turn_angle, blocking=True)

def navigate_fork_smooth2(
    gpg,
    line_follower,
    turn_direction,
    stop_event=None
):
    """Follows the black line and turns at the junction."""

    line_detected = False

    try:
        print("Approaching junction...")
        gpg.forward()

        while True:

            if stop_event and stop_event.is_set():
                return False

            position = line_follower.position()

            if position == "black":
                print("All black detected.")
                gpg.stop()
                return True

            if position == "white" and line_detected:
                print("Junction reached!")
                gpg.stop()

                if turn_direction == "right":
                    turn_angle = 90
                elif turn_direction == "left":
                    turn_angle = -90
                else:
                    print(f"Invalid turn direction: {turn_direction}")
                    return False

                print(f"Turning {turn_direction} ({turn_angle} degrees)...")
                gpg.turn_degrees(turn_angle, blocking=True)

                return True

            elif position != "white":
                line_detected = True

            follow_line_proportional(gpg, line_follower)
            time.sleep(0.05)

    finally:
        gpg.stop()

#buzzer removed from params
def wait_for_cup_removal(cup_distance_sensor, stop_event):
    """
    Waits until the cup is removed.
    Activates the buzzer when removal is detected.
    Returns True if the cup was removed, False if stopped.
    """
    # Detection settings
    CHECK_INTERVAL = 0.2
    REMOVAL_THRESHOLD = 5
    CONFIRMATION_COUNT = 3
    INVALID_READING_LIMIT = 3 
    NO_ECHO_COUNTS_AS_REMOVAL = True

    print("Waiting for cup removal...")
    # Measure the initial distance while the cup is present
    readings = []

    for i in range(5):
        if stop_event.is_set():
            return False
        distance = cup_distance_sensor.read()
        print(f"Initial reading {i + 1}: {distance} cm", flush=True)
        if distance > 0:
            readings.append(distance)
        stop_event.wait(CHECK_INTERVAL)
    if not readings:
        print("Could not measure the cup!")
        return False

    cup_distance = sum(readings) / len(readings)
    print(f"Initial cup distance: {cup_distance:.1f} cm")
    removal_count = 0
    invalid_reading_count = 0

    while not stop_event.is_set():
        distance = cup_distance_sensor.read()
        if distance <= 0:
            # Sensor didn't receive a valid echo
            invalid_reading_count += 1
            removal_count = 0
            if (
                invalid_reading_count >= INVALID_READING_LIMIT
                and NO_ECHO_COUNTS_AS_REMOVAL
            ):
                print("Cup removal detected (no valid echo).")
                #buzzer.sound_on()
                stop_event.wait(2)
                #buzzer.sound_off()
                return not stop_event.is_set()
        else:
            invalid_reading_count = 0
            if distance > cup_distance + REMOVAL_THRESHOLD:
                removal_count += 1
            else:
                removal_count = 0
            if removal_count >= CONFIRMATION_COUNT:
                print("Cup removed!")
                #buzzer.sound_on()
                stop_event.wait(2)
                #buzzer.sound_off()
                return not stop_event.is_set()
        stop_event.wait(CHECK_INTERVAL)
    #buzzer.sound_off()
    return False

