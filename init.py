
import time
import easygopigo3 as easy


def initialize_robot():
    """Initializes the GoPiGo3 sensors and motors."""

    try:
        print("Creating EasyGoPiGo3 instance...", flush=True)
        gpg = easy.EasyGoPiGo3()
        print("GoPiGo3 initialized.", flush=True)

        print("Initializing line follower...", flush=True)
        line_follower = gpg.init_line_follower()
        time.sleep(0.1)
        print("Line follower initialized.", flush=True)

        print("Initializing I2C distance sensor...", flush=True)
        distance_sensor = gpg.init_distance_sensor("I2C")
        time.sleep(0.1)
        print("Distance sensor initialized.", flush=True)
        print(f"Front distance sensor object: {distance_sensor}", flush=True)

        if distance_sensor is None:
            raise RuntimeError("Front distance sensor (I2C) initialization returned None!")

        print("Initializing buzzer on AD1...", flush=True)
        buzzer = gpg.init_buzzer("AD1")
        time.sleep(0.1)
        print("Buzzer initialized.", flush=True)

        print("Initializing distance sensor for cup detection on AD2...", flush=True)
        cup_distance_sensor = gpg.init_ultrasonic_sensor("AD2")
        time.sleep(0.1)
        print(f"Cup sensor object: {cup_distance_sensor}", flush=True)

        if cup_distance_sensor is None:
            raise RuntimeError("Cup distance sensor initialization returned None!")

        print("All hardware initialized successfully!", flush=True)

        return (
            gpg,
            line_follower,
            distance_sensor,
            buzzer,
            cup_distance_sensor
        )

    except Exception as e:
        print(f"Hardware initialization failed: {e}", flush=True)
        raise

