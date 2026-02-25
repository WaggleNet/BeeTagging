import RPi.GPIO as GPIO
import time

IN1 = 17
IN2 = 18
IN3 = 27
IN4 = 22

pins = [IN1, IN2, IN3, IN4]

#for 28BYJ-48 stepper motor?
seq = [
    [1, 0, 0, 1],
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1]
]

GPIO.setmode(GPIO.BCM)

for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

def move_stepper(steps, delay=0.002, reverse=False):
    step_sequence = reversed(seq) if reverse else seq

    for _ in range(steps):
        for step in step_sequence:
            for pin, val in zip(pins, step):
                GPIO.output(pin, val)
            time.sleep(delay)

try:
    move_stepper(512, delay=0.002)
    time.sleep(1)
    move_stepper(512, delay=0.002, reverse=True)

finally:
    GPIO.cleanup()