"""
fusion.py — Multi-Signal Weighted Fusion & Forensic Report Generator
Combines outputs from 6 independent forensic modules into a structured audit report.
Each module result is represented as a structured TestCase with numerical scoring.
"""

def _risk_label(score: float) -> str:
    """Maps a 0–1 risk score to a human-readable severity label."""
    if score >= 0.60:
        return "Critical"
    elif score >= 0.40:
        return "High"
    elif score >= 0.20:
        return "Moderate"
    elif score >= 0.08:
        return "Low"
    return "Minimal"

def _confidence(score: float) -> str:
    """Maps score to a confidence statement."""
    if score >= 0.75:
        return "Very High"
    elif score >= 0.50:
        return "High"
    elif score >= 0.25:
        return "Moderate"
    elif score >= 0.08:
        return "Low"
    return "Negligible"

def _test_verdict(score: float, flagged: bool) -> str:
    """
    Returns a descriptive forensic finding label — NOT a binary FAKE/GENUINE.
    The system describes WHAT was found and HOW SEVERE it is.
    """
    if not flagged and score < 0.08:
        return "No Anomalies Detected"
    elif not flagged and score < 0.25:
        return "Within Normal Parameters"
    elif score < 0.25:
        return "Minor Irregularities Present"
    elif score < 0.45:
        return "Anomalies Detected — Further Review Suggested"
    elif score < 0.70:
        return "Significant Anomalies Detected"
    else:
        return "Multiple High-Confidence Anomalies"


