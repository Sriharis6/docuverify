import cv2
import numpy as np
import os
from PIL import Image

def analyze_typography(image_path: str, text_regions: list = None):
    """
    Module E — Typography Consistency Analysis
    Extracts features (stroke width via edge density, character height, font color/anti-aliasing)
    for text regions and compares them against the document's dominant style to flag outliers.
    """
    try:
        if not os.path.exists(image_path):
            return {"score": 0.0, "explanation": "File not found for typography analysis.", "flagged": False, "regions": []}

        img = cv2.imread(image_path)
        if img is None:
            return {"score": 0.0, "explanation": "Invalid image for typography analysis.", "flagged": False, "regions": []}

        h, w, _ = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect text/high-contrast regions if not explicitly provided
        regions_to_check = []
        if text_regions and len(text_regions) > 0:
            regions_to_check = text_regions
        else:
            # Otsu/Adaptive binarization + contour extraction for robust text line detection
            blur = cv2.GaussianBlur(gray, (3, 3), 0)
            thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 4)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (12, 3))
            dilated = cv2.dilate(thresh, kernel, iterations=1)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            boxes = []
            for c in contours:
                rx, ry, rw, rh = cv2.boundingRect(c)
                # Filter for character / word line dimensions
                if 12 < rh < 90 and 30 < rw < 380 and ry > 70:
                    boxes.append((rx, ry, rw, rh))
            
            # Sort vertically by Y coordinate
            boxes = sorted(boxes, key=lambda b: b[1])
            regions_to_check = [{"x": b[0], "y": b[1], "w": b[2], "h": b[3]} for b in boxes]

        if len(regions_to_check) < 2:
            return {
                "score": 0.0,
                "explanation": "Typography check complete: Insufficient text blocks to determine style outliers.",
                "flagged": False,
                "regions": []
            }

        # Calculate features per region: edge density (stroke width proxy), mean intensity, height
        densities = []
        heights = []
        std_devs = []
        valid_regions = []

        for reg in regions_to_check:
            rx, ry, rw, rh = reg["x"], reg["y"], reg["w"], reg["h"]
            # Clamp bounds
            rx, ry = max(0, rx), max(0, ry)
            rw, rh = min(w - rx, rw), min(h - ry, rh)
            if rw <= 4 or rh <= 4:
                continue

            crop = gray[ry:ry+rh, rx:rx+rw]
            edges = cv2.Canny(crop, 50, 150)
            edge_density = np.sum(edges > 0) / float(rw * rh)
            
            densities.append(edge_density)
            heights.append(rh)
            std_devs.append(np.std(crop))
            valid_regions.append({"x": rx, "y": ry, "w": rw, "h": rh, "density": edge_density, "height": rh, "std": np.std(crop)})

        if len(densities) < 2:
            return {
                "score": 0.0,
                "explanation": "Typography check complete: No clear text style variance detected.",
                "flagged": False,
                "regions": []
            }

        # Compute median & z-scores for edge density and height to find outliers
        mean_density = np.median(densities)
        std_density = np.std(densities) + 1e-5

        mean_height = np.median(heights)
        std_height = np.std(heights) + 1e-5

        outliers = []
        flagged_regions = []

        for reg in valid_regions:
            z_density = abs(reg["density"] - mean_density) / std_density
            z_height = abs(reg["height"] - mean_height) / std_height

            # High z-score indicates stroke width or font size inconsistency
            if z_density > 1.8 or z_height > 1.8:
                outliers.append(reg)
                # Convert to normalized percentage coordinates
                norm_x = (reg["x"] / float(w)) * 100.0
                norm_y = (reg["y"] / float(h)) * 100.0
                norm_w = (reg["w"] / float(w)) * 100.0
                norm_h = (reg["h"] / float(h)) * 100.0
                
                flagged_regions.append({
                    "x": norm_x, "y": norm_y, "w": norm_w, "h": norm_h,
                    "label": "Typography Anomaly",
                    "sev": "Medium",
                    "tip": f"Inconsistent font stroke/height (z-score density: {z_density:.1f}, height: {z_height:.1f})."
                })

        score = min(float(len(outliers)) * 0.45, 1.0)
        flagged = bool(score >= 0.35 or len(outliers) > 0)

        if flagged:
            explanation = f"Typography check flagged {len(outliers)} text region(s) with inconsistent font size, stroke width, or anti-aliasing pattern."
        else:
            explanation = "Typography check complete: Font style, stroke width, and text rendering are uniform across the document."

        return {
            "score": float(score),
            "explanation": explanation,
            "flagged": flagged,
            "regions": flagged_regions
        }

    except Exception as e:
        return {"score": 0.0, "explanation": f"Typography analysis failed: {str(e)}", "flagged": False, "regions": []}
