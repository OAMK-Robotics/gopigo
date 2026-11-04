import easygopigo3 as easy
import time

robot = easy.EasyGoPiGo3()
sensor = robot.init_line_follower()
SPEED = 200

try:
    for i in range(500):
        p = sensor.position_val()-5
        print("Line:", p)
        if -5 <= p <= 5:
            robot.set_motor_dps(robot.MOTOR_LEFT, SPEED+p*30)
            robot.set_motor_dps(robot.MOTOR_RIGHT, SPEED-p*30)
        else:
            break
        time.sleep(0.05)
    robot.stop()
finally:
    print("Program finished!")