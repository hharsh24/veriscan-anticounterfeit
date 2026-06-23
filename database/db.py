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
    c.execute("""CREATE TABLE IF NOT EXISTS qr_units (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        qr_code     TEXT UNIQUE NOT NULL,
        brand       TEXT NOT NULL,
        product     TEXT NOT NULL,
        category    TEXT,
        batch       TEXT,
        mfg_date    TEXT,
        exp_date    TEXT,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
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
    c.execute("""CREATE TABLE IF NOT EXISTS escalations (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        qr_code     TEXT,
        shop        TEXT,
        city        TEXT,
        count       INTEGER,
        priority    TEXT,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()
    _seed()

CATALOG = [
    ("Nike India",           "Air Max 270",            "Footwear"),
    ("Nike India",           "Revolution 6 Running",   "Footwear"),
    ("Adidas India",         "Ultraboost 22",          "Footwear"),
    ("Adidas India",         "Stan Smith Originals",   "Footwear"),
    ("Puma India",           "Suede Classic",          "Footwear"),
    ("boAt Lifestyle",       "Airdopes 141",           "Electronics"),
    ("boAt Lifestyle",       "Rockerz 450 Headphone",  "Electronics"),
    ("Samsung India",        "Galaxy Buds2 Pro",       "Electronics"),
    ("OnePlus India",        "Nord Buds 2r",           "Electronics"),
    ("Apple India",          "AirPods Pro (2nd Gen)",  "Electronics"),
    ("Dabur India",          "Real Fruit Juice 1L",    "FMCG"),
    ("Dabur India",          "Honey 500g",             "FMCG"),
    ("Hindustan Unilever",   "Dove Shampoo 400ml",     "FMCG"),
    ("Hindustan Unilever",   "Surf Excel 2kg",         "FMCG"),
    ("Mamaearth",            "Vitamin C Facewash 100g","Cosmetics"),
    ("Mamaearth",            "Onion Hair Oil 250ml",   "Cosmetics"),
    ("Patanjali",            "Dant Kanti Toothpaste",  "FMCG"),
    ("Amul",                 "Gold Full Cream Milk 1L","FMCG"),
    ("Britannia",            "Good Day Biscuits 250g", "FMCG"),
    ("Parle",                "Hide & Seek 150g",       "FMCG"),
    ("Titan Company",        "Titan Edge Slim Watch",  "Accessories"),
    ("Lakme",                "9-to-5 Primer Foundation","Cosmetics"),
    ("Forest Essentials",    "Soundarya Radiance Cream","Cosmetics"),
    ("WOW Skin Science",     "Apple Cider Vinegar Shampoo","Cosmetics"),
    ("Himalaya",             "Purifying Neem Face Wash","Cosmetics"),
    ("Colgate",              "MaxFresh Toothpaste 200g","FMCG"),
    ("Johnson & Johnson",    "Baby Powder 200g",       "Baby Care"),
    ("Fevicol",              "SH Adhesive 250g",       "Industrial"),
]

def _seed():
    conn = get_conn()
    c = conn.cursor()
    if c.execute("SELECT COUNT(*) FROM qr_units").fetchone()[0] > 0:
        conn.close(); return
    base = datetime(2024, 3, 1)
    for i, (brand, product, cat) in enumerate(CATALOG):
        for unit in range(2):
            qr = f"VS-{uuid.uuid4().hex[:12].upper()}"
            mfg = (base + timedelta(days=i * 7 + unit * 2)).strftime("%Y-%m-%d")
            exp = (base + timedelta(days=i * 7 + unit * 2 + 730)).strftime("%Y-%m-%d")
            batch = f"BT{2024}{i+1:03d}{chr(65+unit)}"
            c.execute("INSERT OR IGNORE INTO qr_units (qr_code,brand,product,category,batch,mfg_date,exp_date) VALUES(?,?,?,?,?,?,?)",
                      (qr, brand, product, cat, batch, mfg, exp))
    conn.commit(); conn.close()

# ── QR ops ─────────────────────────────────────────────────────────────────────
def verify_qr(code: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM qr_units WHERE qr_code=?", (code,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_qr_unit(brand, product, category, batch, mfg, exp):
    code = f"VS-{uuid.uuid4().hex[:12].upper()}"
    conn = get_conn()
    conn.execute("INSERT INTO qr_units(qr_code,brand,product,category,batch,mfg_date,exp_date) VALUES(?,?,?,?,?,?,?)",
                 (code, brand, product, category, batch, mfg, exp))
    conn.commit(); conn.close()
    return code

def get_brands():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT brand FROM qr_units ORDER BY brand").fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_products(brand):
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT product, category FROM qr_units WHERE brand=?", (brand,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_sample_qr(brand=None):
    conn = get_conn()
    if brand:
        row = conn.execute("SELECT qr_code, brand, product FROM qr_units WHERE brand=? LIMIT 1", (brand,)).fetchone()
    else:
        row = conn.execute("SELECT qr_code, brand, product FROM qr_units LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None

# ── Reports ────────────────────────────────────────────────────────────────────
def file_report(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO reports(qr_code,shop,city,reporter,phone,issue,details) VALUES(?,?,?,?,?,?,?)",
              (data['qr_code'], data['shop'], data['city'],
               data['reporter'], data['phone'], data['issue'], data.get('details','')))
    rid = c.lastrowid; conn.commit(); conn.close()
    return rid

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
    conn.commit(); conn.close()
    return priority

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
        'units':      conn.execute("SELECT COUNT(*) FROM qr_units").fetchone()[0],
        'reports':    conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0],
        'escalations':conn.execute("SELECT COUNT(*) FROM escalations").fetchone()[0],
        'today':      conn.execute("SELECT COUNT(*) FROM reports WHERE DATE(created_at)=DATE('now')").fetchone()[0],
        'brands':     conn.execute("SELECT COUNT(DISTINCT brand) FROM qr_units").fetchone()[0],
    }
    conn.close(); return s

init_db()
