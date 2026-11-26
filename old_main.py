import time
import init
import fun
import config

def main():
    gpg, line_follower, distance_sensor, buzzer = init.initialize_robot()

    gpg.set_speed(config.SPEED)
    gpg.forward()

    # True for right branch selection, False for left branch selection
    choose_right_branch = True

    try:
        while True:
            dist = distance_sensor.read()

            if dist > config.SAFETY_DISTANCE_MM:
                p = fun.follow_line_proportional(gpg, line_follower)

                # Triggered when a fork is detected (outside the -5 to 5 range)
                if not (-5 <= p <= 5):
                    
                    # --- SELECT THE FUNCTION TO TEST HERE (Uncomment the one you want to use) ---
                    
                    # Option 1: Smooth (with proportional line following)
                    fun.navigate_fork_smooth(gpg, line_follower, turn_right=choose_right_branch)
                    
                    # Option 2: Jerky (from the first code using direct gpg.left/right commands)
                    # fun.navigate_fork_jerky(gpg, line_follower, turn_right=choose_right_branch)

                time.sleep(0.1)
            else:
                fun.handle_obstacle(gpg, buzzer)
                line_follower.position()  # Reset sensor state after stopping

    except KeyboardInterrupt:
        pass
    finally:
        gpg.stop()


if __name__ == "__main__":
    main()