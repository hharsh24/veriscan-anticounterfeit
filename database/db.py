import sqlite3, os, uuid
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "veriscan.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # ── Core product registry ──────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS qr_units (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        qr_code         TEXT UNIQUE NOT NULL,   -- plain code  VS-XXXXXXXXXXXX
        signed_payload  TEXT,                   -- full QR payload with ECDSA sig
        brand           TEXT NOT NULL,
        product         TEXT NOT NULL,
        category        TEXT,
        batch           TEXT,
        mfg_date        TEXT,
        exp_date        TEXT,
        -- ── One-scan tracking (clone detection) ──
        scan_count      INTEGER DEFAULT 0,
        first_scan_at   TEXT,
        first_scan_city TEXT,
        last_scan_at    TEXT,
        last_scan_city  TEXT,
        -- ── Crypto flag ──
        is_signed       INTEGER DEFAULT 0,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Reports ────────────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS reports (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        qr_code     TEXT NOT NULL,
        shop        TEXT,
        city        TEXT,
        reporter    TEXT,
        phone       TEXT,
        issue       TEXT,
        details     TEXT,
        escalated   INTEGER DEFAULT 0,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Escalations ────────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS escalations (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        qr_code     TEXT,
        shop        TEXT,
        city        TEXT,
        count       INTEGER,
        priority    TEXT,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Scan log (every scan recorded) ────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS scan_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        qr_code     TEXT,
        city        TEXT,
        result      TEXT,   -- 'genuine' | 'fake' | 'clone_alert' | 'invalid_sig'
        sig_valid   INTEGER,
        scanned_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()
    _seed()

# ── 28 pre-loaded Indian brands ───────────────────────────────────────────────
CATALOG = [
    ("Nike India",           "Air Max 270",              "Footwear"),
    ("Nike India",           "Revolution 6 Running",     "Footwear"),
    ("Adidas India",         "Ultraboost 22",            "Footwear"),
    ("Adidas India",         "Stan Smith Originals",     "Footwear"),
    ("Puma India",           "Suede Classic",            "Footwear"),
    ("boAt Lifestyle",       "Airdopes 141",             "Electronics"),
    ("boAt Lifestyle",       "Rockerz 450 Headphone",    "Electronics"),
    ("Samsung India",        "Galaxy Buds2 Pro",         "Electronics"),
    ("OnePlus India",        "Nord Buds 2r",             "Electronics"),
    ("Apple India",          "AirPods Pro 2nd Gen",      "Electronics"),
    ("Dabur India",          "Real Fruit Juice 1L",      "FMCG"),
    ("Dabur India",          "Honey 500g",               "FMCG"),
    ("Hindustan Unilever",   "Dove Shampoo 400ml",       "FMCG"),
    ("Hindustan Unilever",   "Surf Excel 2kg",           "FMCG"),
    ("Mamaearth",            "Vitamin C Facewash 100g",  "Cosmetics"),
    ("Mamaearth",            "Onion Hair Oil 250ml",     "Cosmetics"),
    ("Patanjali",            "Dant Kanti Toothpaste",    "FMCG"),
    ("Amul",                 "Gold Full Cream Milk 1L",  "FMCG"),
    ("Britannia",            "Good Day Biscuits 250g",   "FMCG"),
    ("Parle",                "Hide and Seek 150g",       "FMCG"),
    ("Titan Company",        "Titan Edge Slim Watch",    "Accessories"),
    ("Lakme",                "9to5 Primer Foundation",   "Cosmetics"),
    ("Forest Essentials",    "Soundarya Radiance Cream", "Cosmetics"),
    ("WOW Skin Science",     "Apple Cider Vinegar Shampoo", "Cosmetics"),
    ("Himalaya",             "Purifying Neem Face Wash", "Cosmetics"),
    ("Colgate",              "MaxFresh Toothpaste 200g", "FMCG"),
    ("Johnson and Johnson",  "Baby Powder 200g",         "Baby Care"),
    ("Fevicol",              "SH Adhesive 250g",         "Industrial"),
]

def _seed():
    """Seed demo QR units with cryptographic signatures."""
    conn = get_conn()
    c = conn.cursor()
    if c.execute("SELECT COUNT(*) FROM qr_units").fetchone()[0] > 0:
        conn.close(); return

    # Import crypto (may not be ready on first import, that's ok)
    try:
        from utils.crypto_utils import sign_qr_code, crypto_available
        use_crypto = crypto_available()
    except Exception:
        use_crypto = False
        def sign_qr_code(x): return x

    base = datetime(2024, 3, 1)
    for i, (brand, product, cat) in enumerate(CATALOG):
        for unit in range(2):
            code  = f"VS-{uuid.uuid4().hex[:12].upper()}"
            mfg   = (base + timedelta(days=i*7 + unit*2)).strftime("%Y-%m-%d")
            exp   = (base + timedelta(days=i*7 + unit*2 + 730)).strftime("%Y-%m-%d")
            batch = f"BT{2024}{i+1:03d}{chr(65+unit)}"
            signed = sign_qr_code(code) if use_crypto else code
            c.execute("""INSERT OR IGNORE INTO qr_units
                (qr_code, signed_payload, brand, product, category, batch, mfg_date, exp_date, is_signed)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (code, signed, brand, product, cat, batch, mfg, exp, 1 if use_crypto else 0))
    conn.commit(); conn.close()


# ── QR ops ────────────────────────────────────────────────────────────────────

def verify_and_scan(payload: str, city: str = "Unknown"):
    """
    Full verification pipeline:
      1. Verify cryptographic signature (if signed)
      2. Look up in database
      3. Record scan (one-scan policy tracking)
      4. Detect clones (same QR, different city/multiple scans)

    Returns dict with keys:
      status: 'genuine' | 'genuine_clone_alert' | 'fake' | 'invalid_signature' | 'unsigned_genuine'
      info:   product info dict or {}
      sig_valid: True | False | None
      scan_count: int
      clone_alert: bool
      clone_details: str
    """
    try:
        from utils.crypto_utils import verify_signed_qr
        code, sig_valid, reason = verify_signed_qr(payload.strip())
    except Exception:
        code, sig_valid, reason = payload.strip(), None, "crypto_unavailable"

    # ── Signature check ────────────────────────────────────────────────────────
    if sig_valid is False:
        # Signature present but INVALID → definitely tampered/cloned
        _log_scan(code, city, "invalid_sig", False)
        return {
            "status": "invalid_signature",
            "info": {},
            "sig_valid": False,
            "scan_count": 0,
            "clone_alert": False,
            "clone_details": "Cryptographic signature is INVALID. This QR has been tampered with or cloned.",
        }

    # ── Database lookup ────────────────────────────────────────────────────────
    conn = get_conn()
    row  = conn.execute("SELECT * FROM qr_units WHERE qr_code=?", (code,)).fetchone()

    if not row:
        conn.close()
        _log_scan(code, city, "fake", sig_valid)
        return {
            "status": "fake",
            "info": {},
            "sig_valid": sig_valid,
            "scan_count": 0,
            "clone_alert": False,
            "clone_details": "",
        }

    info = dict(row)
    now  = datetime.now().isoformat()

    # ── One-scan / clone detection ─────────────────────────────────────────────
    scan_count   = (info.get("scan_count") or 0) + 1
    clone_alert  = False
    clone_details = ""

    if info.get("first_scan_at") is None:
        # First ever scan → record it
        conn.execute("""UPDATE qr_units
            SET scan_count=1, first_scan_at=?, first_scan_city=?, last_scan_at=?, last_scan_city=?
            WHERE qr_code=?""", (now, city, now, city, code))
    else:
        first_city = info.get("first_scan_city", "")
        conn.execute("""UPDATE qr_units
            SET scan_count=?, last_scan_at=?, last_scan_city=?
            WHERE qr_code=?""", (scan_count, now, city, code))

        # Clone alert if city differs AND scan count getting high
        if city.lower() != first_city.lower() and city != "Unknown":
            clone_alert   = True
            clone_details = (
                f"This QR was first verified in {first_city} on "
                f"{info['first_scan_at'][:10]}. Now being scanned in {city}. "
                f"Total scans: {scan_count}. This may indicate a CLONED product."
            )

    conn.commit(); conn.close()

    status = "genuine_clone_alert" if clone_alert else (
        "unsigned_genuine" if sig_valid is None else "genuine"
    )
    _log_scan(code, city, status, sig_valid)

    return {
        "status": status,
        "info": info,
        "sig_valid": sig_valid,
        "scan_count": scan_count,
        "clone_alert": clone_alert,
        "clone_details": clone_details,
    }


def create_qr_unit(brand, product, category, batch, mfg, exp):
    """Create a new uniquely signed QR unit. Returns (plain_code, signed_payload)."""
    code = f"VS-{uuid.uuid4().hex[:12].upper()}"

    try:
        from utils.crypto_utils import sign_qr_code, crypto_available
        signed  = sign_qr_code(code) if crypto_available() else code
        is_signed = 1 if crypto_available() else 0
    except Exception:
        signed    = code
        is_signed = 0

    conn = get_conn()
    conn.execute("""INSERT INTO qr_units
        (qr_code, signed_payload, brand, product, category, batch, mfg_date, exp_date, is_signed)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (code, signed, brand, product, category, batch, str(mfg), str(exp), is_signed))
    conn.commit(); conn.close()
    return code, signed


def _log_scan(code, city, result, sig_valid):
    try:
        conn = get_conn()
        conn.execute("INSERT INTO scan_log (qr_code,city,result,sig_valid) VALUES (?,?,?,?)",
                     (code, city, result, 1 if sig_valid else 0))
        conn.commit(); conn.close()
    except Exception:
        pass


# ── Brands / products ─────────────────────────────────────────────────────────
def get_brands():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT brand FROM qr_units ORDER BY brand").fetchall()
    conn.close(); return [r[0] for r in rows]

def get_products(brand):
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT product, category FROM qr_units WHERE brand=?", (brand,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_sample_qr(brand=None):
    conn = get_conn()
    row = conn.execute("SELECT qr_code,signed_payload,brand,product,is_signed FROM qr_units LIMIT 1").fetchone()
    conn.close(); return dict(row) if row else None

def get_units_for_brand(brand):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM qr_units WHERE brand=? ORDER BY created_at DESC LIMIT 15", (brand,)).fetchall()
    conn.close(); return [dict(r) for r in rows]


# ── Reports ───────────────────────────────────────────────────────────────────
def file_report(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO reports(qr_code,shop,city,reporter,phone,issue,details) VALUES(?,?,?,?,?,?,?)",
              (data['qr_code'], data['shop'], data['city'],
               data['reporter'], data['phone'], data['issue'], data.get('details','')))
    rid = c.lastrowid; conn.commit(); conn.close(); return rid

def report_count(qr_code, shop):
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM reports WHERE qr_code=? AND LOWER(shop)=LOWER(?)",
                     (qr_code, shop)).fetchone()[0]
    conn.close(); return n

def escalate(qr_code, shop, city, n):
    priority = "CRITICAL" if n >= 10 else "HIGH"
    conn = get_conn()
    conn.execute("INSERT INTO escalations(qr_code,shop,city,count,priority) VALUES(?,?,?,?,?)",
                 (qr_code, shop, city, n, priority))
    conn.execute("UPDATE reports SET escalated=1 WHERE qr_code=? AND LOWER(shop)=LOWER(?)", (qr_code, shop))
    conn.commit(); conn.close(); return priority

def get_feed(limit=30):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM reports ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_escalations():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM escalations ORDER BY created_at DESC").fetchall()
    conn.close(); return [dict(r) for r in rows]

def stats():
    conn = get_conn()
    s = {
        'units':       conn.execute("SELECT COUNT(*) FROM qr_units").fetchone()[0],
        'signed':      conn.execute("SELECT COUNT(*) FROM qr_units WHERE is_signed=1").fetchone()[0],
        'reports':     conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0],
        'escalations': conn.execute("SELECT COUNT(*) FROM escalations").fetchone()[0],
        'today':       conn.execute("SELECT COUNT(*) FROM reports WHERE DATE(created_at)=DATE('now')").fetchone()[0],
        'brands':      conn.execute("SELECT COUNT(DISTINCT brand) FROM qr_units").fetchone()[0],
        'scans':       conn.execute("SELECT COUNT(*) FROM scan_log").fetchone()[0],
        'clones':      conn.execute("SELECT COUNT(*) FROM scan_log WHERE result='genuine_clone_alert'").fetchone()[0],
    }
    conn.close(); return s

init_db()
