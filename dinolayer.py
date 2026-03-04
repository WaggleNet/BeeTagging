"""
Run thorax detection on frames of a video, randomly pick ONE thorax on the first
frame, and track that same bee across subsequent frames.

Press 'q' to quit. Press 'r' to re-seed and re-pick on the next frame.
"""

import os
import sys
import time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import argparse
import cv2
import numpy as np
import torch
import torchvision.transforms.functional as F

from utils import extract_blobs, load_dino_model, preprocess_images

COMPUTE_BLOBS = True
USE_PICAM = False

if USE_PICAM:
    from picamera2 import Picamera2

# ----------------------
# Tracking state
# ----------------------
TARGET_SELECTED = False
TARGET_COM = None         # (x, y) last known center
TRACK_HISTORY = []        # recent (x, y)
MAX_ASSOC_DIST = 60.0     # pixels (tune per scale/FPS)
TRAIL_LEN = 50            # how many last positions to draw
RNG = np.random.default_rng(42)  # deterministic by default

def _blob_stats_from_mask(mask_torch):
    """
    Given a torch.bool tensor mask (H, W), return:
      - com: (x_mean, y_mean) or None
      - bbox: (x0, y0, x1, y1) or None
    """
    y_idxs, x_idxs = torch.where(mask_torch)
    if y_idxs.numel() == 0:
        return None, None
    x_mean = x_idxs.float().mean().item()
    y_mean = y_idxs.float().mean().item()
    x0 = int(x_idxs.min().item()); x1 = int(x_idxs.max().item())
    y0 = int(y_idxs.min().item()); y1 = int(y_idxs.max().item())
    return (x_mean, y_mean), (x0, y0, x1, y1)

def _nearest_centroid(centroids, target_xy, max_dist):
    """
    centroids: list[(x, y)], target_xy: (x, y)
    returns index within max_dist else None
    """
    if not centroids:
        return None
    tx, ty = target_xy
    best_i, best_d2 = None, None
    for i, (x, y) in enumerate(centroids):
        dx, dy = x - tx, y - ty
        d2 = dx*dx + dy*dy
        if best_d2 is None or d2 < best_d2:
            best_d2 = d2; best_i = i
    if best_d2 is not None and best_d2 <= max_dist * max_dist:
        return best_i
    return None

def run_thorax_model(model, frame):
    """
    Run thorax detection on cv2 image (np array, HWC, uint8).
    Returns:
      frame_vis: BGR uint8 for display
      pred_np: np.bool_ mask (H, W)
    """
    # Crop to square (same logic you had)
    if frame.shape[0] > frame.shape[1]:
        frame = frame.swapaxes(0, 1)
    x_extra = (frame.shape[1] - frame.shape[0]) // 2
    frame = frame[:, x_extra:-x_extra, :]

    frame_t = preprocess_images(frame)           # (1, C, H, W)
    pred = model(frame_t).squeeze(0)             # (1, h, w) or (h, w)
    pred = F.resize(pred, (frame_t.shape[2], frame_t.shape[3]), antialias=True)
    pred = pred.squeeze(0)                       # (H, W)
    pred = (pred > 0.5).to(torch.bool)
    pred_np = pred.cpu().numpy()

    # back to BGR uint8 for display
    frame_vis = frame_t.squeeze(0).permute(1, 2, 0).cpu().numpy()
    frame_vis = (frame_vis * 255).astype(np.uint8)
    if frame_vis.ndim == 2:
        frame_vis = cv2.cvtColor(frame_vis, cv2.COLOR_GRAY2BGR)

    return frame_vis, pred_np

@torch.no_grad()
def main():
    global TARGET_SELECTED, TARGET_COM, TRACK_HISTORY, RNG

    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, help="Omit to use camera.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--seed", type=int, default=42, help=" RNG seed for first-frame random pick.")
    args = parser.parse_args()

    RNG = np.random.default_rng(args.seed)
    model = load_dino_model(args.model)

    # Video source
    if USE_PICAM:
        print("Using PiCam.")
        picam = Picamera2()
        picam.configure(picam.create_preview_configuration(main={"format": "RGB888","size": (1280, 720)}))
        picam.start()
        time.sleep(1)
        video_read = None
    else:
        vid_path = 0 if args.video is None else args.video
        video_read = cv2.VideoCapture(vid_path)
        if vid_path == 0:
            video_read.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        print("Using opencv video reader, path =", vid_path)

    window_name = "thorax-tracker"
    cv2.namedWindow(window_name)

    first_frame_done = False

    while True:
        if USE_PICAM:
            frame = picam.capture_array()
        else:
            ret, frame = video_read.read()
            if not ret:
                break

        frame, pred = run_thorax_model(model, frame)

        # Color all detected thoraxes green for context
        frame[pred] = (0, 255, 0)

        # Get blobs, centroids, bboxes
        centroids, bboxes = [], []
        if COMPUTE_BLOBS:
            # If your extract_blobs returns np masks or labeled image, adapt below.
            blobs = extract_blobs(pred, 0.5)  # EXPECTED: list of masks (H,W)
            for b in blobs:
                if isinstance(b, np.ndarray):
                    b = torch.from_numpy(b.astype(bool))
                elif not isinstance(b, torch.Tensor):
                    b = torch.as_tensor(b, dtype=torch.bool)
                com, bbox = _blob_stats_from_mask(b)
                if com is None: 
                    continue
                centroids.append(com)
                bboxes.append(bbox)

        # Draw bboxes/centroids (green)
        for (x0, y0, x1, y1) in bboxes:
            cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 140, 0), 1)
        for (cx, cy) in centroids:
            cv2.circle(frame, (int(cx), int(cy)), 3, (0, 100, 0), -1)

        # On FIRST frame with detections, randomly pick ONE target
        if not first_frame_done and centroids:
            pick_idx = int(RNG.integers(len(centroids)))
            TARGET_COM = centroids[pick_idx]
            TARGET_SELECTED = True
            TRACK_HISTORY = [TARGET_COM]
            first_frame_done = True

        # Tracking thereafter
        if TARGET_SELECTED:
            idx = _nearest_centroid(centroids, TARGET_COM, MAX_ASSOC_DIST)
            if idx is not None:
                TARGET_COM = centroids[idx]
                TRACK_HISTORY.append(TARGET_COM)
                if len(TRACK_HISTORY) > TRAIL_LEN:
                    TRACK_HISTORY = TRACK_HISTORY[-TRAIL_LEN:]

                # highlight the tracked bee in RED
                tx, ty = int(TARGET_COM[0]), int(TARGET_COM[1])
                if idx < len(bboxes) and bboxes[idx] is not None:
                    (x0, y0, x1, y1) = bboxes[idx]
                    cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 0, 255), 2)
                cv2.circle(frame, (tx, ty), 5, (0, 0, 255), -1)
                for i in range(1, len(TRACK_HISTORY)):
                    x1, y1 = map(int, TRACK_HISTORY[i-1])
                    x2, y2 = map(int, TRACK_HISTORY[i])
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, "TRACKING (random first-frame pick)", (10, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
            else:
                cv2.putText(frame, "TARGET LOST (searching)", (10, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1)
        if key == ord("q"):
            break
        elif key == ord("r"):
            # Re-seed and force a re-pick on the next frame with detections
            TARGET_SELECTED = False
            TARGET_COM = None
            TRACK_HISTORY = []
            first_frame_done = False
            RNG = np.random.default_rng(int(time.time()))

    if not USE_PICAM and video_read is not None:
        video_read.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()