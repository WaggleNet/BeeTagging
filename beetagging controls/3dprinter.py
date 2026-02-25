import time, serial
from gpiozero import AngularServo
from stepper_1 import move_stepper

#set port and baud rate
PORT = "COM5"
BAUD = 115200   # or 250000 if needed

servo = AngularServo(13, min_pulse_width=0.0006, max_pulse_width=0.0024) #we using gpio pin 13
#use: servo.angle = DEGREES

def send(ser, cmd):
    ser.write((cmd + "\n").encode("ascii"))
    print(">>", cmd)
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print("<<", line)
        if line.startswith("ok"):
            break


def home():
    send(ser, "G28")   # home all axes
    send(ser, "M400")
    send(ser, "M114") # report position

def getTag(x, y): #x,y are offsets
    move(1+x, 75+y, 0, 10000) #move to tag position + offset
    move_stepper(512, delay=0.002)
    #tagappON()
    #TO DO: turn the glue dispenser on/off to dispense enough glue (a little) and then retract the linear actuator

def getGlue():
    move() #TO DO: Set to position of glue dispenser
    #TO DO: dip into glue (slowly) and retract 

def tagBee():
    #TO DO: get position of bee from software team
    move() #TO DO: set to position of bee given by software team
    move_stepper(512, delay=0.002)
    #TO DO: tag bee
    #tagappOFF()

def move(x, y, z, speed):
    send(ser, "G0 F" + speed + " X" + x + " Y" + y + " Z" + z)
    send(ser, "M400") #wait for all moves to finish

"""
def tagappON():
    send(ser, "M106") #turn fan motor on
    send(ser, "M400")

def tagappOFF():
    send(ser, "M107") #turn fan motor off
    send(ser, "M400")

def tagging_sequence(x, y): #x,y are offsets for tag
    getTag(x,y)
    getGlue()
    tagBee()
"""

#experiment with exact movements and speeds!!!

with serial.Serial(PORT, BAUD, timeout=2) as ser:
    time.sleep(2)
    ser.reset_input_buffer()

    #home()
    send(ser, "M115")
    send(ser, "M302 P1")
    send(ser, "G0 E10 F150")
    """
    send(ser, "M17") 
    send(ser, "M400")
    send(ser, "M701 L100 Z100")
    send(ser, "G0 E1 F150")
    """
    """
    time.sleep(1)
    send(ser, "G1 E10 F150")
    time.sleep(3)
    send(ser, "G1 E-10 F150" )
    time.sleep(1)
    """
    send(ser, "M18")

    """
    i = 0
    j = 0

    home()
    if(True):
        tagging_sequence()
        if(i < 11):
            i = i + 1
        else:
            i = 0
            j = j + 1
    else:
        home()
    """

    """
    home()

    #move to 100, 100, 0
    move(100, 100, 100, 10000)  # set current position as 0,0,0
    send(ser, "M114")  # report position
    send(ser, "M400")

    time.sleep(2)

    #move to 0, 0, 0
    move(0,0,0,10000)
    send(ser, "M114")
    send(ser, "M400")

    #suck a tag
    getTag(0,0,10)
    """