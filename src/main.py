import argparse
import os

import cv2

from coord_conv import pixel_to_real as convert_coord
from printer import Printer, tag_bee


def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    #camera = cv2.VideoCapture("/dev/video11")

    printer = Printer("COM18")
    printer.init()
    tag_bee(printer)

    """
    if not os.path.isfile("calibration.npy"):
        raise ValueError("No calibration.npy found; run coord_conv.py")
    """

    printer.close()


if __name__ == "__main__":
    main()
