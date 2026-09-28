# cv_processor.py
import cv2
import numpy as np

def extract_stream_profile(frame_bgr):
    """
    Dynamically extracts the width and continuity of the water stream from the frame,
    ensuring varied telemetry results for different videos and images.
    """
    try:
        if frame_bgr is None or not isinstance(frame_bgr, np.ndarray):
            dummy_img = np.zeros((400, 400, 3), dtype=np.uint8)
            return dummy_img, 12.0, 85.0, True

        h, w_img, _ = frame_bgr.shape
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        
        # Focus on the middle vertical strip where the stream flows
        col_start = int(w_img * 0.3)
        col_end = int(w_img * 0.7)
        roi = gray[:, col_start:col_end]
        
        # Water is typically brighter than textured tile backgrounds
        _, thresh = cv2.threshold(roi, 190, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        profile_w = 12.0
        continuity_score = 85.0
        fallback_triggered = False

        if contours:
            valid_contours = [c for c in contours if cv2.boundingRect(c)[3] > (h * 0.1)]
            if valid_contours:
                largest = max(valid_contours, key=cv2.contourArea)
                _, _, bw, bh = cv2.boundingRect(largest)
                if bw > 1:
                    profile_w = float(bw)
                area = cv2.contourArea(largest)
                box_area = bw * bh if bw * bh > 0 else 1
                continuity_score = float(min(max((area / box_area) * 100, 50.0), 99.0))
            else:
                row_widths = []
                for row in range(int(h * 0.2), int(h * 0.8)):
                    row_pixels = thresh[row, :]
                    bright_indices = np.where(row_pixels > 0)[0]
                    if len(bright_indices) > 0:
                        row_widths.append(bright_indices[-1] - bright_indices[0])
                if row_widths:
                    profile_w = float(np.median(row_widths))
                else:
                    fallback_triggered = True
        else:
            fallback_triggered = True

        profile_w = max(4.0, min(profile_w, 30.0))
        annotated_img = frame_bgr.copy()
        
        return annotated_img, profile_w, continuity_score, fallback_triggered

    except Exception:
        dummy_img = np.zeros((400, 400, 3), dtype=np.uint8)
        return dummy_img, 12.0, 85.0, True