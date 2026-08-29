import cv2
import numpy as np
import os

def analyze_copy_move(image_path: str):
    """
    Module B — Copy-Move Forgery Detection using ORB features.
    Extracts keypoints and matches them against each other in the same image.
    Clusters matching points that are spatially separated to locate cloned region bounding boxes.
    """
    try:
        if not os.path.exists(image_path):
             return {"score": 0.0, "explanation": "File not found.", "flagged": False, "regions": [], "matches_path": None}

        img = cv2.imread(image_path)
        if img is None:
             return {"score": 0.0, "explanation": "Invalid image.", "flagged": False, "regions": [], "matches_path": None}
             
        h, w, _ = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Initiate feature detectors (SIFT preferred if available, ORB fallback)
        kp, des = None, None
        try:
            sift = cv2.SIFT_create(nfeatures=4000)
            kp, des = sift.detectAndCompute(gray, None)
            is_sift = True
        except Exception:
            orb = cv2.ORB_create(nfeatures=5000, scaleFactor=1.2, nlevels=8, edgeThreshold=10, fastThreshold=5)
            kp, des = orb.detectAndCompute(gray, None)
            is_sift = False

        if des is None or len(des) < 8:
             return {"score": 0.0, "explanation": "Not enough features found for copy-move analysis.", "flagged": False, "regions": [], "matches_path": None}

        # BFMatcher (NORM_L2 for SIFT, NORM_HAMMING for ORB)
        norm_type = cv2.NORM_L2 if is_sift else cv2.NORM_HAMMING
        bf = cv2.BFMatcher(norm_type, crossCheck=False)
        matches = bf.knnMatch(des, des, k=2)
        
        good_matches = []
        pts_source = []
        pts_target = []

        ratio_thresh = 0.75 if is_sift else 0.82

        for match_pair in matches:
            if len(match_pair) < 2:
                continue
            m, n = match_pair[0], match_pair[1]
            if m.queryIdx != m.trainIdx and m.distance < ratio_thresh * n.distance: # Ratio test
                pt1 = kp[m.queryIdx].pt
                pt2 = kp[m.trainIdx].pt
                
                dist = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
                if dist > 30: # Must be at least 30 pixels apart spatially
                    good_matches.append(m)
                    pts_source.append(pt1)
                    pts_target.append(pt2)

        num_matches = len(good_matches)
        flagged_regions = []
        matches_path = None

        if num_matches >= 3:
            # Cluster matched points to extract region bounding boxes
            src_arr = np.array(pts_source)
            dst_arr = np.array(pts_target)
            
            min_src, max_src = np.min(src_arr, axis=0), np.max(src_arr, axis=0)
            min_dst, max_dst = np.min(dst_arr, axis=0), np.max(dst_arr, axis=0)
            
            for (min_pt, max_pt, label_str) in [(min_src, max_src, "Source Cloned Region"), (min_dst, max_dst, "Duplicate Target Region")]:
                bx = float(max(0, min_pt[0] - 15))
                by = float(max(0, min_pt[1] - 15))
                bw = float(min(w - bx, (max_pt[0] - min_pt[0]) + 30))
                bh = float(min(h - by, (max_pt[1] - min_pt[1]) + 30))
                
                if bw > 10 and bh > 10:
                    flagged_regions.append({
                        "x": (bx / float(w)) * 100.0,
                        "y": (by / float(h)) * 100.0,
                        "w": (bw / float(w)) * 100.0,
                        "h": (bh / float(h)) * 100.0,
                        "label": "Copy-Move Duplicate Region",
                        "sev": "High",
                        "tip": f"{label_str}: Matched feature cluster identified in copy-move analysis."
                    })

            # Draw matches visualization
            vis = img.copy()
            for p1, p2 in zip(pts_source, pts_target):
                cv2.circle(vis, (int(p1[0]), int(p1[1])), 4, (0, 0, 255), -1)
                cv2.circle(vis, (int(p2[0]), int(p2[1])), 4, (0, 255, 0), -1)
                cv2.line(vis, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (255, 255, 0), 1)

            matches_path = image_path + ".copymove.jpg"
            cv2.imwrite(matches_path, vis)

        score = min(float(num_matches) / 10.0, 1.0) if num_matches >= 3 else 0.0
        flagged = bool(score >= 0.30 or len(flagged_regions) > 0)
        
        explanation = f"Copy-Move check localized {num_matches} identical feature matches across distinct document regions. "
        if flagged:
            explanation += "High confidence of clone-stamp/copy-paste duplication."
        else:
            explanation += "No duplicated regions detected."
            
        return {
            "score": float(score),
            "explanation": explanation,
            "flagged": flagged,
            "num_matches": num_matches,
            "regions": flagged_regions,
            "matches_path": matches_path
        }
        
    except Exception as e:
        return {"score": 0.0, "explanation": f"Copy-move detection failed: {str(e)}", "flagged": False, "regions": [], "matches_path": None}

