from gpiozero import AngularServo
from time import sleep

#Define the servo connected to GPIO 18
#Adjust min/max pulse widths if the servo doesn't achieve full rotation
servo = AngularServo(13, min_pulse_width=0.0006, max_pulse_width=0.0024) 

while True:
    servo.angle = 90  # Move to 90 degrees
    sleep(2)
    servo.angle = 0   # Move to 0 degrees
    sleep(2)
    servo.angle = -90 # Move to -90 degrees
    sleep(2)