import time
import config

def handle_obstacle(gpg, buzzer):
    """Executes obstacle avoidance behavior (buzzer sound, stopping, backing up)."""
    buzzer.sound_on()
    gpg.stop()
    time.sleep(0.5)

    buzzer.sound_off()
    time.sleep(0.5)

    gpg.backward()
    time.sleep(0.5)
    gpg.stop()
    time.sleep(5)


def follow_line_proportional(gpg, line_follower):
    """Performs proportional line following based on the sensor position value."""
    p = line_follower.position_val() - config.P_CENTER_OFFSET

    if -5 <= p <= 5:
        gpg.set_motor_dps(gpg.MOTOR_LEFT, config.SPEED + p * config.P_GAIN)
        gpg.set_motor_dps(gpg.MOTOR_RIGHT, config.SPEED - p * config.P_GAIN)
    return p


def navigate_fork_smooth(gpg, line_follower, turn_right=True):
    """Fork navigation (SMOOTH): Drives smoothly using proportional line following until reaching the junction."""
    gpg.forward()

    while line_follower.position() != "white":
        follow_line_proportional(gpg, line_follower)
        time.sleep(0.05)

    gpg.stop()
    turn_angle = 45 if turn_right else -45
    gpg.turn_degrees(turn_angle, blocking=True)


def navigate_fork_jerky(gpg, line_follower, turn_right=True):
    """Fork navigation (DIRECT/JERKY): Uses direct gpg.left/right commands from the first code version."""
    gpg.forward()

    while line_follower.position() != "white":
        line_pos = line_follower.position()
        if line_pos == 'center':
            gpg.forward()
        elif line_pos == 'left':
            gpg.left()
        elif line_pos == 'right':
            gpg.right()
        time.sleep(0.1)

    gpg.stop()
    turn_angle = 45 if turn_right else -45
    gpg.turn_degrees(turn_angle, blocking=True)