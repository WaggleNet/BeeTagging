"""
3D printer control via GCODE.
"""

import time

import serial

PORT = "/dev/ttyUSB0"


class Printer:
    def __init__(self):
        self.ser = serial.Serial(PORT, 115200, timeout=2)

    def send(self, cmd, delay=1):
        self.ser.write((cmd + "\n").encode())
        print(f"Sent: {cmd}")
        time.sleep(delay)

        res = self.ser.readline().decode().strip()
        print(f"Response: {res}")

    def move(self, x, y, z, speed=5000):
        cmd = f"G1 X{x} Y{y} Z{z} F{speed}"
        self.send(cmd)

    def home(self):
        self.send("G28")
