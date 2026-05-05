import os
import re
from datetime import datetime

import cv2
import numpy as np
import pandas as pd

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import easyocr
import uvicorn


try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None





# =========================
# App / Paths
# =========================
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EXCEL_PATH = os.path.join(BASE_DIR, "results.xlsx")
LAST_RECEIVED = os.path.join(BASE_DIR, "last_received.png")
LAST_WARPED   = os.path.join(BASE_DIR, "last_warped.png")
LAST_DEBUG    = os.path.join(BASE_DIR, "last_debug.png")

# سایز ثابت کارت بعد از warp
WARP_W, WARP_H = 1200, 760

# OCR
reader = easyocr.Reader(["fa", "en"], gpu=False)

# =========================
# Serve camera.html
# =========================
@app.get("/")
@app.get("/camera.html")
def camera_page():
    path = os.path.join(BASE_DIR, "camera.html")
    if not os.path.exists(path):
        raise HTTPException(404, "camera.html not found next to server.py")
    return FileResponse(path, media_type="text/html")

# =========================
# Debug endpoints
# =========================
@app.get("/last-image")
def last_image():
    if not os.path.exists(LAST_RECEIVED):
        raise HTTPException(404, "No image received yet")
    return FileResponse(LAST_RECEIVED, media_type="image/png")

@app.get("/last-warped")
def last_warped():
    if not os.path.exists(LAST_WARPED):
        raise HTTPException(404, "No warped image yet")
    return FileResponse(LAST_WARPED, media_type="image/png")

@app.get("/last-debug")
def last_debug():
    if not os.path.exists(LAST_DEBUG):
        raise HTTPException(404, "No debug image yet")
    return FileResponse(LAST_DEBUG, media_type="image/png")

@app.get("/download-excel")
def download_excel():
    if not os.path.exists(EXCEL_PATH):
        raise HTTPException(404, "Excel not found yet")
    return FileResponse(EXCEL_PATH, filename="results.xlsx")

# =========================
# Helpers: text/digits
# =========================
PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS  = "٠١٢٣٤٥٦٧٨٩"
TRANS = {ord(d): str(i) for i, d in enumerate(PERSIAN_DIGITS)}
TRANS.update({ord(d): str(i) for i, d in enumerate(ARABIC_DIGITS)})

DATE_RE = re.compile(r"(1[3-4]\d{2})\s*[/\-\.\s]\s*(\d{1,2})\s*[/\-\.\s]\s*(\d{1,2})")

AR_LETTERS_RE = re.compile(r"[\u0600-\u06FF]")
def looks_like_persian_name(s: str) -> bool:
    s = clean_text(s)
    if not s:
        return False
    if re.search(r"\d", normalize_digits(s)):
        return False
    # حداقل 2 حرف فارسی/عربی داشته باشد
    return len(AR_LETTERS_RE.findall(s)) >= 2




def normalize_digits(s: str) -> str:
    return (s or "").translate(TRANS)

