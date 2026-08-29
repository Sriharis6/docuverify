import cv2
import numpy as np
import os
from PIL import Image, ImageChops, ImageEnhance

def analyze_ela(image_path: str, quality_resave: int = 90, scale: int = 15):
    """
    Module A — Error Level Analysis (ELA)
    Re-saves the image at a known quality and compares it with the original.
    Regions that were previously saved at lower quality or edited will show higher difference.
    Returns score (0 to 1), heatmap path, and flagged high-error region bounding boxes.
    """
    try:
        if not os.path.exists(image_path):
            return {"score": 0.0, "explanation": "File not found for ELA.", "heatmap_path": None, "flagged": False, "regions": []}

        original = Image.open(image_path).convert('RGB')
        w, h = original.size
        
        # Temp path for resaved image
        temp_filename = image_path + ".temp.jpg"
        original.save(temp_filename, 'JPEG', quality=quality_resave)
        
        resaved = Image.open(temp_filename)
        
        # Calculate pixel difference
        ela_img = ImageChops.difference(original, resaved)
        
        # Get extrema to scale it
        extrema = ela_img.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        
        if max_diff == 0:
            max_diff = 1 # Avoid division by zero
            
        scale_factor = 255.0 / max_diff
        ela_enhanced = ImageEnhance.Brightness(ela_img).enhance(scale_factor)
        
        # Save ELA heatmap
        heatmap_path = image_path + ".ela.jpg"
        ela_enhanced.save(heatmap_path, 'JPEG')
        
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        
        # Calculate variance across the image
        ela_np = np.array(ela_enhanced)
        variance = float(np.var(ela_np))
        
        # Find high-error regions (blobs in the ELA diff image)
        gray_diff = cv2.cvtColor(np.array(ela_img), cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray_diff, min(30, max(10, int(max_diff * 0.4))), 255, cv2.THRESH_BINARY)
        
        # Kernel blur to find high diff clusters
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        flagged_regions = []
        for c in contours:
            area = cv2.contourArea(c)
            if area > (w * h * 0.005): # At least 0.5% of total area
                rx, ry, rw, rh = cv2.boundingRect(c)
                norm_x = (rx / float(w)) * 100.0
                norm_y = (ry / float(h)) * 100.0
                norm_w = (rw / float(w)) * 100.0
                norm_h = (rh / float(h)) * 100.0
                
                flagged_regions.append({
                    "x": norm_x, "y": norm_y, "w": norm_w, "h": norm_h,
                    "label": "ELA Compression Anomaly",
                    "sev": "High",
                    "tip": "Abnormal re-compression error level detected in this region."
                })
        
        # Normalize score heuristically
        # Genuine images saved uniformly have low max_diff (<25) and low variance (<500)
        if max_diff < 30 or variance < 500:
            score = float(variance / 2500.0)
            flagged = False
            flagged_regions = []
        else:
            score = min(max(variance / 1500.0, len(flagged_regions) * 0.35), 1.0)
            flagged = bool(score >= 0.45 or len(flagged_regions) >= 2)
        
        explanation = f"ELA error variance is {variance:.1f}. "
        if flagged:
            explanation += f"Detected {len(flagged_regions)} region(s) with abnormal re-compression levels indicating localized edits."
        else:
            explanation += "Compression artifacts are uniform across the document."
            
        return {
            "score": float(score),
            "explanation": explanation,
            "heatmap_path": heatmap_path,
            "flagged": flagged,
            "variance": variance,
            "regions": flagged_regions
        }

        
    except Exception as e:
        return {"score": 0.0, "explanation": f"ELA failed: {str(e)}", "heatmap_path": None, "flagged": False, "regions": []}

if __name__ == "__main__":
    pass

