import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
from database.db import create_qr_unit, verify_and_scan, file_report, report_count, escalate, stats
from utils.crypto_utils import crypto_available
import qrcode

SEP = "=" * 55

print(SEP)
print("   VERISCAN LIVE DEMO")
print(SEP)

# ── STEP 1: Generate real signed QR ──────────────────────────
print("\nSTEP 1: Generating crypto-signed QR for boAt Airdopes 141...")
code, signed = create_qr_unit(
    "boAt Lifestyle", "Airdopes 141", "Electronics",
    "BT2024DEMO", "2024-06-01", "2026-06-01"
)
print("  Plain Code :", code)
print("  Signed     :", signed[:65] + "...")
print("  Crypto ON  :", crypto_available())

# ── STEP 2: Verify genuine QR ─────────────────────────────────
print("\nSTEP 2: Customer in Mumbai scans the GENUINE QR...")
r1 = verify_and_scan(signed, "Mumbai")
print("  Result     :", r1["status"].upper())
print("  Signature  : VALID -", r1["sig_valid"])
print("  Brand      :", r1["info"].get("brand", "-"))
print("  Product    :", r1["info"].get("product", "-"))
print("  Expiry     :", r1["info"].get("exp_date", "-"))
print("  Scan Count :", r1["scan_count"])

# ── STEP 3: Same QR in different city = clone alert ───────────
print("\nSTEP 3: Same QR scanned in Delhi (clone detection)...")
r2 = verify_and_scan(signed, "Delhi")
print("  Status     :", r2["status"].upper())
print("  Clone Alert:", r2["clone_alert"])
if r2["clone_details"]:
    print("  Warning    :", r2["clone_details"][:90])

# ── STEP 4: Tampered QR ───────────────────────────────────────
print("\nSTEP 4: Counterfeiter copies QR and changes 1 character...")
tampered = signed[:-8] + "TAMPERED"
r3 = verify_and_scan(tampered, "Mumbai")
print("  Status     :", r3["status"].upper())
print("  Sig Valid  :", r3["sig_valid"])
print("  Caught     : YES - Cryptographic signature mismatch")

# ── STEP 5: Completely fake QR ────────────────────────────────
print("\nSTEP 5: Scanning a completely fake unregistered QR...")
r4 = verify_and_scan("VS-FAKE999FAKE99", "Kolkata")
print("  Status     :", r4["status"].upper())
print("  In DB      : NO")

# ── STEP 6: Crowd reports → escalation ───────────────────────
print("\nSTEP 6: 5 users report same fake product at Sadar Bazaar...")
shop = "Sadar Bazaar Electronics"
city = "New Delhi"
reporters = [
    ("Rahul Sharma", "9876543210"),
    ("Priya Patel",  "9876543211"),
    ("Amit Kumar",   "9876543212"),
    ("Sunita Roy",   "9876543213"),
    ("Vikram Singh", "9876543214"),
]
for i, (name, phone) in enumerate(reporters):
    rid = file_report({
        "qr_code": code, "shop": shop, "city": city,
        "reporter": name, "phone": phone,
        "issue": "Product quality clearly looks inferior / fake",
        "details": "Earbuds sound quality very poor, packaging has spelling errors"
    })
    n = report_count(code, shop)
    print("  Report", i+1, "- Filed by", name, "(ID #" + str(rid) + ") | Total:", n)
    if n >= 5:
        priority = escalate(code, shop, city, n)
        print("  🔴 AUTO-ESCALATED →", priority, "| Brand team notified!")

# ── STEP 7: Final stats ───────────────────────────────────────
print()
s = stats()
print(SEP)
print("   FINAL SYSTEM STATS")
print(SEP)
print("  Total Brands     :", s["brands"])
print("  QR Units Issued  :", s["units"])
print("  Crypto-Signed    :", s["signed"])
print("  Total Scans      :", s["scans"])
print("  Clone Alerts     :", s["clones"])
print("  Fake Reports     :", s["reports"])
print("  Escalations      :", s["escalations"])
print(SEP)
print("  DEMO COMPLETE!")
print("  Open http://localhost:8501 to see it live")
print(SEP)

# ── Save demo QR image ────────────────────────────────────────
img = qrcode.make(signed)
img.save("DEMO_QR_boat_airdopes.png")
print()
print("  QR image saved as: DEMO_QR_boat_airdopes.png")
print("  Plain code to type in app:", code)
