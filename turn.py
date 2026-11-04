import easygopigo3 as easy
import time

sensor_readings = None
gpg = easy.EasyGoPiGo3()
try:
    my_linefollower = gpg.init_line_follower()
    time.sleep(0.1)
    sensor = gpg.init_distance_sensor("I2C")
    time.sleep(0.1)
    my_buzzer = gpg.init_buzzer("AD1")
except:
    print('Line Follower not responding')
    print('Distance sensor not responding')
    print('Buzzer not responding')
    time.sleep(0.2)
    exit()

# start
gpg.forward()
while not  my_linefollower.position() == "black":
    line_pos = my_linefollower.position()
    if line_pos == 'center':
        gpg.forward()
    elif line_pos == 'left':
        gpg.left()
    elif line_pos == 'right':
        gpg.right()
    time.sleep(0.1) # don't poll sensor too quickly
gpg.stop()
if False:
    gpg.forward()
    while not  my_linefollower.position() == "white":
        line_pos = my_linefollower.position()
        if line_pos == 'center':
            gpg.forward()
        elif line_pos == 'left':
            gpg.left()
        elif line_pos == 'right':
            gpg.right()
        time.sleep(0.1) # don't poll sensor too quickly
    gpg.stop()
    gpg.turn_degrees(-45, blocking=True)
else:
    gpg.forward()
    while not  my_linefollower.position() == "white":
        line_pos = my_linefollower.position()
        if line_pos == 'center':
            gpg.forward()
        elif line_pos == 'left':
            gpg.left()
        elif line_pos == 'right':
            gpg.right()
        time.sleep(0.1) # don't poll sensor too quickly
    gpg.stop()
    gpg.turn_degrees(45, blocking=True)