def clean_text(s: str) -> str:
    s = (s or "").replace("\n", " ").replace("\r", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def digits_only(s: str) -> str:
    return re.sub(r"\D", "", normalize_digits(s or ""))

def extract_birth_date(text: str) -> str:
    t = normalize_digits(text)
    m = DATE_RE.search(t)
    if not m:
        return ""
    y = int(m.group(1))
    mo = int(m.group(2))
    d = int(m.group(3))

    # اعتبارسنجی منطقی
    if not (1300 <= y <= 1499):
        return ""
    if not (1 <= mo <= 12):
        return ""
    if not (1 <= d <= 31):
        return ""

    return f"{y}/{mo:02d}/{d:02d}"

def iran_national_id_is_valid(code: str) -> bool:
    if not code or not re.fullmatch(r"\d{10}", code):
        return False
    if code == code[0] * 10:
        return False
    check = int(code[-1])
    s = sum(int(code[i]) * (10 - i) for i in range(9))
    r = s % 11
    return (r < 2 and check == r) or (r >= 2 and check == (11 - r))

def fix_nid_by_05(code10: str) -> str:
    """
    اگر کد ۱۰رقمی معتبر نبود، روی رقم‌های '5' احتمال می‌دهیم '0' بوده.
    حالت‌ها را تست می‌کنیم تا کد معتبر پیدا شود.
    """
    if not code10 or not re.fullmatch(r"\d{10}", code10):
        return ""
    if iran_national_id_is_valid(code10):
        return code10

    idxs = [i for i, ch in enumerate(code10) if ch == "5"]
    if not idxs:
        return ""
    if len(idxs) > 8:
        idxs = idxs[:8]

    base = list(code10)
    for mask in range(1, 1 << len(idxs)):
        temp = base[:]
        for bit in range(len(idxs)):
            if (mask >> bit) & 1:
                temp[idxs[bit]] = "0"
        cand = "".join(temp)
        if iran_national_id_is_valid(cand):
            return cand
    return ""

def extract_nid_from_digits_stream(d: str) -> tuple[str, str]:
    """
    d: فقط رقم
    خروجی: (nid_fixed, raw10)
    """
    if len(d) < 10:
        return "", ""
    for i in range(0, len(d) - 9):
        cand = d[i:i+10]
        if iran_national_id_is_valid(cand):
            return cand, cand
        fixed = fix_nid_by_05(cand)
        if fixed:
            return fixed, cand
    return "", ""

def fix_birth_text(s: str) -> str:
    s = normalize_digits(s).replace(" ", "")
    b1 = extract_birth_date(s)
    if b1:
        return b1

    # اگر نامعتبر بود، 5 را 0 فرض کن
    b2 = extract_birth_date(s.replace("5", "0"))
    if b2:
        return b2

    return ""

def append_to_excel(row: dict):
    df_new = pd.DataFrame([row])
    if os.path.exists(EXCEL_PATH):
        df_old = pd.read_excel(EXCEL_PATH)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new
    df_all.to_excel(EXCEL_PATH, index=False)

# =========================
# Image helpers: crop/warp/preprocess
# =========================
def crop_norm(img, x1, y1, x2, y2):
    """
    Crop با مختصات نرمال‌شده (۰..۱)
    """
    h, w = img.shape[:2]
    X1, Y1 = int(x1 * w), int(y1 * h)
    X2, Y2 = int(x2 * w), int(y2 * h)

    X1 = max(0, min(w - 1, X1))
    X2 = max(0, min(w, X2))
    Y1 = max(0, min(h - 1, Y1))
    Y2 = max(0, min(h, Y2))

    if X2 <= X1 or Y2 <= Y1:
        return img
    return img[Y1:Y2, X1:X2]

def preprocess_for_ocr(img_bgr: np.ndarray) -> np.ndarray:
    """
    پیش‌پردازش ملایم برای فارسی
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

def preprocess_digits_roi(roi_bgr: np.ndarray) -> np.ndarray:
    """
    پیش‌پردازش مخصوص اعداد: threshold + invert + close
    """
    gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    if th.mean() > 127:
        th = 255 - th

    k = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, k, iterations=1)
    return cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)

def ocr_digits_easyocr(img_bgr: np.ndarray) -> str:
    img2 = cv2.resize(img_bgr, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
    txts = reader.readtext(
        img2,
        detail=0,
        paragraph=False,
        allowlist="0123456789۰۱۲۳۴۵۶۷۸۹",
        text_threshold=0.45,
        low_text=0.30,
        link_threshold=0.40,
        mag_ratio=1.0,
    )
    return clean_text(" ".join(txts))

def order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def find_card_quad(img_bgr: np.ndarray):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Canny با آستانه‌ی تطبیقی (بهتر از اعداد ثابت)
    v = np.median(gray)
    low = int(max(0, 0.66 * v))
    high = int(min(255, 1.33 * v))
    edges = cv2.Canny(gray, low, high)

    # بستن شکاف‌ها
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, k, iterations=2)

    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:25]

    area_img = img_bgr.shape[0] * img_bgr.shape[1]
    CARD_AR = WARP_W / WARP_H

    best_rect = None
    best_score = -1e9

    for c in cnts:
        area = cv2.contourArea(c)
        if area < 0.10 * area_img:
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            pts = approx.reshape(4, 2).astype("float32")
            return order_points(pts)

        # fallback: minAreaRect
        rect = cv2.minAreaRect(c)
        (cx, cy), (w, h), ang = rect
        if w < 10 or h < 10:
            continue

        ar = max(w, h) / min(w, h)
        ar_score = 1.0 - min(abs(ar - CARD_AR) / CARD_AR, 1.0)
        area_score = min(area / area_img, 1.0)
        score = 0.7 * ar_score + 0.3 * area_score

        if score > best_score:
            best_score = score
            best_rect = rect

    if best_rect is None:
        return None

    box = cv2.boxPoints(best_rect).astype("float32")
    return order_points(box)


def warp_card(img_bgr: np.ndarray):
    quad = find_card_quad(img_bgr)
    if quad is None:
        return img_bgr

    dst = np.array([
        [0, 0],
        [WARP_W - 1, 0],
        [WARP_W - 1, WARP_H - 1],       
        [0, WARP_H - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(quad, dst)
    warped = cv2.warpPerspective(img_bgr, M, (WARP_W, WARP_H))
    return warped

# =========================
# OCR boxes + Label->Value
# =========================
def ocr_boxes(img_bgr: np.ndarray):
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    results = reader.readtext(rgb, detail=1, paragraph=False)
    boxes = []
    for (bbox, text, conf) in results:
        text = clean_text(text)
        if not text:
            continue
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        x1, y1, x2, y2 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        boxes.append({
            "text": text, "conf": float(conf),
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "cx": cx, "cy": cy
        })
    return boxes

# =========================
# Fuzzy label matching
# =========================
# =========================
# OCR boxes + Label->Value  (FUZZY + LINE-AWARE + Y-PRIOR)
# =========================

FA_CHAR_MAP = str.maketrans({
    "ي": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه",
    "ؤ": "و", "إ": "ا", "أ": "ا", "آ": "ا",
    "\u200c": "",  # ZWNJ
})

LABEL_PATTERNS = {
    "nid":    ["شمارهملی", "شماره ملی", "کدملی", "کد ملی", "ملی"],
    "name":   ["نام"],
    "family": ["نامخانوادگی", "نام خانوادگی", "خانوادگی", "خانواد"],
    "birth":  ["تاریختولد", "تاریخ تولد", "تولد"],
    "father": ["نامپدر", "نام پدر", "پدر"],
}

# سختگیری برای "نام" چون کوتاه است و زیاد با بقیه قاطی می‌شود
MIN_LABEL_SCORE = {"nid": 72, "name": 92, "family": 72, "birth": 72, "father": 78}

# جای تقریبی لیبل‌ها روی کارت warp شده (نرمال‌شده 0..1)
EXPECTED_Y = {
    "nid": 0.22,
    "name": 0.33,
    "family": 0.43,
    "birth": 0.56,
    "father": 0.67,
}
Y_TOL = {
    "nid": 0.16,
    "name": 0.10,
    "family": 0.10,
    "birth": 0.11,
    "father": 0.11,
}

def ocr_boxes(img_bgr: np.ndarray):
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    results = reader.readtext(rgb, detail=1, paragraph=False)
    boxes = []
    for (bbox, text, conf) in results:
        text = clean_text(text)
        if not text:
            continue
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        x1, y1, x2, y2 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        boxes.append({
            "text": text, "conf": float(conf),
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "cx": cx, "cy": cy
        })
    return boxes

def norm_str(s: str) -> str:
    s = clean_text(s).translate(FA_CHAR_MAP)
    s = re.sub(r"[\s\-\_:،,\.\/\\\|]+", "", s)
    return s

def _fuzzy(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 100.0
    if (a in b) or (b in a):
        return 98.0
    if fuzz is None:
        return 0.0
    return float(fuzz.partial_ratio(a, b))

def label_match_score(text: str, kind: str) -> float:
    t = norm_str(text)
    if not t:
        return 0.0

    # اگر بیشترش عدد بود، لیبل نیست
    if len(re.sub(r"\D", "", normalize_digits(t))) >= max(2, len(t)//2):
        return 0.0

    best = 0.0
    for p in LABEL_PATTERNS.get(kind, []):
        best = max(best, _fuzzy(t, norm_str(p)))

    # جلوگیری از قاطی شدن "نام" با "نام پدر/نام خانوادگی"
    if kind == "name":
        for bad_kind in ("father", "family", "birth", "nid"):
            bad = 0.0
            for p in LABEL_PATTERNS[bad_kind]:
                bad = max(bad, _fuzzy(t, norm_str(p)))
            if bad >= 75:
                return 0.0
        if t == "نام":
            return 100.0

    # برای father حتماً چیزی شبیه پدر داشته باشد (نه صرفاً "نام")
    if kind == "father":
        has_pdr_like = max(_fuzzy(t, norm_str("پدر")), _fuzzy(t, norm_str("نامپدر")))
        if has_pdr_like < 70:
            return 0.0

    return best

def assign_line_ids(boxes):
    if not boxes:
        return
    hs = [max(8, b["y2"] - b["y1"]) for b in boxes]
    med_h = float(np.median(hs)) if hs else 18.0
    thr = max(16.0, 0.65 * med_h)  # آستانه‌ی تشخیص خط

    boxes_sorted = sorted(boxes, key=lambda b: b["cy"])
    line_id = 0
    current_y = None

    for b in boxes_sorted:
        if current_y is None or abs(b["cy"] - current_y) > thr:
            line_id += 1
            current_y = b["cy"]
        else:
            current_y = 0.7 * current_y + 0.3 * b["cy"]
        b["line_id"] = line_id

def pick_value_for_label(boxes, label_box):
    """
    فقط از همان line مقدار را انتخاب کن + سمت چپ لیبل
    """
    if label_box is None:
        return []

    label_line = label_box.get("line_id", None)
    label_h = max(10, label_box["y2"] - label_box["y1"])
    join_gap = 220  # حداکثر فاصله برای چسباندن تکه‌ها

    cands = []
    for b in boxes:
        if b is label_box:
            continue
        if label_line is not None and b.get("line_id", None) != label_line:
            continue

        # مقدار باید سمت چپ لیبل باشد
        if b["x2"] >= label_box["x1"] - 3:
            continue

        # یک کنترل عمودی نرم (برای وقتی line_id موجود نبود)
        if abs(b["cy"] - label_box["cy"]) > max(18, 0.9 * label_h):
            continue

        gap = label_box["x1"] - b["x2"]
        score = gap + (1.0 - b["conf"]) * 25.0
        cands.append((score, b))

    if not cands:
        return []

    cands.sort(key=lambda x: x[0])
    first = cands[0][1]

    parts = [first]
    for _, b in cands[1:]:
        if abs(b["cy"] - first["cy"]) <= max(18, 0.8 * label_h) and (first["x1"] - b["x2"]) < join_gap:
            parts.append(b)

    parts = sorted(parts, key=lambda x: x["x1"])
    return parts

def join_parts(parts):
    return clean_text(" ".join([p["text"] for p in parts]))

def extract_fields_by_labels(boxes, img_w, img_h):
    assign_line_ids(boxes)

    label_kinds = ["nid", "name", "family", "birth", "father"]
    label_boxes = {}

    for kind in label_kinds:
        best = None
        best_score = -1e9
        for b in boxes:
            ms = label_match_score(b["text"], kind)
            if ms < MIN_LABEL_SCORE.get(kind, 75):
                continue

            y_norm = b["cy"] / max(1.0, img_h)
            if abs(y_norm - EXPECTED_Y[kind]) > Y_TOL[kind]:
                continue

            # امتیاز نهایی: قدرت fuzzy + conf + ترجیح سمت راست
            score = (ms / 100.0) * 2.0 + b["conf"] + 0.35 * (b["cx"] / max(1.0, img_w))
            if score > best_score:
                best = b
                best_score = score

        label_boxes[kind] = best

    values = {}
    picked_parts = {}
    for kind, lb in label_boxes.items():
        if lb is None:
            values[kind] = ""
            picked_parts[kind] = []
            continue
        parts = pick_value_for_label(boxes, lb)
        picked_parts[kind] = parts
        values[kind] = join_parts(parts)

    return values, label_boxes, picked_parts

def _sim(a: str, b: str) -> float:
    if not a or not b or fuzz is None:
        return 0.0
    return float(fuzz.ratio(norm_str(a), norm_str(b)))

def is_suspect_father(father: str, family: str) -> bool:
    f = clean_text(father)
    if not f:
        return True
    # پدر معمولاً خیلی کوتاه‌تر از نام خانوادگی است
    if len(f) > 18 or f.count(" ") >= 3:
        return True
    # اگر خیلی شبیه نام خانوادگی شد، یعنی از خط اشتباه آمده
    if family and _sim(f, family) >= 78:
        return True
    return False



def draw_debug(img, boxes, label_boxes, picked_parts, roi_rects=None):
    dbg = img.copy()

    # OCR boxes (آبی)
    for b in boxes:
        cv2.rectangle(dbg, (b["x1"], b["y1"]), (b["x2"], b["y2"]), (255, 0, 0), 1)

    # Labels + picked values (سبز)
    for kind, lb in label_boxes.items():
        if lb is not None:
            cv2.rectangle(dbg, (lb["x1"], lb["y1"]), (lb["x2"], lb["y2"]), (0, 255, 0), 3)
            cv2.putText(dbg, kind.upper(), (lb["x1"], max(20, lb["y1"] - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        for p in picked_parts.get(kind, []):
            cv2.rectangle(dbg, (p["x1"], p["y1"]), (p["x2"], p["y2"]), (0, 255, 0), 2)

    # ROI ها (زرد)
    if roi_rects:
        for (x1, y1, x2, y2, label) in roi_rects:
            cv2.rectangle(dbg, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(dbg, label, (x1, max(20, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    return dbg

# =========================
# ROI helpers for stable reading
# =========================
def ocr_fa_roi(warped_bgr, x1, y1, x2, y2) -> str:
    roi = crop_norm(warped_bgr, x1, y1, x2, y2)
    roi = cv2.resize(roi, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    txts = reader.readtext(roi, detail=0, paragraph=True)
    return clean_text(" ".join(txts))

def extract_best_nid_from_roi(warped_bgr):
    """
    ROI عدد کد ملی (ثابت روی کارت warp شده)
    """
    roi = crop_norm(warped_bgr, 0.45, 0.16, 0.86, 0.30)
    roi_pp = preprocess_digits_roi(roi)
    raw_txt = ocr_digits_easyocr(roi_pp)
    d = digits_only(raw_txt)
    fixed, raw10 = extract_nid_from_digits_stream(d)
    return fixed, raw10

def extract_best_birth_from_roi(warped_bgr):
    """
    ROI تاریخ تولد (ثابت)
    """
    roi = crop_norm(warped_bgr, 0.45, 0.44, 0.86, 0.60)
    roi_pp = preprocess_digits_roi(roi)
    roi2 = cv2.resize(roi_pp, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    txt = reader.readtext(
        roi2,
        detail=0,
        paragraph=False,
        allowlist="0123456789۰۱۲۳۴۵۶۷۸۹/-. ",
    )
    return fix_birth_text(" ".join(txt))

# =========================
# Main API
# =========================
@app.post("/process-photo")
async def process_photo(
    request: Request,
    photo: UploadFile = File(None),
    file: UploadFile = File(None),
    image: UploadFile = File(None),
    imageFile: UploadFile = File(None),  # camera.html شما همینو میفرسته
):
    up = photo or file or image or imageFile
    if up is None:
        raise HTTPException(422, "No uploaded file found (photo/file/image/imageFile)")

    contents = await up.read()
    img = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return JSONResponse({"ok": False, "error": "Invalid image"}, status_code=400)

    cv2.imwrite(LAST_RECEIVED, img)

    warped = warp_card(img)
    warped = preprocess_for_ocr(warped)
    cv2.imwrite(LAST_WARPED, warped)

    h, w = warped.shape[:2]

    boxes = ocr_boxes(warped)
    values, label_boxes, picked_parts = extract_fields_by_labels(boxes, w, h)

    # --- Read fields from labels
    name   = values.get("name", "")
    family = values.get("family", "")
    father = values.get("father", "")
    if is_suspect_father(father, family):
     father = ""

    birth_label = fix_birth_text(values.get("birth", ""))

    # --- NID from label digits (backup)
    nid_label_digits = digits_only(values.get("nid", ""))
    nid_fixed_label, nid_raw10_label = extract_nid_from_digits_stream(nid_label_digits)

    # --- NID main from ROI
    nid_fixed_roi, nid_raw10_roi = extract_best_nid_from_roi(warped)

    national_id = nid_fixed_roi or nid_fixed_label or ""
    raw_nid_digits = nid_raw10_roi or nid_raw10_label or ""

    # --- Birth: if label bad, use ROI
    birth_date = birth_label
    if not birth_date:
        birth_date = extract_best_birth_from_roi(warped)

    # --- Fallback ROIs (اگر خالی/مشکوک)
    # این ROIها روی کارت warp شده پایدار هستند
    if (not looks_like_persian_name(name)):
    # فقط ناحیه مقدار "نام" (مثل سینا)
     name = ocr_fa_roi(warped, 0.60, 0.30, 0.78, 0.39)


    if not family or len(family) < 2:
        family = ocr_fa_roi(warped, 0.45, 0.36, 0.82, 0.52)

    if not father or len(father) < 2:
        father = ocr_fa_roi(warped, 0.45, 0.60, 0.86, 0.74)


    # --- Debug: ROI rectangles
    roi_rects = [
        (int(0.45*w), int(0.16*h), int(0.86*w), int(0.30*h), "NID_ROI"),
        (int(0.45*w), int(0.44*h), int(0.86*w), int(0.60*h), "BIRTH_ROI"),
        (int(0.45*w), int(0.28*h), int(0.78*w), int(0.40*h), "NAME_ROI"),
        (int(0.45*w), int(0.36*h), int(0.82*w), int(0.52*h), "FAMILY_ROI"),
        (int(0.45*w), int(0.54*h), int(0.78*w), int(0.70*h), "FATHER_ROI"),
    ]

    dbg = draw_debug(warped, boxes, label_boxes, picked_parts, roi_rects=roi_rects)
    cv2.imwrite(LAST_DEBUG, dbg)

    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "national_id": national_id,
        "raw_nid_digits": raw_nid_digits,
        "name": clean_text(name),
        "family": clean_text(family),
        "father_name": clean_text(father),
        "birth_date": birth_date,
        "raw_text": "\n".join([b["text"] for b in boxes]),
    }
    append_to_excel(record)

    return JSONResponse({
        "ok": True,
        "data": record,
        "excel": "/download-excel",
        "last_image": "/last-image",
        "last_warped": "/last-warped",
        "last_debug": "/last-debug",
    })

# =========================
# Run HTTPS
# =========================
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8443,
        ssl_keyfile=os.path.join(BASE_DIR, "key.pem"),
        ssl_certfile=os.path.join(BASE_DIR, "cert.pem"),
    )
