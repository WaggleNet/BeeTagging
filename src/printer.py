"""
3D printer control via GCODE.
"""

import time

import serial


class Printer:
    def __init__(self, port):
        self.ser = serial.Serial(port, 115200, timeout=2)

    def close(self):
        self.ser.close()

    def send(self, cmd, delay=1):
        acc_res = {'wait'}
        self.ser.write((cmd + "\n").encode())
        # self.ser.write(b"M400\n")  # Wait for moves to finish
        print(f"Sent: {cmd}")
        time.sleep(delay)
        while (True ):
            res = self.ser.readline().decode().strip()
            print(f"Response: {res}")
            if (res in acc_res): break

    def move(self, x, y, z, speed=5000):
        cmd = f"G1 X{x} Y{y} Z{z} F{speed}"
        self.send(cmd)
        # self.send("M400")

    def home(self):
        self.send("G28")

    def init(self):
        self.send("M17")
        self.home()
        self.move(0, 0, 30)


def tag_bee(printer: Printer):
    # printer.move(0, 0, 30)

    # Tag
    printer.move(15, 200, 30)
    printer.move(15, 200, 16)
    printer.move(15, 200, 30)

    # Edge trace
    printer.move(0, 200, 30)
    printer.move(0, 200, 30)
    printer.move(200, 200, 30)
    printer.move(200, 10, 30)
    printer.move(10, 10, 30)
    printer.move(10, 10, 30)

    # Idle
    printer.move(0, 0, 30)


# y=200: bed all the way front
# y=10: nozzle at front of bed
# x=200: printer limit, still a bit behind edge
# tag: approx x = (1, 33) y = (184, limit)
# z=16: tag bed
# z=15: barely clears edge
# z=30: clears glue syringe and stuff
# z=0: at bed level
