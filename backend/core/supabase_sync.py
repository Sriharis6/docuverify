"""
DocuVerify — Supabase Cloud Sync Module
Synchronizes forensic analysis records and artifacts directly to Supabase.
"""

import os
import logging
from typing import Dict, Any, Optional

log = logging.getLogger("docuverify.supabase")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

_client = None

def get_supabase_client():
    global _client
    if _client is not None:
        return _client
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    
    try:
        from supabase import create_client, Client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _client
    except Exception as e:
        log.warning(f"Supabase client initialization skipped: {e}")
        return None


def sync_report_to_supabase(report: Dict[str, Any]) -> Optional[str]:
    """
    Saves an analysis report directly to the Supabase verification_reports table.
    Returns the generated database record ID, or None if skipped/failed.
    """
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        fi = report.get("file_info", {})
        payload = {
            "file_id": fi.get("file_id", "unknown"),
            "filename": fi.get("filename", "unknown"),
            "size_kb": fi.get("size_kb", 0),
            "extension": fi.get("extension", ""),
            "authenticity_index": report.get("authenticity_index", 100),
            "risk_index": report.get("risk_index", 0),
            "modules_flagged": report.get("modules_flagged", 0),
            "total_anomalies": report.get("total_anomalies", 0),
            "integrity_label": report.get("integrity_label", "Authentic"),
            "summary_report": report.get("summary_report", ""),
            "test_cases": report.get("test_cases", []),
            "regions": report.get("regions", []),
            "visualizations": report.get("visualizations", {}),
        }
        
        res = client.table("verification_reports").insert(payload).execute()
        if res.data and len(res.data) > 0:
            inserted_id = res.data[0].get("id")
            log.info(f"Report synced to Supabase successfully with ID: {inserted_id}")
            return inserted_id
    except Exception as e:
        log.warning(f"Failed to sync report to Supabase: {e}")
    return None
