import easygopigo3 as easy
import time

# Initialize GoPiGo3
gpg = easy.EasyGoPiGo3()

# Initialize devices
ultrasonic = gpg.init_ultrasonic_sensor("AD2")
buzzer = gpg.init_buzzer("AD1")

# Configuration
REMOVAL_DELTA_CM = 5
CHECK_INTERVAL = 0.2
CONFIRMATION_COUNT = 3

# Measure initial cup distance
print("Measuring cup position...")

readings = []

for _ in range(10):
    distance = ultrasonic.read()

    if distance > 0:
        readings.append(distance)

    time.sleep(0.2)

if not readings:
    raise RuntimeError("Could not detect cup!")

cup_distance = sum(readings) / len(readings)

print(f"Cup detected at {cup_distance:.1f} cm")
print("Waiting for cup removal...")

removal_count = 0
cup_removed = False

try:
    while True:
        distance = ultrasonic.read()

        if distance > cup_distance + REMOVAL_DELTA_CM:
            removal_count += 1
        else:
            removal_count = 0

        # Confirm cup removal
        if removal_count >= CONFIRMATION_COUNT and not cup_removed:
            print("Cup removed!")

            buzzer.sound_on()
            time.sleep(1)
            buzzer.sound_off()

            cup_removed = True

        # Re-arm when cup is returned
        if cup_removed and distance <= cup_distance + 2:
            print("Cup returned!")
            cup_removed = False
            removal_count = 0

        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print("Stopping...")

finally:
    buzzer.sound_off()
    gpg.stop()