from __future__ import division
from __future__ import print_function
from approxeng.input.selectbinder import ControllerResource
import Base
from time import sleep

motors = Base.Motors()   # Motor driving class

# Try to import line following
def fail(meh):
    pass
try:
    import line_follow
    line_follow = line_follow.line
except:
    line_follow = fail

# Parameters
MAX = 480
MIN = 100
pwm = 480

while True:
    try:
        # Sets up controller
        with ControllerResource(dead_zone=0.1, hot_zone=0.2) as joystick:
            # Main control loop, controls motors of left joystick
            # and changes to different modes through the right hand buttons.
            while True:
                joystick.check_presses()   # Checks key presses
                # Speed hotkeys
                if 'r1' in joystick.presses:
                    pwm = 150
                    print('speed limit is:  ', round(pwm))
                    motors.stop()
                    motors.speed_down()
                elif 'r2' in joystick.presses:
                    pwm = 480
                    print('speed limit is:  ', round(pwm))
                    motors.stop()
                    motors.speed_up()
                # Changes modes to line following
                if 'circle' in joystick.presses:
                    print('line starting...')
                    line_follow(joystick)
                # Gets joystick data
                yaw, throttle, side, accelerator = joystick['lx', 'ly', 'rx', 'ry']
                # Handles finer speed control
                if accelerator != 0:
                    pwm = pwm + accelerator
                    if pwm < MIN:
                        pwm = MIN
                    elif pwm > MAX:
                        pwm = MAX
                    print('speed limit is:  ', round(pwm))
                # Turns joystick values into motor values
                right = round((throttle - yaw) * pwm)
                left = round((throttle + yaw) * pwm)
                motors.drive(left, right)   # Drives motors and lights
                sleep(0.005)
    except IOError:
        # We get an IOError when using the ControllerResource if we don't have
        # a controller yet, so in this case we just wait a second and try
        # again after printing a message.
        print('No controller found yet')
        sleep(1)
