import cv2
import numpy as np
import os

def analyze_alignment(image_path: str):
    """
    Module F — Text Baseline Alignment & Layout Skew Analysis
    Detects text baseline angles, vertical alignment offsets, line spacing variations,
    and text block position shifts indicative of inserted or tampered text fields.
    """
    try:
        if not os.path.exists(image_path):
            return {
                "score": 0.0,
                "explanation": "Alignment Audit: Source file unavailable.",
                "flagged": False,
                "regions": [],
                "details": {"line_skews": [], "baseline_variance": 0.0}
            }

        img = cv2.imread(image_path)
        if img is None:
            return {
                "score": 0.0,
                "explanation": "Alignment Audit: Image format unreadable.",
                "flagged": False,
                "regions": [],
                "details": {"line_skews": [], "baseline_variance": 0.0}
            }

        h, w, _ = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Adaptive binarization to extract text line structure
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 4)
        
        # Horizontal structuring element to isolate text baselines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 2))
        dilated = cv2.dilate(thresh, kernel, iterations=1)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        lines = []
        for c in contours:
            rx, ry, rw, rh = cv2.boundingRect(c)
            # Filter for horizontal text lines
            if rw > 40 and 8 < rh < 80:
                # Find minAreaRect to calculate line angle
                rect = cv2.minAreaRect(c)
                angle = rect[-1]
                if angle < -45:
                    angle = 90 + angle
                elif angle > 45:
                    angle = angle - 90
                
                lines.append({
                    "x": rx, "y": ry, "w": rw, "h": rh,
                    "angle": angle,
                    "bottom": ry + rh
                })

        if len(lines) < 3:
            return {
                "score": 0.05,
                "explanation": "Alignment Audit: Baseline alignment uniform. Insufficient text lines for macro skew evaluation.",
                "flagged": False,
                "regions": [],
                "details": {"line_skews": [], "baseline_variance": 0.0}
            }

        angles = [l["angle"] for l in lines]
        median_angle = float(np.median(angles))
        
        # Sort lines by Y to evaluate line spacing consistency
        sorted_lines = sorted(lines, key=lambda l: l["y"])
        vertical_gaps = []
        for i in range(len(sorted_lines) - 1):
            gap = sorted_lines[i+1]["y"] - sorted_lines[i]["bottom"]
            if 4 < gap < 120:
                vertical_gaps.append(gap)
                
        gap_variance = float(np.std(vertical_gaps)) if len(vertical_gaps) > 2 else 0.0
        
        flagged_regions = []
        anomalous_lines = 0
        
        for idx, line in enumerate(lines):
            dev = abs(line["angle"] - median_angle)
            if dev > 2.5: # More than 2.5 degrees tilt deviation relative to document median
                anomalous_lines += 1
                norm_x = (line["x"] / float(w)) * 100.0
                norm_y = (line["y"] / float(h)) * 100.0
                norm_w = (line["w"] / float(w)) * 100.0
                norm_h = (line["h"] / float(h)) * 100.0
                
                flagged_regions.append({
                    "x": norm_x, "y": norm_y, "w": norm_w, "h": norm_h,
                    "label": "Baseline Skew Anomaly",
                    "sev": "High" if dev > 4.5 else "Medium",
                    "tip": f"Line baseline tilt deviation: {dev:.2f}° (Doc Median: {median_angle:.2f}°)"
                })

        score = min(1.0, (anomalous_lines * 0.35) + (gap_variance / 40.0 * 0.2))
        flagged = bool(score >= 0.35 or len(flagged_regions) > 0)
        
        if flagged:
            explanation = f"Alignment Audit: Flagged {len(flagged_regions)} line(s) with anomalous baseline tilt or irregular vertical spacing (Gap Var: {gap_variance:.1f})."
        else:
            explanation = f"Alignment Audit: Document text lines conform to uniform baseline angle ({median_angle:.1f}°) and consistent line spacing."

        return {
            "score": round(float(score), 3),
            "explanation": explanation,
            "flagged": flagged,
            "regions": flagged_regions,
            "details": {
                "median_angle": round(float(median_angle), 2),
                "angle_variance": round(float(np.var(angles)), 3),
                "gap_variance": round(gap_variance, 2),
                "flagged_lines_count": len(flagged_regions)
            }
        }

    except Exception as e:
        return {
            "score": 0.0,
            "explanation": f"Alignment Audit Failed: {str(e)}",
            "flagged": False,
            "regions": [],
            "details": {"line_skews": [], "baseline_variance": 0.0}
        }
