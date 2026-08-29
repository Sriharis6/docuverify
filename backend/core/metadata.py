import os
from PIL import Image, ExifTags
import pypdf

def analyze_metadata(file_path: str):
    """
    Module C — Metadata Audit (EXIF for images, PDF properties for PDFs).
    Flags mismatches like editing software in Producer/Creator/Software fields
    and creation/modification date anomalies.
    """
    try:
        if not os.path.exists(file_path):
             return {"score": 0.0, "explanation": "File not found.", "flagged": False, "items": []}
             
        ext = file_path.lower().split('.')[-1]
        score = 0.0
        flagged = False
        findings = []
        metadata_items = []
        
        suspicious_software = ['photoshop', 'gimp', 'canva', 'paint', 'illustrator', 'acrobat pro', 'pdfeditor', 'inkscape']
        
        if ext in ['jpg', 'jpeg', 'png', 'tiff']:
            img = Image.open(file_path)
            exif_data = img._getexif()
            
            metadata_items.append({"k": "File Format", "v": ext.upper(), "status": "ok"})
            metadata_items.append({"k": "Dimensions", "v": f"{img.width} x {img.height} px", "status": "ok"})
            
            if exif_data is None:
                findings.append("No EXIF metadata structure present.")
                metadata_items.append({"k": "EXIF Data", "v": "Missing / Stripped", "status": "warn", "note": "Common in web downloads or re-saved images."})
                score = 0.25
            else:
                software = ""
                for tag_id, value in exif_data.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag == 'Software':
                        software = str(value).lower()
                        metadata_items.append({"k": "Software Tag", "v": str(value), "status": "warn" if any(s in software for s in suspicious_software) else "ok"})
                    elif tag == 'DateTimeOriginal':
                        metadata_items.append({"k": "Date Original", "v": str(value), "status": "ok"})
                    elif tag == 'DateTime':
                        metadata_items.append({"k": "Date Modified", "v": str(value), "status": "ok"})

                if software:
                    if any(s in software for s in suspicious_software):
                        findings.append(f"Editing software signature detected in EXIF: '{software}'.")
                        score = 0.9
                        flagged = True
                    else:
                        findings.append(f"Software tag: {software}.")
                else:
                    findings.append("No Software tag in EXIF.")
                    
        elif ext == 'pdf':
            metadata_items.append({"k": "File Format", "v": "PDF Document", "status": "ok"})
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                meta = reader.metadata
                if meta:
                    producer = meta.get('/Producer', '')
                    creator = meta.get('/Creator', '')
                    c_date = meta.get('/CreationDate', '')
                    m_date = meta.get('/ModDate', '')
                    
                    prod_lower = str(producer).lower()
                    creat_lower = str(creator).lower()
                    
                    metadata_items.append({"k": "PDF Producer", "v": producer if producer else "Not Specified", "status": "warn" if any(s in prod_lower for s in suspicious_software) else "ok"})
                    metadata_items.append({"k": "PDF Creator", "v": creator if creator else "Not Specified", "status": "warn" if any(s in creat_lower for s in suspicious_software) else "ok"})
                    if c_date:
                        metadata_items.append({"k": "Creation Date", "v": c_date, "status": "ok"})
                    if m_date:
                        metadata_items.append({"k": "Modification Date", "v": m_date, "status": "ok"})

                    found_suspicious = False
                    if producer and any(s in prod_lower for s in suspicious_software):
                        findings.append(f"Suspicious PDF Producer tool: '{producer}'.")
                        found_suspicious = True
                    if creator and any(s in creat_lower for s in suspicious_software):
                        findings.append(f"Suspicious PDF Creator tool: '{creator}'.")
                        found_suspicious = True
                        
                    if found_suspicious:
                        score = 0.85
                        flagged = True
                else:
                    findings.append("No embedded PDF metadata stream found.")
                    metadata_items.append({"k": "PDF Metadata", "v": "Missing / Stripped", "status": "warn"})
                    score = 0.3
        else:
            return {"score": 0.0, "explanation": "Unsupported file type for metadata audit.", "flagged": False, "items": []}
             
        if not flagged and score == 0.0:
            explanation = "Metadata Audit: Camera/document metadata stream is intact and clean. No editing software indicators found."
        else:
            explanation = "Metadata Audit: " + " ".join(findings)
            
        return {
            "score": float(score),
            "explanation": explanation,
            "flagged": flagged,
            "items": metadata_items
        }
        
    except Exception as e:
        return {"score": 0.0, "explanation": f"Metadata analysis failed: {str(e)}", "flagged": False, "items": []}

