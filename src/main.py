import argparse

import cv2


def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    camera = cv2.VideoCapture("/dev/video11")


if __name__ == "__main__":
    main()
