# Light and motor imports
from blinkt import set_pixel, show, set_all
from dual_g2_hpmd_rpi import motors
import time

# Light class
class lights:
    # Shows direction and speed of the motors through 10 neopixels
    class drive:
        # Sets up the side for the lights
        def __init__(self, side):
            if side == 'left':
                self.MIN = 0
                self.MAX = 4
                self.DIF = -1
            else:
                self.MIN = 5
                self.MAX = 9
                self.DIF = 1
            self.DIM = 1.09
            self.times_called = 480
            self.pixel_bright = self.MIN

        # Changes speed and brightness of the lights to reflect the
        # speed of the motor
        def pulse_direction(self, direction, bright, speed, r=0, g=0, b=0):
            # Change r to g or b for a different background colour
            r = int(bright-bright/self.DIM)
            # Sets the background colour
            for led in range(self.MIN, self.MAX+1):
                set_pixel(led, r, g, b)
            # Change number for different light movement speed
            self.times_called = self.times_called-25
            # Changes position of the brightest LED
            if self.times_called < abs(speed):
                # Moves the light in the correct direction
                self.pixel_bright = self.pixel_bright+(direction*self.DIF)
                # Loops the light around
                if self.pixel_bright < self.MIN:
                    self.pixel_bright = self.MAX
                elif self.pixel_bright > self.MAX:
                    self.pixel_bright = self.MIN
                # Resets count
                self.times_called = 480
            # Change r to g or b for a different bright light colour
            r = bright
            # Sets the 'bright pixel'
            set_pixel(self.pixel_bright, r, g, b)

        # Decides direction and how bright the light should be
        def pulse(self, speed):
            # Magic number is 255(light range) into 480(motor range)
            bright = int(abs(speed)/1.88235294118)
            # Limits the brightness
            if bright > 255:
                bright = 255
            # Direction control
            if speed < 0:
                self.pulse_direction(-1, bright, speed)
            else:
                self.pulse_direction(1, bright, speed)

    # Sets up sides
    def __init__(self):
        self.left = self.drive('left')
        self.right = self.drive('right')

    # Stops lights
    def stop(self):
        self.show_speed(0, 0)

    # Flashes twice with a delay
    def flash(self, colour, bright, bright2):
        r, g, b = colour
        set_all(r, g, b, bright)
        show()
        time.sleep(0.05)
        set_all(0,0,0)
        show()
        time.sleep(0.05)
        set_all(r, g, b, bright2)
        show()
        time.sleep(0.05)
        set_all(0,0,0)
        show()

    # Sets left and right speed
    def show_speed(self, left_speed, right_speed):
        self.left.pulse(left_speed)
        self.right.pulse(right_speed)


lights = lights()   # Sets up the lights class for the motors

# Drives motors for autonomous and direct drive
class Motors:
    # Sets up motors for autonomous drive
    def __init__(self, MID=0, base_speed=0, turn_speed=0, speed_adj=0):
        self.MID = MID
        self.base_speed = base_speed
        self.turn_speed = turn_speed
        self.speed_adj = speed_adj
        motors.enable()

    # If you want to stop the motors from working call this
    def disable(self):
        motors.disable()

    # Stops motors and lights
    def stop(self):
        motors.motor1.setSpeed(0)
        motors.motor2.setSpeed(0)
        print('stop')
        lights.stop()

    # Flashes the up sequence
    def speed_up(self):
        lights.flash((0, 0, 255), 255, 100)

    # Flashes the down sequence
    def speed_down(self):
        lights.flash((0, 255, 0), 100, 255)

    # Motors and lights at a speed
    def motors(self, left, right):
        print('Left:   ', left)
        print('Right:  ', right)
        motors.motor1.setSpeed(left)
        motors.motor2.setSpeed(right)
        lights.show_speed(left, right)
        show()  # Shows lights

    # Handles direct motor values or autonomous inputs
    def drive(self, left, right=0, intense='s'):
        try:
            # Direct driving
            self.motors(left, right)
        except:
            # Autonomous driving commands
            # Left turn
            if left is 'left':
                self.motors(self.turn_speed, 0)
            # Right turn
            elif left is 'right':
                self.motors(0, self.turn_speed)
            # aligns to a x position (designed for my line following library
            elif left is 'allign':
                x = right
                if abs(x-self.MID) < 17 and intense == 's':
                    # Non-extreme handling
                    # Motor adjustment based on x position
                    left = self.base_speed-int((self.MID-x)/self.speed_adj)
                    right = self.base_speed+int((self.MID-x)/self.speed_adj)
                    # Speed changer based on x position
                    self.motors(left, right)
                else:
                    # Extreme handling
                    if x < self.MID:
                        self.drive('right')
                    else:
                        self.drive('left')
            elif left is 'stop':
                self.stop()