import easygopigo3 as easy
import time

sensor_readings = None
gpg = easy.EasyGoPiGo3()
sensor = gpg.init_distance_sensor("I2C")

#led_signal = gpg.init_led("AD2")
my_buzzer = gpg.init_buzzer("AD1")

try:
    my_linefollower = gpg.init_line_follower()
    time.sleep(0.1)
except:
    print('Line Follower not responding')
    time.sleep(0.2)
    exit()

sensor = gpg.init_distance_sensor("I2C")
# create the LED instance, passing the port and gpg
#led_signal = gpg.init_led("AD2")
my_buzzer = gpg.init_buzzer("AD1")

gpg.set_speed(200)

try:
    while True:
        dist = sensor.read()

        if dist > 10:
            # line following (inside the obstacle loop)
            line_pos = my_linefollower.position()
            if line_pos == "black":
                break
            elif line_pos == 'center':
                gpg.forward()
            elif line_pos == 'left':
                gpg.left()
            elif line_pos == 'right':
                gpg.right()
            time.sleep(0.1)  # don't poll sensor too quickly
        else:
            # obstacle avoidance
            my_buzzer.sound_on()
            gpg.stop()
            #led_signal.light_max()

            time.sleep(0.5)

            my_buzzer.sound_off()
            time.sleep(0.5)
            #led_signal.light_off()
            gpg.backward()
            time.sleep(0.5)
            gpg.stop()
            gpg.turn_degrees(105)
            gpg.stop()
            time.sleep(1)

except KeyboardInterrupt:
    pass
finally:
    gpg.stop()
