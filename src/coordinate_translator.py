import cv2
import numpy as np


"""
    We are creating a matrix that will help translate virtual coordinates
    into real ones. We do this with the getPerspectiveTransform that uses 
    SVD to create a matrix that will help us convert virtual coordinates to 
    real ones. 
"""

"""
Real world coordinates of the printer bed in mm.
We need to change these numbers to match the actual dimensions of the printer bed

We are trying to align the pixels in the camera to the dimensions of the printer bed
for orientation. 

This script will output a matrix that, when multiplied by the pixel where the thorax 
is located, should give directions to it. 
"""
# REAL WORLD COORDINATES (in millimeters)
# Order: Top-Left, Top-Right, Bottom-Right, Bottom-Left
#replace with printer bed dimensions
REAL_POINTS = np.float32([
    [0, 0],       # Top-Left 
    [200, 0],     # Top-Right
    [200, 200],   # Bottom-Right
    [0, 200]      # Bottom-Left
])
# ---------------------

# we store the 4 points selected on the camera here
# should be the virtual outline of the printing bed
pixel_points = []
test_points = []
matrix = None           
mode = "CALIBRATE" 
calibration_pixels = [] 

def mouse_handler(event, x, y, flags, params):
    global matrix, mode, calibration_pixels, test_points

    if event == cv2.EVENT_LBUTTONDOWN:
        # calibration
        if mode == "CALIBRATE":
            calibration_pixels.append((x, y))
            if len(calibration_pixels) == 4:
                src_pts = np.float32(calibration_pixels)
                dst_pts = REAL_POINTS
                matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
                mode = "TEST"

        # testing
        elif mode == "TEST":
            point = np.array([[[x, y]]], dtype="float32")
            result = cv2.perspectiveTransform(point, matrix)
            real_x = result[0][0][0]
            real_y = result[0][0][1]
            
            # Save the test point so it stays on screen
            test_points.append((x, y, real_x, real_y))
            print(f"Measured: {real_x:.1f}mm, {real_y:.1f}mm")

cap = cv2.VideoCapture(0)
cv2.namedWindow("BeeSee Bed")
cv2.setMouseCallback("BeeSee Bed", mouse_handler)

while True:
    ret, frame = cap.read()
    if not ret: break

    # --- DRAWING SECTION--- this runs every frame
    
    #  Draw Green Calibration Circles
    for i, pt in enumerate(calibration_pixels):
        cv2.circle(frame, pt, 5, (0, 255, 0), -1) # Green Dot
        # Connect them with lines to visualize the box
        if i > 0:
            cv2.line(frame, calibration_pixels[i-1], pt, (0, 255, 0), 2)
        if i == 3: # Close the box
            cv2.line(frame, calibration_pixels[3], calibration_pixels[0], (0, 255, 0), 2)

    #Draw Red Test Points (if any exist)
    for (tx, ty, rx, ry) in test_points:
        cv2.circle(frame, (tx, ty), 5, (0, 0, 255), -1) # Red Dot
        label = f"{rx:.0f},{ry:.0f}"
        cv2.putText(frame, label, (tx+10, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

    # Status Text
    if mode == "CALIBRATE":
        cv2.putText(frame, f"Click Corners: {len(calibration_pixels)}/4", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "TEST MODE: Click to Measure", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("BeeSee Bed", frame)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    elif key == ord('r'): # Reset everything
        calibration_pixels = []
        test_points = []
        mode = "CALIBRATE"

cap.release()
cv2.destroyAllWindows()


    
