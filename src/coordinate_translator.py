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


#calibration
#4 corners clicked -> build perspective transform matrix by pairing each pixel corner with its corresponding mm corner in REAL_POINTS
def try_calibrate(calibration_pixels):
    if len(calibration_pixels) == 4:
        src_pts = np.float32(calibration_pixels)
        return cv2.getPerspectiveTransform(src_pts, REAL_POINTS)
    return None

def reset_state(): #to restart calibration
    return [], [], "CALIBRATE", None
    
    
#coordinate transformation
def pixel_to_real(x, y, matrix): #takes a pixel coordinate and applies the matrix to get real-world mm coordinates back
    point = np.array([[[x, y]]], dtype="float32")
    result = cv2.perspectiveTransform(point, matrix)
    return result[0][0][0], result[0][0][1]
    
#input handling
def handle_calibrate_click(x, y, calibration_pixels):
    calibration_pixels.append((x, y))
    matrix = try_calibrate(calibration_pixels)
    if matrix is not None:
        mode = "TEST" #test mode once all 4 corners are clicked
    else:
        mode = "CALIBRATE"
    return calibration_pixels, matrix, mode
    
def handle_test_click(x, y, matrix, test_points): #converts clicked pixel to mm, printing result after storing in test_points
    real_x, real_y = pixel_to_real(x, y, matrix)
    test_points.append((x, y, real_x, real_y))
    print(f"Measured: {real_x:.1f}mm, {real_y:.1f}mm")
    return test_points
    
def mouse_handler(event, x, y, flags, params): #called on any mouse event, only acting on left clicks
    global matrix, mode, calibration_pixels, test_points
    if event == cv2.EVENT_LBUTTONDOWN:
        if mode == "CALIBRATE":
            calibration_pixels, matrix, mode = handle_calibrate_click(x, y, calibration_pixels)
        elif mode == "TEST":
            test_points = handle_test_click(x, y, matrix, test_points)
            
# drawing

def draw_calibration_points(frame, calibration_pixels): #draws green dot for corner clicks and connects with lines to visualize the calibration box
    for i, pt in enumerate(calibration_pixels):
        cv2.circle(frame, pt, 5, (0, 255, 0), -1)
        if i > 0:
            cv2.line(frame, calibration_pixels[i - 1], pt, (0, 255, 0), 2)
        if i == 3: #last corner closes the box back to first point
            cv2.line(frame, calibration_pixels[3], calibration_pixels[0], (0, 255, 0), 2)

def draw_test_points(frame, test_points): #red dots for test clicks with overlayed mm coordinates
    for (tx, ty, rx, ry) in test_points:
        cv2.circle(frame, (tx, ty), 5, (0, 0, 255), -1)
        label = f"{rx:.0f},{ry:.0f}"
        cv2.putText(frame, label, (tx + 10, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

def draw_status(frame, mode, calibration_pixels): #instruction text drawn at top of frame
#shows corner count during calibration, or "TEST MODE" once ready
    if mode == "CALIBRATE":
        cv2.putText(frame, f"Click Corners: {len(calibration_pixels)}/4", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "TEST MODE: Click to Measure", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

def draw_frame(frame, calibration_pixels, test_points, mode): #calls drawing functions in order
    draw_calibration_points(frame, calibration_pixels)
    draw_test_points(frame, test_points)
    draw_status(frame, mode, calibration_pixels)


#main loop

#camera opened, creates window, registers mouse handler
cap = cv2.VideoCapture(0)
cv2.namedWindow("BeeSee Bed")
cv2.setMouseCallback("BeeSee Bed", mouse_handler)

while True: #each iteration reads frame, draws on it, and displays it
    ret, frame = cap.read()
    if not ret:
        break

    draw_frame(frame, calibration_pixels, test_points, mode)
    cv2.imshow("BeeSee Bed", frame)

    key = cv2.waitKey(1)
    if key == ord('q'): #to quit
        break
    elif key == ord('r'): #to reset
        calibration_pixels, test_points, mode, matrix = reset_state()
#cleanup
cap.release()
cv2.destroyAllWindows()