def fuse_results(ela_res, cm_res, meta_res, ocr_res, typo_res=None, align_res=None):
    """
    Multi-Signal Weighted Fusion & Granular Telemetry Engine.
    Combines outputs from 6 forensic modules into:
      - authenticity_index (0–100): higher = more intact
      - risk_index (0–100): higher = more anomalies
      - test_cases[]: per-module structured forensic scoring cards
      - regions[]: bounding box annotations for image overlay
      - summary_report: human-readable forensic audit conclusion
    """
    if typo_res is None:
        typo_res = {"score": 0.0, "explanation": "Typography module not executed.", "flagged": False, "regions": []}
    if align_res is None:
        align_res = {"score": 0.0, "explanation": "Alignment module not executed.", "flagged": False, "regions": []}

    # ── Weights (must sum to 1.0) ─────────────────────────────────────────────
    weights = {
        'ela':        0.20,
        'copy_move':  0.20,
        'typography': 0.18,
        'alignment':  0.14,
        'ocr':        0.14,
        'metadata':   0.14,
    }

    s_ela   = float(ela_res.get('score', 0.0))
    s_cm    = float(cm_res.get('score', 0.0))
    s_typo  = float(typo_res.get('score', 0.0))
    s_align = float(align_res.get('score', 0.0))
    s_ocr   = float(ocr_res.get('score', 0.0))
    s_meta  = float(meta_res.get('score', 0.0))

    base_risk = (
        (s_ela   * weights['ela']) +
        (s_cm    * weights['copy_move']) +
        (s_typo  * weights['typography']) +
        (s_align * weights['alignment']) +
        (s_ocr   * weights['ocr']) +
        (s_meta  * weights['metadata'])
    )

    # If any single module flags a high-confidence anomaly, it pulls up overall risk
    flagged_scores = [
        s for (s, res) in [
            (s_ela, ela_res), (s_cm, cm_res), (s_typo, typo_res),
            (s_align, align_res), (s_ocr, ocr_res), (s_meta, meta_res)
        ] if res.get('flagged')
    ]

    if flagged_scores:
        max_flag = max(flagged_scores)
        overall_risk = max(base_risk, max_flag * 0.72)
    else:
        overall_risk = base_risk

    # ── Aggregate anomaly regions ─────────────────────────────────────────────
    all_regions = []
    reg_id_counter = 1
    for mod_name, res in [
        ("ELA", ela_res), ("Copy-Move", cm_res), ("Typography", typo_res),
        ("Alignment", align_res), ("OCR/Logic", ocr_res)
    ]:
        for r in res.get('regions', []):
            item = dict(r)
            item["id"]        = f"r{reg_id_counter}"
            item["module"]    = mod_name
            item["page"]      = 1
            item["findingId"] = f"F{reg_id_counter}"
            all_regions.append(item)
            reg_id_counter += 1

    # ── Build structured test case cards ─────────────────────────────────────
    module_defs = [
        {
            "id": "ela",
            "name": "Error Level Analysis",
            "category": "Pixel Compression Forensics",
            "description": "Detects localized JPEG re-compression anomalies caused by copy-paste or content insertion.",
            "score": s_ela,
            "res": ela_res,
            "weight_pct": int(weights['ela'] * 100),
            "test_criteria": [
                "Compression variance uniformity across image blocks",
                "High-frequency noise distribution analysis",
                "Re-save artifact localization",
            ],
        },
        {
            "id": "copy_move",
            "name": "Copy-Move Cloning Detection",
            "category": "Feature Keypoint Analysis",
            "description": "Identifies duplicate regions or cloned content using SIFT/ORB feature matching across the document.",
            "score": s_cm,
            "res": cm_res,
            "weight_pct": int(weights['copy_move'] * 100),
            "test_criteria": [
                "Keypoint descriptor matching (SIFT/ORB)",
                "Spatial distance between matched pairs",
                "Cluster bounding box extraction",
            ],
        },
        {
            "id": "typography",
            "name": "Typography Consistency",
            "category": "Font & Rendering Analysis",
            "description": "Checks consistency of font stroke width, character height, and anti-aliasing across all text blocks.",
            "score": s_typo,
            "res": typo_res,
            "weight_pct": int(weights['typography'] * 100),
            "test_criteria": [
                "Edge density (stroke width proxy) per text block",
                "Character height distribution z-score",
                "Anti-aliasing pattern uniformity",
            ],
        },
        {
            "id": "alignment",
            "name": "Text Baseline & Layout Skew",
            "category": "Geometric Structural Analysis",
            "description": "Measures text baseline angles and line spacing to identify inserted or repositioned text fields.",
            "score": s_align,
            "res": align_res,
            "weight_pct": int(weights['alignment'] * 100),
            "test_criteria": [
                "Horizontal text line angle extraction",
                "Baseline skew deviation from document median",
                "Inter-line vertical spacing variance",
            ],
        },
        {
            "id": "ocr",
            "name": "OCR & Logical Integrity",
            "category": "Semantic Content Validation",
            "description": "Extracts text via OCR and validates logical consistency of dates, ID numbers, and field sequences.",
            "score": s_ocr,
            "res": ocr_res,
            "weight_pct": int(weights['ocr'] * 100),
            "test_criteria": [
                "Date chronology validation (Expiry ≥ Issue ≥ DOB)",
                "ID checksum format validation",
                "Temporal sequence plausibility",
            ],
        },
        {
            "id": "metadata",
            "name": "EXIF & Document Metadata",
            "category": "File Provenance Audit",
            "description": "Audits embedded EXIF or PDF metadata for editing software signatures, date anomalies, or stripped fields.",
            "score": s_meta,
            "res": meta_res,
            "weight_pct": int(weights['metadata'] * 100),
            "test_criteria": [
                "Software tag screening (Photoshop, GIMP, Canva, etc.)",
                "Creation vs. modification date consistency",
                "Metadata stream completeness",
            ],
        },
    ]

    test_cases = []
    for m in module_defs:
        s     = m["score"]
        res   = m["res"]
        count = len(res.get("regions", []))
        tc = {
            "id":            m["id"],
            "name":          m["name"],
            "category":      m["category"],
            "description":   m["description"],
            "score_pct":     round(s * 100.0, 1),
            "weight_pct":    m["weight_pct"],
            "risk_level":    _risk_label(s),
            "confidence":    _confidence(s),
            "flagged":       bool(res.get("flagged", False)),
            "anomaly_count": count,
            "verdict":       _test_verdict(s, bool(res.get("flagged", False))),
            "finding":       res.get("explanation", "Analysis complete."),
            "test_criteria": m["test_criteria"],
            "regions":       res.get("regions", []),
        }
        # Carry module-specific extra fields
        if m["id"] == "ela":
            tc["variance"] = res.get("variance")
        if m["id"] == "copy_move":
            tc["num_matches"] = res.get("num_matches", 0)
        if m["id"] == "metadata":
            tc["items"] = res.get("items", [])
        if m["id"] == "ocr":
            tc["extracted_text_preview"] = res.get("extracted_text_preview", "")
        if m["id"] == "alignment":
            tc["details"] = res.get("details", {})
        test_cases.append(tc)

    # ── Compute final scores ──────────────────────────────────────────────────
    authenticity_index = max(0.0, min(100.0, (1.0 - overall_risk) * 100.0))
    risk_index         = max(0.0, min(100.0, overall_risk * 100.0))

    total_flagged  = sum(1 for tc in test_cases if tc["flagged"])
    total_anomalies = sum(tc["anomaly_count"] for tc in test_cases)

    # ── Forensic audit findings log ──────────────────────────────────────────
    audit_findings = []
    labels = {
        "ela":        "Compression ELA",
        "copy_move":  "Copy-Move Cloning",
        "typography": "Typography Audit",
        "alignment":  "Baseline Alignment",
        "ocr":        "OCR Logical Validation",
        "metadata":   "Metadata Audit",
    }
    for tc in test_cases:
        if tc["flagged"]:
            audit_findings.append(f"[{labels[tc['id']]}] {tc['finding']}")

    if not audit_findings:
        audit_findings.append(
            "All 6 forensic verification modules completed without flagging critical anomalies. "
            "Document structure, compression, typography, and metadata are within expected parameters."
        )

    # ── Human-readable forensic summary ──────────────────────────────────────
    if total_flagged == 0:
        integrity_label = "High Integrity"
        summary_tone = (
            f"The document passed all {len(test_cases)} forensic verification modules. "
            f"No significant anomalies were detected in compression patterns, pixel structure, "
            f"typographic consistency, baseline alignment, OCR logical fields, or file metadata."
        )
    elif total_flagged == 1:
        integrity_label = "Marginal Integrity"
        tc_name = next(tc['name'] for tc in test_cases if tc['flagged'])
        summary_tone = (
            f"One forensic module ({tc_name}) returned findings outside expected parameters. "
            f"A total of {total_anomalies} localized anomaly region(s) were identified. "
            f"This may indicate a partial modification or may result from image compression artifacts."
        )
    elif total_flagged <= 3:
        integrity_label = "Compromised Integrity"
        flagged_names = [tc['name'] for tc in test_cases if tc['flagged']]
        summary_tone = (
            f"{total_flagged} of {len(test_cases)} forensic modules returned anomalies: "
            f"{', '.join(flagged_names)}. "
            f"A total of {total_anomalies} region(s) were flagged. "
            f"The convergence of findings across multiple independent modules suggests a higher probability of intentional modification."
        )
    else:
        integrity_label = "Severely Compromised Integrity"
        summary_tone = (
            f"{total_flagged} of {len(test_cases)} forensic modules detected significant anomalies. "
            f"Total of {total_anomalies} region(s) flagged across compression, structural, and semantic checks. "
            f"The breadth and depth of findings indicate high-confidence evidence of document manipulation."
        )

    # ── Telemetry matrix (legacy format, kept for backward compat) ────────────
    telemetry_matrix = [
        {
            "category":   tc["name"],
            "key":        tc["id"],
            "score_pct":  tc["score_pct"],
            "risk_level": tc["risk_level"],
            "finding":    tc["finding"],
        }
        for tc in test_cases
    ]

    return {
        "authenticity_index":  round(authenticity_index, 1),
        "risk_index":          round(risk_index, 1),
        "overall_score":       round(float(overall_risk), 3),
        "integrity_label":     integrity_label,
        "modules_flagged":     total_flagged,
        "total_anomalies":     total_anomalies,
        "test_cases":          test_cases,
        "telemetry_matrix":    telemetry_matrix,
        "audit_summary":       "\n".join(audit_findings),
        "summary_report":      summary_tone,
        "regions":             all_regions,
        "module_breakdown": {
            "ela":        ela_res,
            "copy_move":  cm_res,
            "typography": typo_res,
            "alignment":  align_res,
            "ocr":        ocr_res,
            "metadata":   meta_res,
        },
    }
