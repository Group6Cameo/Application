from adafruit_servokit import ServoKit

kit = ServoKit(channels=16)

kit.servo[0].set_pulse_width_range(400, 2600)
kit.servo[1].set_pulse_width_range(400, 2600)
kit.servo[2].set_pulse_width_range(400, 2600)
kit.servo[3].set_pulse_width_range(400, 2600)

def set_arm_position(angle):
    """Linked control for servo2 & servo3, so that when servo3 moves forward,
    servo2 moves backward. The 'angle' must be between 0 and 180."""
    if angle < 0 or angle > 180:
        raise ValueError("Angle must be between 0 and 180 degrees.")
    kit.servo[3].angle = angle
    kit.servo[2].angle = 180 - angle

kit.servo[0].angle = 90

set_arm_position(90)
