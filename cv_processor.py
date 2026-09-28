# cv_processor.py
import cv2
import numpy as np

def extract_stream_profile(frame_bgr):
    """
    Safely extracts stream profile metrics and guarantees returning 
    exactly 4 values to prevent any ValueError unpacking crash in app.py.
    """
    try:
        if frame_bgr is None or not isinstance(frame_bgr, np.ndarray):
            # Fallback dummy frame and values if input is invalid
            dummy_img = np.zeros((400, 400, 3), dtype=np.uint8)
            return dummy_img, 12.0, 25.0, True

        # Basic image processing for stream width and height estimation
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 120, 255, cv2.THRESH_BINARY)
        
        # Find contours or estimate profile width safely
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        profile_w = 12.0
        h_val = float(frame_bgr.shape[0])
        fallback_triggered = False

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            if w > 2:
                profile_w = float(w)
        else:
            fallback_triggered = True

        annotated_img = frame_bgr.copy()
        return annotated_img, profile_w, h_val, fallback_triggered

    except Exception:
        # Absolute safety net
        dummy_img = np.zeros((400, 400, 3), dtype=np.uint8)
        return dummy_img, 12.0, 25.0, True