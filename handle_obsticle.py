import time
import easygopigo3 as easy
from init import initialize_robot

def handle_obstacle(gpg, buzzer):
    """Executes obstacle avoidance behavior (buzzer sound, stopping, backing up)."""
    gpg = easy.EasyGoPiGo3()
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



def distance(gpg, distance_sensor):
    while True:
        dist = distance_sensor.read()
        if dist > 10:
            break
        else:
            handle_obsticle(gpg, buzzer)



if __name__ == "__main__":
    gpg = easy.EasyGoPiGo3()
    buzzer = gpg.init_buzzer("AD1")
    distance_sensor = gpg.init_distance_sensor("12C")
    distance(gpg, distance_sensor)
