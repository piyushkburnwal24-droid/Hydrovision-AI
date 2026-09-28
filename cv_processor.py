import cv2
import numpy as np

def extract_stream_profile(image_bgr):
    # Convert frame to grayscale and blur to reduce image noise
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Use Canny edge detection to find the boundaries of the water stream
    edges = cv2.Canny(blurred, 40, 120)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    valid_contours = []
    if contours:
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            extent = float(area) / max(1.0, float(w * h))
            # Filter contours to find the main vertical water stream
            if h > w * 1.0 and extent > 0.15:
                valid_contours.append(cnt)
                
    if valid_contours:
        # Pick the largest contour found
        c = max(valid_contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        
        # Measure widths at 5 different horizontal slices down the stream
        profile_widths = []
        slice_h = max(1, h // 5)
        for i in range(5):
            sy = y + i * slice_h
            roi = edges[sy:min(image_bgr.shape[0], sy + slice_h), x:min(image_bgr.shape[1], x + w)]
            cols = np.sum(roi > 0, axis=0)
            nz = np.where(cols > 0)[0]
            measured_w = float(nz[-1] - nz[0]) if len(nz) > 1 else float(w)
            profile_widths.append(max(2.0, measured_w))
            
        annotated = image_bgr.copy()
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 127), 2)
        return annotated, profile_widths, float(h), False
    else:
        # Fallback dimensions if no clear contour is found
        h_img, w_img = image_bgr.shape[:2]
        default_widths = [w_img * 0.15, w_img * 0.13, w_img * 0.11, w_img * 0.10, w_img * 0.09]
        return image_bgr, default_widths, float(h_img * 0.5), True