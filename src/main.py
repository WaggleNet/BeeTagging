import argparse
import os

import cv2
import numpy as np

from coord_conv import pixel_to_real as convert_coord
from printer import Printer


def ask_for_point(camera, matrix):
    """
    Dummy func to ask for point via cv2.
    Returns in mm coords.
    """
    coords = None

    def handle_mouse(event, x, y, flags, param):
        nonlocal coords
        if event == cv2.EVENT_LBUTTONDOWN:
            coords = convert_coord(x, y, matrix)
            print("Got", coords)

    first = True
    while True:
        ret, frame = camera.read()
        if not ret:
            continue
        cv2.imshow("Calibration", frame)

        if first:
            cv2.setMouseCallback("Calibration", handle_mouse)
            first = False

        if cv2.waitKey(1) == ord("q"):
            break

    return coords


def tag_bee(printer, camera, matrix):
    """
    Sequence of commands to tag bee.
    """

    while True:
        printer.move(0, 200, 30)
        printer.move(0, 200, 30)

        # TODO manually asking point.
        point = ask_for_point(camera, matrix)
        input("Press enter")
        point = [200 - point[0], point[1]]

        # Get tag.
        printer.move(15, 190, 30)
        printer.move(15, 190, 16)
        printer.move(15, 190, 30)

        # Move to point.
        printer.move(point[0], point[1], 30)
        printer.move(point[0], point[1], 0)
        printer.move(point[0], point[1], 30)


def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    camera = cv2.VideoCapture("/dev/video11")

    printer = Printer("/dev/ttyUSB0")
    printer.init()

    if not os.path.isfile("calibration.npy"):
        raise ValueError("No calibration.npy found; run coord_conv.py")
    matrix = np.load("calibration.npy")

    tag_bee(printer, camera, matrix)

    printer.close()


if __name__ == "__main__":
    main()
