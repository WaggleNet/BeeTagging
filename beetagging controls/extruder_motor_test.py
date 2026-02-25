import time, serial

PORT = "COM5"
BAUD = 115200   # or 250000 if needed

def send(ser, cmd):
    ser.write((cmd + "\n").encode("ascii"))
    print(">>", cmd)
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print("<<", line)
        if line.startswith("ok"):
            break

with serial.Serial(PORT, BAUD, timeout=2) as ser:
    time.sleep(2)
    ser.reset_input_buffer()

    send(ser, "G28")   # home all axes
    send(ser, "M302 S0")
    send(ser, "T1")
    send(ser, "G1 E10 F300")
    #send(ser, "M18") #disable motors
    #send(ser, "M17 E")