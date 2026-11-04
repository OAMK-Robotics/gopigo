Below are our steps on integrating the GopiGo to our overall project.
Our GopiGo's role is to act as the bar's waiter and pass drinks around the table to two different customers.

We are testing line following and obstacle avoidance. 
merged.py combines our original line following code, tested in the demo week, with obstacle avoidance skills.
It can follow a black line on a white surface and can stop and reverse slightly, when it detects an obstacle.
We also added a beeper which allows the GopiGo to beep when stopped to alert customers or staff in our scenario, that an object may be in the way of the robot's path.

Smooth_line_following.py is an promising optimised version of our line following and preforms smoother turns than our other program.

turn.py is a program that can detect a split in the path of the black line and uses true/false to turn left or right. We can use this to decide on which customer the robot will go towards.
