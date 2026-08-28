"""
DocuVerify — Sample Dataset Generator
Generates synthetic document images for demonstration and testing.

Documents Generated:
  dataset/genuine/
    genuine_certificate.jpg   — Clean academic certificate
    genuine_id_card.jpg       — Clean national ID card

  dataset/tampered/
    tampered_date_altered.jpg  — ID card with impossible expiry date (before issue)
    tampered_copy_move.jpg     — Certificate with copy-pasted text block
    tampered_ela_artifact.jpg  — Document with ELA-detectable JPEG re-save artifact

Run:
    python dataset_generator.py
"""

import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance
import io

# ── Directories ─────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
GENUINE_DIR = os.path.join(BASE, "dataset", "genuine")
TAMPERED_DIR = os.path.join(BASE, "dataset", "tampered")
os.makedirs(GENUINE_DIR, exist_ok=True)
os.makedirs(TAMPERED_DIR, exist_ok=True)

# ── Font helpers ─────────────────────────────────────────────────────────────
def get_font(size=14, bold=False):
    """Try system fonts; fall back to PIL default."""
    candidates_bold = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/trebucbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    candidates_regular = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/trebuc.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    pool = candidates_bold if bold else candidates_regular
    for p in pool:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def get_mono_font(size=12):
    candidates = [
        "C:/Windows/Fonts/cour.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


# ── Color Palette ─────────────────────────────────────────────────────────────
WHITE  = (255, 255, 255)
OFF_WHITE = (248, 246, 242)
CREAM  = (245, 241, 232)
BLACK  = (20, 20, 20)
DARK   = (40, 40, 55)
NAVY   = (18, 38, 88)
GRAY   = (130, 130, 140)
LGRAY  = (200, 200, 205)
GOLD   = (180, 145, 55)
LGOLD  = (215, 185, 95)
RED    = (160, 30, 40)
BLUE   = (30, 60, 140)
GREEN  = (30, 110, 60)

def draw_border_pattern(draw, w, h, color, margin=14, thickness=2):
    """Draws a double-line official border."""
    draw.rectangle([margin, margin, w-margin, h-margin], outline=color, width=thickness)
    draw.rectangle([margin+6, margin+6, w-margin-6, h-margin-6], outline=color, width=1)

def draw_horizontal_rule(draw, y, x0, x1, color=GRAY, width=1):
    draw.line([(x0, y), (x1, y)], fill=color, width=width)

def draw_field_line(draw, font, x, y, label, value, label_color=GRAY, value_color=BLACK, gap=130):
    draw.text((x, y), label + ":", font=font, fill=label_color)
    draw.text((x + gap, y), value, font=font, fill=value_color)

def add_watermark(img, text="SPECIMEN", opacity=18):
    """Adds a diagonal watermark text."""
    wm = Image.new("RGBA", img.size, (0,0,0,0))
    draw = ImageDraw.Draw(wm)
    font = get_font(62, bold=True)
    draw.text((img.width//2 - 110, img.height//2 - 30), text, font=font, fill=(0,0,0, opacity))
    wm = wm.rotate(30, expand=False)
    result = Image.alpha_composite(img.convert("RGBA"), wm)
    return result.convert("RGB")

# ── Document 1: Genuine Certificate ──────────────────────────────────────────
def make_genuine_certificate():
    W, H = 900, 640
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    # Background texture (subtle noise)
    for _ in range(6000):
        px = random.randint(0, W-1)
        py = random.randint(0, H-1)
        noise = random.randint(-6, 6)
        r, g, b = CREAM
        img.putpixel((px, py), (max(0,min(255,r+noise)), max(0,min(255,g+noise)), max(0,min(255,b+noise))))

    # Top color band
    draw.rectangle([0, 0, W, 52], fill=NAVY)
    draw.rectangle([0, 52, W, 60], fill=GOLD)

    # Bottom band
    draw.rectangle([0, H-52, W, H], fill=NAVY)
    draw.rectangle([0, H-60, W, H-52], fill=GOLD)

    # Border
    draw_border_pattern(draw, W, H, NAVY, margin=18, thickness=2)

    # Header
    font_title = get_font(11, bold=True)
    font_inst = get_font(26, bold=True)
    font_body = get_font(14)
    font_name = get_font(34, bold=True)
    font_degree = get_font(18)
    font_mono = get_mono_font(10)

    draw.text((W//2, 16), "GOVERNMENT OF INDIA — MINISTRY OF EDUCATION", font=font_title, fill=WHITE, anchor="mm")
    draw.text((W//2, 110), "NATIONAL INSTITUTE OF TECHNOLOGY", font=font_inst, fill=NAVY, anchor="mm")
    draw.text((W//2, 148), "TIRUCHIRAPALLI — ESTABLISHED 1964", font=get_font(11), fill=GRAY, anchor="mm")

    # Horizontal rules
    draw_horizontal_rule(draw, 168, 60, W-60, GOLD, 2)
    draw_horizontal_rule(draw, 172, 60, W-60, NAVY, 1)

    # Main text
    draw.text((W//2, 205), "CERTIFICATE OF ACHIEVEMENT", font=get_font(13, bold=True), fill=GOLD, anchor="mm")
    draw.text((W//2, 232), "This is to certify that", font=get_font(14), fill=DARK, anchor="mm")

    # Name
    draw.text((W//2, 278), "Arjun Ramakrishnan Nair", font=font_name, fill=NAVY, anchor="mm")
    draw_horizontal_rule(draw, 304, 220, W-220, NAVY, 1)

    # Degree text
    draw.text((W//2, 328), "has successfully completed the programme of study and fulfilled all", font=font_body, fill=DARK, anchor="mm")
    draw.text((W//2, 352), "requirements for the award of the degree of", font=font_body, fill=DARK, anchor="mm")

    draw.text((W//2, 388), "Bachelor of Technology in Computer Science and Engineering", font=font_degree, fill=RED, anchor="mm")

    draw.text((W//2, 420), "with First Class Distinction — CGPA: 9.34 / 10.00", font=get_font(13), fill=DARK, anchor="mm")

    # Date + Signature row
    draw_horizontal_rule(draw, 460, 60, W-60, LGRAY, 1)
    draw.text((140, 488), "Date of Award:", font=font_mono, fill=GRAY)
    draw.text((140, 506), "15 June 2024", font=get_font(13, bold=True), fill=DARK)

    draw.text((W//2, 488), "Certificate No:", font=font_mono, fill=GRAY, anchor="mm")
    draw.text((W//2, 506), "NIT/CS/2024/0734", font=get_mono_font(13), fill=DARK, anchor="mm")

    draw.text((W-140, 488), "Issued On:", font=font_mono, fill=GRAY, anchor="rm")
    draw.text((W-140, 506), "20 June 2024", font=get_font(13, bold=True), fill=DARK, anchor="rm")

    # Signature lines
    for sx in [140, W//2 - 60, W - 200]:
        draw_horizontal_rule(draw, 555, sx, sx + 120, DARK, 1)
    draw.text((200, 560), "Registrar", font=font_mono, fill=GRAY, anchor="mm")
    draw.text((W//2, 560), "Director", font=font_mono, fill=GRAY, anchor="mm")
    draw.text((W-140, 560), "Controller of Examinations", font=font_mono, fill=GRAY, anchor="mm")

    # Seal circle
    draw.ellipse([W//2-38, 540, W//2+38, 616], outline=GOLD, width=3)
    draw.ellipse([W//2-32, 546, W//2+32, 610], outline=NAVY, width=1)
    draw.text((W//2, 578), "OFFICIAL\nSEAL", font=get_font(9, bold=True), fill=NAVY, anchor="mm", align="center")

    # Footer text in bands
    draw.text((W//2, H-38), "Verify at: verify.nittr.ac.in | Helpdesk: coe@nittr.ac.in | +91-431-250-3000", font=get_mono_font(9), fill=LGOLD, anchor="mm")

    img = add_watermark(img, "SPECIMEN", 12)
    path = os.path.join(GENUINE_DIR, "genuine_certificate.jpg")
    img.save(path, "JPEG", quality=95)
    print(f"[OK] {path}")
    return path


# ── Document 2: Genuine ID Card ───────────────────────────────────────────────
def make_genuine_id_card():
    W, H = 760, 480
    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # Background
    for _ in range(4000):
        px, py = random.randint(0, W-1), random.randint(0, H-1)
        n = random.randint(-4, 4)
        r, g, b = WHITE
        img.putpixel((px, py), (max(0,min(255,r+n)), max(0,min(255,g+n)), max(0,min(255,b+n))))

    # Left color sidebar
    draw.rectangle([0, 0, 8, H], fill=NAVY)
    draw.rectangle([8, 0, 14, H], fill=GOLD)

    # Header bar
    draw.rectangle([14, 0, W, 72], fill=NAVY)
    draw.rectangle([14, 72, W, 80], fill=GOLD)

    # Header text
    draw.text((W//2 + 20, 18), "NATIONAL IDENTITY AUTHORITY OF INDIA", font=get_font(12, bold=True), fill=WHITE, anchor="mm")
    draw.text((W//2 + 20, 44), "AADHAAR-LINKED CITIZEN IDENTITY CARD", font=get_font(10), fill=LGOLD, anchor="mm")
    draw.text((W//2 + 20, 62), "Ministry of Home Affairs — Government of India", font=get_font(9), fill=LGRAY, anchor="mm")

    # Photo box
    draw.rectangle([28, 92, 148, 212], outline=NAVY, width=2)
    draw.rectangle([30, 94, 146, 210], fill=(230,230,235))
    draw.text((88, 152), "PHOTO", font=get_font(10), fill=LGRAY, anchor="mm")
    draw.text((88, 168), "HERE", font=get_font(10), fill=LGRAY, anchor="mm")

    # ID number bar under photo
    draw.rectangle([28, 216, 148, 234], fill=NAVY)
    draw.text((88, 225), "UID: 4521 8834 6612", font=get_mono_font(8), fill=WHITE, anchor="mm")

    # Fields
    fnt_label = get_mono_font(9)
    fnt_value = get_font(13, bold=True)
    fnt_val_reg = get_font(12)
    fnt_mono = get_mono_font(11)

    fx = 168
    draw.text((fx, 96), "FULL NAME", font=fnt_label, fill=GRAY)
    draw.text((fx, 112), "PRIYA VENKATARAMAN SUBRAMANIAM", font=get_font(14, bold=True), fill=DARK)
    draw_horizontal_rule(draw, 134, fx, W-24, LGRAY)

    draw.text((fx, 140), "DATE OF BIRTH", font=fnt_label, fill=GRAY)
    draw.text((fx, 156), "14 March 1992", font=fnt_value, fill=DARK)

    draw.text((fx + 200, 140), "GENDER", font=fnt_label, fill=GRAY)
    draw.text((fx + 200, 156), "Female", font=fnt_value, fill=DARK)

    draw_horizontal_rule(draw, 178, fx, W-24, LGRAY)

    draw.text((fx, 186), "ADDRESS", font=fnt_label, fill=GRAY)
    draw.text((fx, 202), "42, Anna Nagar 4th Street, Chennai — 600 040", font=fnt_val_reg, fill=DARK)
    draw.text((fx, 220), "Tamil Nadu, India", font=fnt_val_reg, fill=DARK)

    draw_horizontal_rule(draw, 244, fx, W-24, LGRAY)

    draw.text((fx, 252), "ISSUE DATE", font=fnt_label, fill=GRAY)
    draw.text((fx, 268), "10 January 2020", font=fnt_value, fill=DARK)

    draw.text((fx + 200, 252), "EXPIRY DATE", font=fnt_label, fill=GRAY)
    draw.text((fx + 200, 268), "09 January 2030", font=fnt_value, fill=GREEN)  # Valid date

    draw_horizontal_rule(draw, 292, fx, W-24, LGRAY)

    draw.text((fx, 300), "CARD NO.", font=fnt_label, fill=GRAY)
    draw.text((fx, 316), "IND/TN/2020/A4521883", font=fnt_mono, fill=DARK)

    # Bottom footer
    draw.rectangle([14, H-68, W, H-4], fill=(245,245,248))
    draw_horizontal_rule(draw, H-68, 14, W, LGRAY)
    draw.text((W//2+20, H-50), "This card is the property of Government of India. If found, please return to nearest police station.", font=get_font(8), fill=GRAY, anchor="mm")
    draw.text((W//2+20, H-32), "Verify authenticity: www.uidai.gov.in  |  Helpline: 1947  |  Valid across all states of India", font=get_mono_font(8), fill=GRAY, anchor="mm")

    # MRZ-like strip
    draw.rectangle([14, H-18, W, H-4], fill=NAVY)
    mrz = "IND<<VENKATARAMAN<<PRIYA<<<<<<<<<<<<<<<<<<<<<<<<<"
    draw.text((W//2+20, H-11), mrz, font=get_mono_font(7), fill=WHITE, anchor="mm")

    path = os.path.join(GENUINE_DIR, "genuine_id_card.jpg")
    img.save(path, "JPEG", quality=95)
    print(f"[OK] {path}")
    return path


# ── Document 3: Tampered — Date Altered (Expiry before Issue) ─────────────────
def make_tampered_date_altered():
    W, H = 760, 480
    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # Same base as genuine ID
    for _ in range(4000):
        px, py = random.randint(0, W-1), random.randint(0, H-1)
        n = random.randint(-4, 4)
        img.putpixel((px, py), (max(0,min(255,255+n)), max(0,min(255,255+n)), max(0,min(255,255+n))))

    draw.rectangle([0, 0, 8, H], fill=NAVY)
    draw.rectangle([8, 0, 14, H], fill=GOLD)
    draw.rectangle([14, 0, W, 72], fill=NAVY)
    draw.rectangle([14, 72, W, 80], fill=GOLD)

    draw.text((W//2 + 20, 18), "NATIONAL IDENTITY AUTHORITY OF INDIA", font=get_font(12, bold=True), fill=WHITE, anchor="mm")
    draw.text((W//2 + 20, 44), "AADHAAR-LINKED CITIZEN IDENTITY CARD", font=get_font(10), fill=LGOLD, anchor="mm")
    draw.text((W//2 + 20, 62), "Ministry of Home Affairs — Government of India", font=get_font(9), fill=LGRAY, anchor="mm")

    draw.rectangle([28, 92, 148, 212], outline=NAVY, width=2)
    draw.rectangle([30, 94, 146, 210], fill=(230,230,235))
    draw.text((88, 152), "PHOTO", font=get_font(10), fill=LGRAY, anchor="mm")
    draw.text((88, 168), "HERE", font=get_font(10), fill=LGRAY, anchor="mm")
    draw.rectangle([28, 216, 148, 234], fill=NAVY)
    draw.text((88, 225), "UID: 4521 8834 6612", font=get_mono_font(8), fill=WHITE, anchor="mm")

    fnt_label = get_mono_font(9)
    fnt_value = get_font(13, bold=True)
    fnt_val_reg = get_font(12)
    fnt_mono = get_mono_font(11)

    fx = 168
    draw.text((fx, 96), "FULL NAME", font=fnt_label, fill=GRAY)
    draw.text((fx, 112), "PRIYA VENKATARAMAN SUBRAMANIAM", font=get_font(14, bold=True), fill=DARK)
    draw_horizontal_rule(draw, 134, fx, W-24, LGRAY)

    draw.text((fx, 140), "DATE OF BIRTH", font=fnt_label, fill=GRAY)
    draw.text((fx, 156), "14 March 1992", font=fnt_value, fill=DARK)
    draw.text((fx + 200, 140), "GENDER", font=fnt_label, fill=GRAY)
    draw.text((fx + 200, 156), "Female", font=fnt_value, fill=DARK)
    draw_horizontal_rule(draw, 178, fx, W-24, LGRAY)

    draw.text((fx, 186), "ADDRESS", font=fnt_label, fill=GRAY)
    draw.text((fx, 202), "42, Anna Nagar 4th Street, Chennai — 600 040", font=fnt_val_reg, fill=DARK)
    draw.text((fx, 220), "Tamil Nadu, India", font=fnt_val_reg, fill=DARK)
    draw_horizontal_rule(draw, 244, fx, W-24, LGRAY)

    draw.text((fx, 252), "ISSUE DATE", font=fnt_label, fill=GRAY)
    draw.text((fx, 268), "10 January 2020", font=fnt_value, fill=DARK)

    # TAMPERED: Expiry date is BEFORE issue date — impossible!
    draw.text((fx + 200, 252), "EXPIRY DATE", font=fnt_label, fill=GRAY)

    # Simulate pasted-over text (slightly different background)
    paste_x, paste_y = fx + 200, 262
    draw.rectangle([paste_x-2, paste_y-2, paste_x+148, paste_y+22], fill=(252,250,248))
    draw.text((paste_x, paste_y+4), "01 January 2010", font=fnt_value, fill=RED)

    draw_horizontal_rule(draw, 292, fx, W-24, LGRAY)

    draw.text((fx, 300), "CARD NO.", font=fnt_label, fill=GRAY)
    draw.text((fx, 316), "IND/TN/2020/A4521883", font=fnt_mono, fill=DARK)

    draw.rectangle([14, H-68, W, H-4], fill=(245,245,248))
    draw_horizontal_rule(draw, H-68, 14, W, LGRAY)
    draw.text((W//2+20, H-50), "This card is the property of Government of India. If found, please return to nearest police station.", font=get_font(8), fill=GRAY, anchor="mm")
    draw.text((W//2+20, H-32), "Verify authenticity: www.uidai.gov.in  |  Helpline: 1947  |  Valid across all states of India", font=get_mono_font(8), fill=GRAY, anchor="mm")
    draw.rectangle([14, H-18, W, H-4], fill=NAVY)
    mrz = "IND<<VENKATARAMAN<<PRIYA<<<<<<<<<<<<<<<<<<<<<<<<<"
    draw.text((W//2+20, H-11), mrz, font=get_mono_font(7), fill=WHITE, anchor="mm")

    path = os.path.join(TAMPERED_DIR, "tampered_date_altered.jpg")
    img.save(path, "JPEG", quality=95)
    print(f"[OK] {path}")
    return path


# ── Document 4: Tampered — Copy-Move (Duplicated Text Block) ──────────────────
def make_tampered_copy_move():
    W, H = 900, 640
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    for _ in range(6000):
        px, py = random.randint(0, W-1), random.randint(0, H-1)
        n = random.randint(-5, 5)
        r, g, b = CREAM
        img.putpixel((px, py), (max(0,min(255,r+n)), max(0,min(255,g+n)), max(0,min(255,b+n))))

    draw.rectangle([0, 0, W, 52], fill=NAVY)
    draw.rectangle([0, 52, W, 60], fill=GOLD)
    draw.rectangle([0, H-52, W, H], fill=NAVY)
    draw.rectangle([0, H-60, W, H-52], fill=GOLD)
    draw_border_pattern(draw, W, H, NAVY, margin=18, thickness=2)

    draw.text((W//2, 16), "GOVERNMENT OF INDIA — MINISTRY OF EDUCATION", font=get_font(11, bold=True), fill=WHITE, anchor="mm")
    draw.text((W//2, 110), "NATIONAL INSTITUTE OF TECHNOLOGY", font=get_font(26, bold=True), fill=NAVY, anchor="mm")
    draw.text((W//2, 148), "TIRUCHIRAPALLI — ESTABLISHED 1964", font=get_font(11), fill=GRAY, anchor="mm")

    draw_horizontal_rule(draw, 168, 60, W-60, GOLD, 2)
    draw.text((W//2, 205), "CERTIFICATE OF ACHIEVEMENT", font=get_font(13, bold=True), fill=GOLD, anchor="mm")
    draw.text((W//2, 232), "This is to certify that", font=get_font(14), fill=DARK, anchor="mm")
    draw.text((W//2, 278), "Karthikeyan Murugesan Pillai", font=get_font(34, bold=True), fill=NAVY, anchor="mm")
    draw_horizontal_rule(draw, 304, 220, W-220, NAVY, 1)

    draw.text((W//2, 328), "has successfully completed the programme of study and fulfilled all", font=get_font(14), fill=DARK, anchor="mm")
    draw.text((W//2, 352), "requirements for the award of the degree of", font=get_font(14), fill=DARK, anchor="mm")
    draw.text((W//2, 388), "Bachelor of Technology in Electronics and Communication Engineering", font=get_font(18), fill=RED, anchor="mm")
    draw.text((W//2, 420), "with First Class Distinction — CGPA: 8.91 / 10.00", font=get_font(13), fill=DARK, anchor="mm")

    draw_horizontal_rule(draw, 460, 60, W-60, LGRAY, 1)

    # Original stamp block
    draw.text((140, 488), "Date of Award:", font=get_mono_font(10), fill=GRAY)
    draw.text((140, 506), "15 June 2024", font=get_font(13, bold=True), fill=DARK)
    draw.text((W//2, 488), "Certificate No:", font=get_mono_font(10), fill=GRAY, anchor="mm")
    draw.text((W//2, 506), "NIT/EC/2024/0891", font=get_mono_font(13), fill=DARK, anchor="mm")
    draw.text((W-140, 488), "Issued On:", font=get_mono_font(10), fill=GRAY, anchor="rm")
    draw.text((W-140, 506), "20 June 2024", font=get_font(13, bold=True), fill=DARK, anchor="rm")

    for sx in [140, W//2 - 60, W - 200]:
        draw_horizontal_rule(draw, 555, sx, sx + 120, DARK, 1)
    draw.text((200, 560), "Registrar", font=get_mono_font(10), fill=GRAY, anchor="mm")
    draw.text((W//2, 560), "Director", font=get_mono_font(10), fill=GRAY, anchor="mm")
    draw.text((W-140, 560), "Controller of Examinations", font=get_mono_font(10), fill=GRAY, anchor="mm")

    draw.ellipse([W//2-38, 540, W//2+38, 616], outline=GOLD, width=3)
    draw.ellipse([W//2-32, 546, W//2+32, 610], outline=NAVY, width=1)
    draw.text((W//2, 578), "OFFICIAL\nSEAL", font=get_font(9, bold=True), fill=NAVY, anchor="mm", align="center")
    draw.text((W//2, H-38), "Verify at: verify.nittr.ac.in | Helpdesk: coe@nittr.ac.in | +91-431-250-3000", font=get_mono_font(9), fill=LGOLD, anchor="mm")

    # TAMPER: Copy-paste a grade block over the CGPA region
    # Source patch: copy from around (250, 330) to (650, 360)
    patch = img.crop((250, 330, 650, 365))
    # Slightly brighten to simulate pasted region
    patch = ImageEnhance.Brightness(patch).enhance(1.06)
    # Paste in a shifted location (CGPA area)
    img.paste(patch, (250, 406))

    # Draw new CGPA text over pasted area to make it look edited
    draw2 = ImageDraw.Draw(img)
    draw2.text((W//2, 420), "with First Class Distinction — CGPA: 9.87 / 10.00", font=get_font(13), fill=DARK, anchor="mm")

    path = os.path.join(TAMPERED_DIR, "tampered_copy_move.jpg")
    img.save(path, "JPEG", quality=95)
    print(f"[OK] {path}")
    return path


# ── Document 5: Tampered — ELA Artifact (Re-saved subsection) ────────────────
def make_tampered_ela_artifact():
    W, H = 760, 480
    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # Background
    for _ in range(4000):
        px, py = random.randint(0, W-1), random.randint(0, H-1)
        n = random.randint(-3, 3)
        img.putpixel((px, py), (max(0,min(255,255+n)), max(0,min(255,255+n)), max(0,min(255,255+n))))

    draw.rectangle([0, 0, 8, H], fill=NAVY)
    draw.rectangle([8, 0, 14, H], fill=GOLD)
    draw.rectangle([14, 0, W, 72], fill=NAVY)
    draw.rectangle([14, 72, W, 80], fill=GOLD)

    draw.text((W//2 + 20, 18), "NATIONAL INSTITUTE OF TECHNOLOGY — STUDENT RECORD", font=get_font(11, bold=True), fill=WHITE, anchor="mm")
    draw.text((W//2 + 20, 44), "ACADEMIC TRANSCRIPT — CONFIDENTIAL", font=get_font(10), fill=LGOLD, anchor="mm")
    draw.text((W//2 + 20, 62), "Office of the Controller of Examinations", font=get_font(9), fill=LGRAY, anchor="mm")

    fnt_label = get_mono_font(9)
    fnt_value = get_font(13, bold=True)

    fx = 30
    draw.text((fx, 96), "STUDENT NAME", font=fnt_label, fill=GRAY)
    draw.text((fx, 112), "RAHUL KRISHNASWAMY", font=fnt_value, fill=DARK)
    draw.text((fx+300, 96), "ROLL NUMBER", font=fnt_label, fill=GRAY)
    draw.text((fx+300, 112), "2020CS0142", font=get_mono_font(13), fill=DARK)
    draw_horizontal_rule(draw, 136, fx, W-24, LGRAY)

    draw.text((fx, 148), "PROGRAMME", font=fnt_label, fill=GRAY)
    draw.text((fx, 164), "B.Tech — Computer Science & Engineering (2020–2024)", font=get_font(12), fill=DARK)
    draw_horizontal_rule(draw, 188, fx, W-24, LGRAY)

    # Grade table
    draw.text((fx, 200), "SEMESTER-WISE GRADE SUMMARY", font=get_font(11, bold=True), fill=NAVY)
    draw_horizontal_rule(draw, 218, fx, W-24, NAVY, 2)

    headers = ["Semester", "Credits Earned", "SGPA", "Cumulative CGPA"]
    col_x = [fx, fx+140, fx+320, fx+460]
    for i, h in enumerate(headers):
        draw.text((col_x[i], 224), h, font=fnt_label, fill=GRAY)
    draw_horizontal_rule(draw, 238, fx, W-24, LGRAY)

    sems = [
        ("Semester I",   "24", "8.42", "8.42"),
        ("Semester II",  "22", "8.76", "8.58"),
        ("Semester III", "24", "8.91", "8.69"),
        ("Semester IV",  "24", "9.10", "8.80"),
        ("Semester V",   "22", "9.22", "8.88"),
        ("Semester VI",  "24", "9.08", "8.91"),
        ("Semester VII", "20", "9.34", "8.97"),
        ("Semester VIII","20", "9.41", "9.02"),
    ]
    for idx, (s, cr, sg, cg) in enumerate(sems):
        y = 248 + idx * 22
        row_bg = (248,248,248) if idx % 2 == 0 else WHITE
        draw.rectangle([fx-2, y-2, W-24, y+18], fill=row_bg)
        draw.text((col_x[0], y), s, font=get_font(11), fill=DARK)
        draw.text((col_x[1], y), cr, font=get_font(11), fill=DARK)
        draw.text((col_x[2], y), sg, font=get_font(11), fill=DARK)
        draw.text((col_x[3], y), cg, font=get_font(11), fill=DARK)

    draw_horizontal_rule(draw, 432, fx, W-24, NAVY, 2)
    draw.text((fx, 438), "FINAL CGPA:", font=get_font(12, bold=True), fill=NAVY)

    # ─── TAMPER: The CGPA value region is extracted, modified, re-saved at low
    #     quality and pasted back — classic ELA forensic artifact
    # First, save the whole image at high quality
    buf_high = io.BytesIO()
    img.save(buf_high, "JPEG", quality=95)

    # Crop a region (the CGPA area)
    crop_box = (fx + 120, 430, fx + 280, 458)

    # Write the tampered value on a clean white surface
    patch_img = Image.new("RGB", (160, 28), WHITE)
    patch_draw = ImageDraw.Draw(patch_img)
    patch_draw.text((4, 4), "9.87 / 10.00", font=get_font(14, bold=True), fill=GREEN)

    # Save patch at LOW quality to create detectable ELA artifact
    buf_low = io.BytesIO()
    patch_img.save(buf_low, "JPEG", quality=30)
    buf_low.seek(0)
    patch_low = Image.open(buf_low)

    # Save patch at medium quality again (layered re-saves = ELA artifact)
    buf_med = io.BytesIO()
    patch_low.save(buf_med, "JPEG", quality=65)
    buf_med.seek(0)
    patch_final = Image.open(buf_med)

    img.paste(patch_final, (fx + 120, 432))

    draw3 = ImageDraw.Draw(img)
    draw3.text((W-140, 442), "Pass Class: DISTINCTION", font=get_font(11, bold=True), fill=NAVY, anchor="rm")

    draw_horizontal_rule(draw3, H-68, 14, W, LGRAY)
    draw3.text((W//2+20, H-50), "This transcript is issued for official use only. Alteration or tampering is a punishable offence.", font=get_font(8), fill=GRAY, anchor="mm")
    draw3.text((W//2+20, H-32), "Verify at: verify.nittr.ac.in  |  Ref: NIT/EXAM/2024/TR-0142", font=get_mono_font(8), fill=GRAY, anchor="mm")

    path = os.path.join(TAMPERED_DIR, "tampered_ela_artifact.jpg")
    img.save(path, "JPEG", quality=92)
    print(f"[OK] {path}")
    return path


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\nDocuVerify — Sample Dataset Generator")
    print("=" * 44)
    make_genuine_certificate()
    make_genuine_id_card()
    make_tampered_date_altered()
    make_tampered_copy_move()
    make_tampered_ela_artifact()
    print("\nAll 5 sample documents generated successfully.")
    print(f"  Genuine  -> {GENUINE_DIR}")
    print(f"  Tampered -> {TAMPERED_DIR}")
