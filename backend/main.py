"""
DocuVerify — FastAPI Backend
Multi-Signal Forensic Document Verification Engine v3.0

Endpoints:
  GET  /               — Health status
  GET  /health         — Detailed system health
  GET  /sample-images  — List available sample demo files
  POST /analyze        — Analyze an uploaded document image/PDF
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import shutil
import os
import uuid
import cv2
import logging
from datetime import datetime

from core.ela import analyze_ela
from core.copy_move import analyze_copy_move
from core.metadata import analyze_metadata
from core.ocr_nlp import analyze_ocr_logical
from core.typography import analyze_typography
from core.alignment import analyze_alignment
from core.fusion import fuse_results
from core.supabase_sync import sync_report_to_supabase

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("docuverify")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="DocuVerify Forensic API",
    description="Multi-Signal Document Authenticity & Forensic Verification Engine",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Directories ───────────────────────────────────────────────────────────────
BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_DIR  = os.path.abspath(os.path.join(BASE_DIR, "uploads"))
DATASET_DIR = os.path.abspath(os.path.join(BASE_DIR, "dataset"))

os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Mount dataset directory if it exists (for sample image serving)
if os.path.isdir(DATASET_DIR):
    app.mount("/dataset", StaticFiles(directory=DATASET_DIR), name="dataset")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".pdf", ".bmp"}
MAX_FILE_SIZE_MB   = 20

# ── Forensic overlay generator ────────────────────────────────────────────────
def generate_annotated_overlay(image_path: str, output_path: str, regions: list) -> str | None:
    """
    Draws forensic bounding box callouts on the document image.
    Uses greyscale-safe colors (white + black) for readability.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None
        h, w, _ = img.shape

        # B&W severity mapping: stroke intensity varies by severity
        stroke_map = {
            "Critical": (10, 10, 10),
            "High":     (30, 30, 30),
            "Medium":   (80, 80, 80),
            "Low":      (140, 140, 140),
        }
        thickness_map = {
            "Critical": 3,
            "High":     2,
            "Medium":   2,
            "Low":      1,
        }

        for idx, reg in enumerate(regions, 1):
            norm_x = reg.get("x", 0)
            norm_y = reg.get("y", 0)
            norm_w = reg.get("w", 0)
            norm_h = reg.get("h", 0)
            sev    = reg.get("sev", "High")
            label  = reg.get("label", "Anomaly")

            bx = int((norm_x / 100.0) * w)
            by = int((norm_y / 100.0) * h)
            bw = int((norm_w / 100.0) * w)
            bh = int((norm_h / 100.0) * h)

            color     = stroke_map.get(sev, (30, 30, 30))
            thickness = thickness_map.get(sev, 2)

            cv2.rectangle(img, (bx, by), (bx + bw, by + bh), color, thickness)

            # Corner tick marks (forensic callout style)
            cl = max(8, int(min(bw, bh) * 0.15))
            for (px, py) in [(bx, by), (bx+bw, by), (bx, by+bh), (bx+bw, by+bh)]:
                dx = 1 if px == bx else -1
                dy = 1 if py == by else -1
                cv2.line(img, (px, py), (px + dx*cl, py), color, thickness+1)
                cv2.line(img, (px, py), (px, py + dy*cl), color, thickness+1)

            # Region number badge
            badge_txt = f"#{idx}"
            (tw, th), _ = cv2.getTextSize(badge_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            bx_text = max(0, bx)
            by_text = max(0, by - 20)
            cv2.rectangle(img, (bx_text, by_text), (bx_text + tw + 10, by_text + 20), (20, 20, 20), -1)
            cv2.putText(img, badge_txt, (bx_text + 5, by_text + 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

            # Module label
            mod_txt = label[:32]
            (mw, mh), _ = cv2.getTextSize(mod_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.36, 1)
            cv2.rectangle(img, (bx, by + bh), (bx + mw + 8, by + bh + 18), (40, 40, 40), -1)
            cv2.putText(img, mod_txt, (bx + 4, by + bh + 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.36, (220, 220, 220), 1, cv2.LINE_AA)

        cv2.imwrite(output_path, img)
        return output_path

    except Exception as e:
        log.error(f"Overlay generation failed: {e}")
        return None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Status"])
def root():
    return {
        "status": "online",
        "service": "DocuVerify Forensic API",
        "version": "3.0.0",
        "docs": "/docs",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/health", tags=["Status"])
def health_check():
    """Returns detailed system health including module availability."""
    modules_status = {}

    # Check Tesseract
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        modules_status["tesseract_ocr"] = {"available": True, "note": "OCR engine ready"}
    except Exception as e:
        modules_status["tesseract_ocr"] = {"available": False, "note": f"Tesseract not found: {str(e)[:60]}. OCR will use fallback."}

    # Check OpenCV SIFT
    try:
        cv2.SIFT_create(nfeatures=10)
        modules_status["sift_feature_detector"] = {"available": True, "note": "SIFT available (opencv-contrib)"}
    except Exception:
        modules_status["sift_feature_detector"] = {"available": False, "note": "SIFT unavailable, ORB fallback active"}

    # Check dataset
    genuine_count = 0
    tampered_count = 0
    if os.path.isdir(DATASET_DIR):
        g_dir = os.path.join(DATASET_DIR, "genuine")
        t_dir = os.path.join(DATASET_DIR, "tampered")
        if os.path.isdir(g_dir):
            genuine_count = len([f for f in os.listdir(g_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        if os.path.isdir(t_dir):
            tampered_count = len([f for f in os.listdir(t_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

    return {
        "status": "healthy",
        "version": "3.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "modules": modules_status,
        "forensic_engines": [
            "Error Level Analysis (ELA)",
            "Copy-Move Cloning Detection",
            "Typography Consistency",
            "Text Baseline & Layout Skew",
            "OCR & Logical Integrity",
            "EXIF & Document Metadata",
        ],
        "sample_dataset": {
            "genuine_images": genuine_count,
            "tampered_images": tampered_count,
        },
        "upload_dir": UPLOAD_DIR,
        "max_file_size_mb": MAX_FILE_SIZE_MB,
    }


@app.get("/sample-images", tags=["Dataset"])
def list_sample_images(request: Request):
    """Returns a list of available sample images from the dataset directory."""
    results = {"genuine": [], "tampered": []}

    if not os.path.isdir(DATASET_DIR):
        return {
            "error": "Dataset directory not found. Run dataset_generator.py to generate samples.",
            "path": DATASET_DIR,
            **results,
        }

    base_url = str(request.base_url).rstrip("/")
    server_base = f"{base_url}/dataset"
    descriptions = {
        "genuine_certificate.jpg": "Clean academic certificate — NIT Tiruchirapalli. No anomalies expected.",
        "genuine_id_card.jpg":     "Clean national ID card with consistent typography and valid dates.",
        "tampered_date_altered.jpg": "ID card with altered expiry date (2010) before issue date (2020). OCR logical failure.",
        "tampered_copy_move.jpg":    "Certificate with copy-pasted CGPA region. Copy-move and ELA anomalies expected.",
        "tampered_ela_artifact.jpg": "Academic transcript with ELA artifact from multi-generation JPEG re-save.",
    }

    for category in ["genuine", "tampered"]:
        cat_dir = os.path.join(DATASET_DIR, category)
        if not os.path.isdir(cat_dir):
            continue
        for fname in sorted(os.listdir(cat_dir)):
            if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            fpath = os.path.join(cat_dir, fname)
            fsize = os.path.getsize(fpath)
            results[category].append({
                "filename": fname,
                "category": category,
                "description": descriptions.get(fname, "Sample document for forensic testing."),
                "size_kb": round(fsize / 1024, 1),
                "url": f"{server_base}/{category}/{fname}",
            })

    return results


@app.post("/analyze", tags=["Forensics"])
async def analyze_document(request: Request, file: UploadFile = File(...)):
    """
    Runs all 6 forensic analysis modules against the uploaded document.
    Returns structured test_cases, forensic scores, regions, and a summary report.
    """
    # ── Validate ──────────────────────────────────────────────────────────────
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Accepted: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    file_id       = str(uuid.uuid4())[:8]
    safe_filename = f"{file_id}_{file.filename}"
    file_path     = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        # ── Save uploaded file ────────────────────────────────────────────────
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            os.remove(file_path)
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({file_size_mb:.1f} MB). Maximum allowed: {MAX_FILE_SIZE_MB} MB."
            )

        log.info(f"Analyzing [{file_id}] {file.filename!r} ({file_size_mb:.2f} MB)")

        # ── Run 6 independent forensic modules ───────────────────────────────
        log.info(f"[{file_id}] Running ELA...")
        ela_res  = analyze_ela(file_path)

        log.info(f"[{file_id}] Running Copy-Move...")
        cm_res   = analyze_copy_move(file_path)

        log.info(f"[{file_id}] Running Metadata Audit...")
        meta_res = analyze_metadata(file_path)

        log.info(f"[{file_id}] Running OCR & Logical Integrity...")
        ocr_res  = analyze_ocr_logical(file_path)

        log.info(f"[{file_id}] Running Typography Analysis...")
        typo_res = analyze_typography(file_path)

        log.info(f"[{file_id}] Running Alignment Analysis...")
        align_res = analyze_alignment(file_path)

        # ── Fuse results ──────────────────────────────────────────────────────
        log.info(f"[{file_id}] Fusing results...")
        final_result = fuse_results(ela_res, cm_res, meta_res, ocr_res, typo_res, align_res)

        # ── Generate annotated overlay ────────────────────────────────────────
        overlay_filename = f"{file_id}_overlay.jpg"
        overlay_path     = os.path.join(UPLOAD_DIR, overlay_filename)
        overlay_created  = generate_annotated_overlay(
            file_path, overlay_path, final_result.get("regions", [])
        )

        # ── Attach URLs ───────────────────────────────────────────────────────
        base_url = str(request.base_url).rstrip("/")
        server_base = f"{base_url}/uploads"
        ela_heatmap_url = None
        if ela_res.get("heatmap_path") and os.path.exists(ela_res["heatmap_path"]):
            ela_heatmap_url = f"{server_base}/{os.path.basename(ela_res['heatmap_path'])}"

        final_result["visualizations"] = {
            "original_url":    f"{server_base}/{safe_filename}",
            "ela_heatmap_url": ela_heatmap_url,
            "overlay_url":     f"{server_base}/{overlay_filename}" if overlay_created else f"{server_base}/{safe_filename}",
        }

        # ── File info ─────────────────────────────────────────────────────────
        final_result["file_info"] = {
            "filename":      file.filename,
            "file_id":       file_id,
            "size_kb":       round(file_size_mb * 1024, 1),
            "extension":     ext,
            "analyzed_at":   datetime.utcnow().isoformat() + "Z",
        }

        # ── Sync to Supabase if configured ────────────────────────────────────
        try:
            supabase_id = sync_report_to_supabase(final_result)
            if supabase_id:
                final_result["supabase_id"] = supabase_id
        except Exception as e:
            log.warning(f"Optional Supabase sync failed: {e}")

        log.info(
            f"[{file_id}] Done — Integrity: {final_result['authenticity_index']}% | "
            f"Modules Flagged: {final_result['modules_flagged']}/6"
        )

        return JSONResponse(content=final_result)

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[{file_id}] Analysis failed: {e}", exc_info=True)
        # Clean up on failure
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
