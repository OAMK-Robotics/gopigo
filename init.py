import time
import easygopigo3 as easy

def initialize_robot():
    """Initializes the GoPiGo3 sensors and motors, exiting the program if errors occur."""
    try:
        gpg = easy.EasyGoPiGo3()
        line_follower = gpg.init_line_follower()
        time.sleep(0.1)
        distance_sensor = gpg.init_distance_sensor("I2C")
        time.sleep(0.1)
        buzzer = gpg.init_buzzer("AD1")
        time.sleep(0.1)
        return gpg, line_follower, distance_sensor, buzzer
    except Exception as e:
        print(f"Hardware initialization failed: {e}")
        print("Line Follower, Distance Sensor, or Buzzer are not responding")
        exit()