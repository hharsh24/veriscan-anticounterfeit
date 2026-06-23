import streamlit as st
import sys, os, io, uuid, cv2
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))

import qrcode
from PIL import Image
from datetime import datetime

from database.db import (
    init_db, verify_qr, create_qr_unit, get_brands, get_products,
    get_sample_qr, file_report, report_count, escalate,
    get_feed, get_escalations, stats, CATALOG
)

init_db()

st.set_page_config(page_title="VeriScan — Beat the Fake", page_icon="🛡️",
                   layout="centered", initial_sidebar_state="collapsed")

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
* { font-family:'Inter',sans-serif !important; box-sizing:border-box; }

.stApp { background:#f5f7fa; }
#MainMenu,footer,header,[data-testid="stSidebarNav"]{ visibility:hidden; }
.block-container{ padding:0 !important; max-width:700px !important; margin:0 auto !important; }
div[data-testid="stVerticalBlock"]>div{ padding-left:0; padding-right:0; }

/* NAV */
.navbar{
  background:#0f172a; padding:14px 20px;
  display:flex; align-items:center; justify-content:space-between;
}
.nav-logo{ color:#fff; font-size:1.1rem; font-weight:800; letter-spacing:-0.3px; }
.nav-logo em{ color:#3b82f6; font-style:normal; }
.nav-tagline{ color:#64748b; font-size:0.72rem; }

/* HERO */
.hero{
  background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 60%,#1d4ed8 100%);
  padding:40px 24px 36px; text-align:center; color:#fff;
}
.hero-badge{
  background:rgba(59,130,246,0.2); border:1px solid rgba(59,130,246,0.4);
  color:#93c5fd; font-size:0.72rem; font-weight:700; letter-spacing:0.08em;
  text-transform:uppercase; padding:4px 14px; border-radius:20px;
  display:inline-block; margin-bottom:16px;
}
.hero h1{ font-size:2rem; font-weight:900; margin:0 0 8px; letter-spacing:-0.5px; line-height:1.15; }
.hero p{ font-size:0.9rem; color:#94a3b8; margin:0 0 28px; line-height:1.6; }

/* SCAN CARD */
.scan-card{
  background:#fff; border-radius:20px; padding:24px;
  box-shadow:0 8px 40px rgba(0,0,0,0.18); margin:0 8px;
}
.scan-card-title{ font-size:0.72rem; font-weight:700; color:#94a3b8;
  text-transform:uppercase; letter-spacing:0.08em; margin-bottom:12px; }

/* BOTTOM NAV */
.bottom-nav{
  position:fixed; bottom:0; left:50%; transform:translateX(-50%);
  width:100%; max-width:700px;
  background:#fff; border-top:1px solid #e2e8f0;
  display:flex; padding:8px 0 12px; z-index:999;
}
.bnav-item{
  flex:1; text-align:center; cursor:pointer;
  font-size:0.68rem; font-weight:600; color:#94a3b8; padding:4px 0;
}
.bnav-item .icon{ font-size:1.3rem; display:block; margin-bottom:2px; }
.bnav-item.active{ color:#1d4ed8; }

/* SECTION */
.section{ padding:20px 16px 100px; }
.section-title{
  font-size:1rem; font-weight:800; color:#0f172a; margin-bottom:4px;
}
.section-sub{ font-size:0.82rem; color:#64748b; margin-bottom:20px; }

/* RESULT CARDS */
.res-ok{
  background:#f0fdf4; border:2px solid #22c55e; border-radius:16px;
  padding:20px; margin-top:16px;
}
.res-fake{
  background:#fff1f2; border:2px solid #ef4444; border-radius:16px;
  padding:20px; margin-top:16px;
}
.res-title{ font-size:1.1rem; font-weight:800; margin-bottom:14px; }
.res-row{
  display:flex; justify-content:space-between; padding:8px 0;
  border-bottom:1px solid rgba(0,0,0,0.06); font-size:0.85rem;
}
.res-row:last-child{ border:none; }
.res-key{ color:#64748b; }
.res-val{ font-weight:700; color:#0f172a; text-align:right; max-width:60%; }

/* STATS ROW */
.stats{
  display:flex; background:#fff; border-radius:16px;
  overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.06);
  margin-bottom:20px;
}
.stat{ flex:1; padding:16px 8px; text-align:center; }
.stat+.stat{ border-left:1px solid #f1f5f9; }
.stat-n{ font-size:1.6rem; font-weight:900; color:#0f172a; }
.stat-n.red{ color:#dc2626; }
.stat-l{ font-size:0.65rem; font-weight:700; color:#94a3b8;
  text-transform:uppercase; letter-spacing:0.05em; margin-top:2px; }

/* FEED CARD */
.feed-card{
  background:#fff; border-radius:14px; padding:14px 16px;
  margin-bottom:10px; border:1px solid #f1f5f9;
  display:flex; gap:12px; align-items:flex-start;
}
.feed-dot{ width:9px; height:9px; border-radius:50%; flex-shrink:0; margin-top:5px; }
.feed-title{ font-size:0.88rem; font-weight:700; color:#0f172a; }
.feed-sub{ font-size:0.76rem; color:#64748b; margin-top:3px; }
.feed-qr{ font-family:monospace; font-size:0.72rem; color:#94a3b8; margin-top:3px; }
.esc-badge{
  background:#fee2e2; color:#dc2626; font-size:0.65rem; font-weight:800;
  border-radius:20px; padding:2px 8px; display:inline-block; margin-top:4px;
}

/* ESC CARD */
.esc-card{
  background:linear-gradient(135deg,#fff1f2,#fff5f5);
  border:1.5px solid #fca5a5; border-radius:14px; padding:16px;
  margin-bottom:10px;
}
.esc-head{ font-size:0.9rem; font-weight:800; color:#dc2626; margin-bottom:6px; }
.esc-meta{ font-size:0.8rem; color:#374151; }

/* FORM CARD */
.form-card{
  background:#fff; border-radius:16px; padding:20px;
  box-shadow:0 2px 12px rgba(0,0,0,0.07); margin-bottom:16px;
}

/* HOW IT WORKS */
.how-row{ display:flex; gap:10px; margin-bottom:20px; }
.how-item{
  flex:1; background:#fff; border-radius:14px; padding:16px 12px;
  text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.05);
}
.how-icon{ font-size:1.8rem; margin-bottom:8px; }
.how-title{ font-size:0.82rem; font-weight:700; color:#0f172a; }
.how-sub{ font-size:0.72rem; color:#94a3b8; margin-top:4px; line-height:1.4; }

/* BRAND CHIPS */
.brand-chip{
  display:inline-block; background:#f1f5f9; color:#334155;
  border-radius:20px; padding:5px 13px; font-size:0.78rem;
  font-weight:600; margin:3px; border:1px solid #e2e8f0;
}

/* QR PREVIEW BOX */
.qr-box{
  background:#f8fafc; border:2px dashed #cbd5e1; border-radius:16px;
  padding:24px; text-align:center; margin-top:16px;
}
.qr-code-text{
  font-family:monospace; font-size:0.88rem; color:#1d4ed8;
  background:#eff6ff; padding:8px 16px; border-radius:10px;
  display:inline-block; margin-top:10px; font-weight:700;
  letter-spacing:1px;
}

/* BUTTONS */
.stButton>button{
  border-radius:12px !important; font-weight:700 !important;
  font-size:0.88rem !important; padding:11px 22px !important;
  border:none !important; transition:all 0.15s !important;
  background:#0f172a !important; color:#fff !important; width:100%;
}
.stButton>button:hover{ opacity:0.85 !important; transform:translateY(-1px) !important; }
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,#1d4ed8,#2563eb) !important;
}

/* INPUTS */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div{
  background:#fff !important; border:1.5px solid #e2e8f0 !important;
  border-radius:10px !important; color:#0f172a !important;
  font-size:0.88rem !important;
}
.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus{
  border-color:#3b82f6 !important;
  box-shadow:0 0 0 3px rgba(59,130,246,0.1) !important;
}
label{ color:#475569 !important; font-size:0.8rem !important; font-weight:600 !important; }

/* TABS */
.stTabs [data-baseweb="tab-list"]{
  background:#f1f5f9; border-radius:12px; padding:4px; gap:4px;
}
.stTabs [data-baseweb="tab"]{
  border-radius:9px; font-size:0.82rem; font-weight:600;
  color:#64748b; padding:8px 14px;
}
.stTabs [aria-selected="true"]{
  background:#fff !important; color:#0f172a !important;
  box-shadow:0 2px 6px rgba(0,0,0,0.1);
}

hr{ border:none; border-top:1px solid #f1f5f9; margin:16px 0; }

.info-box{
  background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px;
  padding:12px 16px; color:#1e40af; font-size:0.82rem; margin:10px 0;
}
.warn-box{
  background:#fff7ed; border:1px solid #fed7aa; border-radius:10px;
  padding:12px 16px; color:#c2410c; font-size:0.82rem; margin:10px 0;
}
.success-box{
  background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px;
  padding:14px 16px; color:#15803d; font-size:0.88rem; font-weight:600; margin:10px 0;
}
</style>
""", unsafe_allow_html=True)

# ─── NAVBAR ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="navbar">
  <div>
    <div class="nav-logo">🛡️ Veri<em>Scan</em></div>
  </div>
  <div class="nav-tagline">India's Anti-Counterfeit Network</div>
</div>
""", unsafe_allow_html=True)

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
for key, val in [('page','home'), ('scan_result',None), ('gen_result',None), ('report_qr','')]:
    if key not in st.session_state:
        st.session_state[key] = val

# ─── BOTTOM NAV ───────────────────────────────────────────────────────────────
nav_labels = [("🏠","Home","home"), ("🔍","Scan QR","scan"),
              ("🚨","Report","report"), ("📡","Live Feed","feed"),
              ("🔖","Brand QR","brand")]

cols = st.columns(len(nav_labels))
for col, (icon, label, pg) in zip(cols, nav_labels):
    with col:
        active = "▪ " if st.session_state.page == pg else ""
        if st.button(f"{icon}\n{active}{label}", key=f"nav_{pg}"):
            st.session_state.page = pg
            st.session_state.scan_result = None
            st.rerun()

page = st.session_state.page

# ═══════════════════════════════════════════════════════════════════════════════
#  HOME
# ═══════════════════════════════════════════════════════════════════════════════
if page == 'home':
    # Hero
    sample = get_sample_qr()
    st.markdown(f"""
    <div class="hero">
      <div class="hero-badge">🇮🇳 Made for India · Crowd-Powered</div>
      <h1>Is Your Product<br>Real or Fake?</h1>
      <p>Scan the QR code on any product.<br>
         VeriScan instantly tells you if it's genuine — in seconds.</p>
    </div>
    """, unsafe_allow_html=True)

    # Quick scan strip directly below hero
    st.markdown("<div style='padding:0 12px; margin-top:-1px; background:#fff; border-bottom:1px solid #f1f5f9; padding:16px;'>", unsafe_allow_html=True)
    c1, c2 = st.columns([5,1])
    with c1:
        qr_home = st.text_input("QR code", placeholder="Type or paste QR code here…", label_visibility="collapsed", key="home_input")
    with c2:
        go = st.button("Check →", key="home_go")
    if go and qr_home:
        st.session_state.page = 'scan'
        st.session_state['prefill_scan'] = qr_home.strip().upper()
        st.rerun()
    if sample:
        st.markdown(f"""<div class="info-box">
        💡 <b>Try a demo scan:</b> <code>{sample['qr_code']}</code>
        &nbsp;({sample['brand']} – {sample['product']})
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Stats
    s = stats()
    st.markdown(f"""
    <div style="padding:16px 12px 0;">
    <div class="stats">
      <div class="stat"><div class="stat-n">{s['brands']}</div><div class="stat-l">Brands</div></div>
      <div class="stat"><div class="stat-n">{s['units']}</div><div class="stat-l">QR Units</div></div>
      <div class="stat"><div class="stat-n">{s['reports']}</div><div class="stat-l">Reports</div></div>
      <div class="stat"><div class="stat-n red">{s['escalations']}</div><div class="stat-l">Escalated</div></div>
    </div>
    """, unsafe_allow_html=True)

    # How it works
    st.markdown("""
    <div class="section-title">How VeriScan Works</div>
    <div class="how-row">
      <div class="how-item">
        <div class="how-icon">📷</div>
        <div class="how-title">Scan QR</div>
        <div class="how-sub">Upload photo of QR code or type the code from packaging</div>
      </div>
      <div class="how-item">
        <div class="how-icon">✅</div>
        <div class="how-title">Verify</div>
        <div class="how-sub">Instant check against brand registry — real or fake in 1 second</div>
      </div>
      <div class="how-item">
        <div class="how-icon">🔴</div>
        <div class="how-title">Auto-Escalate</div>
        <div class="how-sub">5 reports from same shop = brand + authorities auto-notified</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Registered brands
    st.markdown('<div class="section-title" style="margin-top:8px;">Registered Brands</div>', unsafe_allow_html=True)
    brands = get_brands()
    chips = "".join(f'<span class="brand-chip">{b}</span>' for b in brands)
    st.markdown(f'<div style="margin-bottom:20px;">{chips}</div>', unsafe_allow_html=True)

    # Recent reports
    feed = get_feed(6)
    if feed:
        st.markdown('<div class="section-title">Recent Community Reports</div>', unsafe_allow_html=True)
        for r in feed:
            dot_color = "#ef4444" if r.get('escalated') else "#f97316"
            esc_html = "<span class='esc-badge'>🔴 ESCALATED</span>" if r.get('escalated') else ""
            st.markdown(f"""
            <div class="feed-card">
              <div class="feed-dot" style="background:{dot_color};"></div>
              <div style="flex:1;">
                <div class="feed-title">{r['shop']}, {r['city']}</div>
                <div class="feed-sub">{r['issue']}</div>
                <div class="feed-qr">{r['qr_code']}</div>
                {esc_html}
              </div>
              <div style="font-size:0.72rem;color:#94a3b8;white-space:nowrap;">{r['created_at'][:10]}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  SCAN QR  (Upload image OR type code)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == 'scan':
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Verify Product Authenticity</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Upload a QR code photo or type the code manually</div>', unsafe_allow_html=True)

    tab_upload, tab_type = st.tabs(["📷 Upload QR Image", "⌨️ Type Code Manually"])

    def show_result(code):
        code = code.strip().upper()
        info = verify_qr(code)
        if info:
            st.markdown(f"""
            <div class="res-ok">
              <div class="res-title" style="color:#15803d;">✅ Genuine Product Verified!</div>
              <div class="res-row"><span class="res-key">Brand</span><span class="res-val">{info['brand']}</span></div>
              <div class="res-row"><span class="res-key">Product</span><span class="res-val">{info['product']}</span></div>
              <div class="res-row"><span class="res-key">Category</span><span class="res-val">{info.get('category','—')}</span></div>
              <div class="res-row"><span class="res-key">Batch No.</span><span class="res-val">{info.get('batch','—')}</span></div>
              <div class="res-row"><span class="res-key">Mfg Date</span><span class="res-val">{info.get('mfg_date','—')}</span></div>
              <div class="res-row"><span class="res-key">Expiry</span><span class="res-val">{info.get('exp_date','—')}</span></div>
              <div class="res-row"><span class="res-key">QR Code</span><span class="res-val" style="font-family:monospace;font-size:0.78rem;">{code}</span></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="res-fake">
              <div class="res-title" style="color:#dc2626;">❌ Not Found — Possible Fake!</div>
              <div class="res-row"><span class="res-key">QR Code</span><span class="res-val" style="font-family:monospace;font-size:0.78rem;">{code}</span></div>
              <div class="res-row"><span class="res-key">Status</span><span class="res-val" style="color:#dc2626;">Not registered in VeriScan</span></div>
              <div style="margin-top:12px;font-size:0.82rem;color:#6b7280;">
                This QR is not in our brand registry. This product may be counterfeit.
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.session_state.report_qr = code
            if st.button("🚨 Report This Product", type="primary"):
                st.session_state.page = 'report'
                st.rerun()
        return info is not None

    # ── Tab 1: Upload image ────────────────────────────────────────────────────
    with tab_upload:
        st.markdown("""
        <div class="info-box">
          📷 <b>How to scan:</b> Take a clear photo of the QR code on the product packaging → upload below → VeriScan decodes and verifies it instantly.
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader("Upload QR code image", type=["png","jpg","jpeg","webp"],
                                     label_visibility="collapsed")
        if uploaded:
            img_bytes = uploaded.read()
            col1, col2 = st.columns([1, 1])
            with col1:
                st.image(img_bytes, caption="Uploaded image", use_container_width=True)
            with col2:
                with st.spinner("🔍 Decoding QR…"):
                    # Decode with OpenCV
                    nparr = np.frombuffer(img_bytes, np.uint8)
                    img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    detector = cv2.QRCodeDetector()
                    decoded, _, _ = detector.detectAndDecode(img_cv)

                if decoded:
                    st.markdown(f"""
                    <div class="success-box">
                      ✅ QR Decoded!<br>
                      <span style="font-family:monospace;font-size:0.82rem;">{decoded}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    show_result(decoded)
                else:
                    st.markdown("""
                    <div class="warn-box">
                      ⚠️ Could not decode QR from this image.<br>
                      Make sure the QR code is clear, well-lit, and not blurry.
                      Try the "Type Code Manually" tab instead.
                    </div>
                    """, unsafe_allow_html=True)

    # ── Tab 2: Manual type ─────────────────────────────────────────────────────
    with tab_type:
        prefill = st.session_state.pop('prefill_scan', '')
        manual_code = st.text_input("Enter QR code", value=prefill,
                                     placeholder="e.g. VS-A1B2C3D4E5F6",
                                     key="manual_qr_input")

        sample = get_sample_qr()
        if sample:
            st.markdown(f"""
            <div class="info-box">
              💡 <b>Demo:</b> Copy and paste this real registered QR code to test:<br>
              <code style="font-size:0.85rem;font-weight:700;">{sample['qr_code']}</code>
              &nbsp;→&nbsp; {sample['brand']} — {sample['product']}
            </div>
            """, unsafe_allow_html=True)

        if st.button("🔍 Verify Product", type="primary", key="verify_manual_btn"):
            if manual_code:
                show_result(manual_code)
            else:
                st.warning("Please enter a QR code first.")

    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  REPORT FAKE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == 'report':
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🚨 Report a Counterfeit Product</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="warn-box">
      ⚡ <b>How crowd-reporting works:</b> Every report is sent to the brand's anti-counterfeit team.
      When <b>5 or more users</b> report the same QR from the same shop, it's automatically
      escalated as HIGH PRIORITY to the brand and government portals.
    </div>
    """, unsafe_allow_html=True)

    # Prefill QR from scan page
    prefill_qr = st.session_state.get('report_qr', '')

    with st.form("report_form", clear_on_submit=True):
        qr = st.text_input("QR code on product *", value=prefill_qr,
                            placeholder="VS-XXXXXXXX  or any text/code on packaging")

        c1, c2 = st.columns(2)
        with c1: shop = st.text_input("Shop Name *", placeholder="e.g. Sadar Electronics")
        with c2: city = st.text_input("City *", placeholder="e.g. New Delhi")

        issue = st.selectbox("What's the problem? *", [
            "QR not found in VeriScan database",
            "Product quality clearly looks fake",
            "Price is suspiciously too low",
            "Poor packaging / spelling mistakes on label",
            "Multiple products share the same QR code",
            "Shopkeeper refused to allow scanning",
            "QR redirected to suspicious link",
            "Other",
        ])

        details = st.text_area("Additional details", placeholder="Describe what made you suspicious…", height=80)

        c3, c4 = st.columns(2)
        with c3: reporter = st.text_input("Your Name *", placeholder="Full name")
        with c4: phone    = st.text_input("Mobile Number *", placeholder="+91 XXXXX XXXXX")

        submitted = st.form_submit_button("Submit Report 🚨", use_container_width=True, type="primary")

    if submitted:
        missing = [f for f, v in [("QR code", qr), ("Shop", shop), ("City", city),
                                    ("Name", reporter), ("Phone", phone)] if not v.strip()]
        if missing:
            st.error(f"Please fill in: {', '.join(missing)}")
        else:
            rid  = file_report(dict(qr_code=qr.upper(), shop=shop, city=city,
                                    reporter=reporter, phone=phone,
                                    issue=issue, details=details))
            n    = report_count(qr.upper(), shop)
            is_esc = n >= 5

            st.markdown(f'<div class="success-box">✅ Report #{rid} submitted! Brand team has been notified.</div>',
                        unsafe_allow_html=True)

            if is_esc:
                priority = escalate(qr.upper(), shop, city, n)
                st.markdown(f"""
                <div class="esc-card" style="margin-top:12px;">
                  <div class="esc-head">🔴 AUTO-ESCALATION — {priority}!</div>
                  <div class="esc-meta">
                    <b>{n} independent users</b> reported the same product at <b>"{shop}"</b>.<br>
                    This is now flagged <b>{priority}</b> and sent to brand's anti-counterfeiting
                    team + government portals automatically.
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # PDF
                try:
                    from utils.pdf_utils import generate_escalation_pdf
                    all_r = get_feed(100)
                    rel = [r for r in all_r if r['qr_code'] == qr.upper() and r['shop'].lower() == shop.lower()]
                    pdf = generate_escalation_pdf(qr.upper(), shop, rel, n, city)
                    if pdf and os.path.exists(pdf):
                        with open(pdf, "rb") as f:
                            st.download_button("📄 Download Evidence PDF", f,
                                               os.path.basename(pdf), "application/pdf",
                                               use_container_width=True)
                except Exception:
                    pass

            st.markdown("---")
            st.markdown('<div style="font-size:0.8rem;color:#64748b;margin-bottom:8px;">Also report directly to government:</div>', unsafe_allow_html=True)
            gc1, gc2, gc3 = st.columns(3)
            with gc1: st.link_button("📞 1915 Helpline", "https://consumerhelpline.gov.in/", use_container_width=True)
            with gc2: st.link_button("⚖️ Cybercrime", "https://cybercrime.gov.in/", use_container_width=True)
            with gc3: st.link_button("📜 IP India", "https://ipindia.gov.in/", use_container_width=True)

            st.session_state.report_qr = ''

    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  LIVE FEED
# ═══════════════════════════════════════════════════════════════════════════════
elif page == 'feed':
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📡 Live Community Feed</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Real-time counterfeit reports from users across India</div>', unsafe_allow_html=True)

    s = stats()
    st.markdown(f"""
    <div class="stats">
      <div class="stat"><div class="stat-n">{s['reports']}</div><div class="stat-l">Total Reports</div></div>
      <div class="stat"><div class="stat-n red">{s['escalations']}</div><div class="stat-l">Escalated</div></div>
      <div class="stat"><div class="stat-n">{s['today']}</div><div class="stat-l">Today</div></div>
      <div class="stat"><div class="stat-n">{s['units']}</div><div class="stat-l">QR Protected</div></div>
    </div>
    """, unsafe_allow_html=True)

    escs = get_escalations()
    if escs:
        st.markdown('<div style="font-size:0.72rem;font-weight:700;color:#dc2626;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:8px;">🔴 Escalated Hotspots</div>', unsafe_allow_html=True)
        for e in escs:
            p = e.get('priority','HIGH')
            pcolor = "#dc2626" if p == "CRITICAL" else "#d97706"
            st.markdown(f"""
            <div class="esc-card">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div class="esc-head" style="margin:0;">{e['shop']}, {e['city']}</div>
                <span style="background:#fee2e2;color:{pcolor};font-size:0.68rem;font-weight:800;
                             border-radius:20px;padding:3px 10px;">{p}</span>
              </div>
              <div class="esc-meta" style="margin-top:6px;">
                <b>{e['count']} reports</b> &nbsp;·&nbsp;
                <code style="font-size:0.76rem;">{e['qr_code']}</code> &nbsp;·&nbsp;
                {e.get('created_at','')[:10]}
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    feed = get_feed(40)
    if feed:
        st.markdown('<div style="font-size:0.72rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:10px;">All Reports</div>', unsafe_allow_html=True)
        for r in feed:
            dot_color = "#ef4444" if r.get('escalated') else "#f97316"
            esc_html  = "<span class='esc-badge'>🔴 ESCALATED</span>" if r.get('escalated') else ""
            st.markdown(f"""
            <div class="feed-card">
              <div class="feed-dot" style="background:{dot_color};margin-top:5px;"></div>
              <div style="flex:1;">
                <div style="display:flex;justify-content:space-between;">
                  <div class="feed-title">{r['shop']}, {r['city']}</div>
                  <div style="font-size:0.72rem;color:#94a3b8;white-space:nowrap;">{r['created_at'][:10]}</div>
                </div>
                <div class="feed-sub">{r['issue']}</div>
                <div class="feed-qr">{r['qr_code']}</div>
                {esc_html}
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:48px 20px;color:#94a3b8;">
          <div style="font-size:2.5rem;margin-bottom:10px;">📭</div>
          <div style="font-size:0.9rem;font-weight:700;color:#475569;">No reports yet</div>
          <div style="font-size:0.8rem;margin-top:4px;">Submit a report to get started</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  BRAND QR  (Generate unique QR per product unit)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == 'brand':
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔖 Brand QR Generator</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
      <b>What is this?</b><br>
      Brands use this to generate a <b>unique QR sticker</b> for each physical product unit.
      Each click creates a <b>brand-new, one-of-a-kind code</b> stored in VeriScan's database.
      That sticker goes on the box/bottle. Customers scan it → VeriScan confirms it's real.
    </div>
    """, unsafe_allow_html=True)

    # Brand + Product selector
    brands = get_brands()
    sel_brand = st.selectbox("Select Brand", brands, key="brand_sel")
    products  = get_products(sel_brand)
    prod_map  = {p['product']: p['category'] for p in products}
    sel_prod  = st.selectbox("Select Product", list(prod_map.keys()), key="prod_sel")

    c1, c2 = st.columns(2)
    with c1: mfg_d = st.date_input("Manufacture Date", key="mfg_d")
    with c2: exp_d = st.date_input("Expiry Date",      key="exp_d")
    batch = st.text_input("Batch Number (optional)", placeholder="e.g. BT2024001A", key="batch_in")

    if st.button("🔖 Generate Unique QR Code", type="primary", key="gen_btn"):
        with st.spinner("Generating…"):
            new_code = create_qr_unit(
                sel_brand, sel_prod, prod_map[sel_prod],
                batch or f"BT-{uuid.uuid4().hex[:6].upper()}",
                str(mfg_d), str(exp_d)
            )
            # Build QR image
            qr_img = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H,
                                    box_size=10, border=4)
            qr_img.add_data(new_code)
            qr_img.make(fit=True)
            pil_img = qr_img.make_image(fill_color="#0f172a", back_color="white")
            buf = io.BytesIO()
            pil_img.save(buf, "PNG")
            buf.seek(0)
            qr_bytes = buf.getvalue()

        # Store in session so it persists after button click
        st.session_state.gen_result = (new_code, sel_brand, sel_prod, qr_bytes)

    # Always show result if it exists
    if st.session_state.gen_result:
        new_code, gb, gp, qr_bytes = st.session_state.gen_result
        st.markdown(f"""
        <div class="qr-box">
          <div style="font-size:0.8rem;font-weight:700;color:#475569;margin-bottom:4px;">{gb} — {gp}</div>
          <div style="font-size:0.72rem;color:#94a3b8;margin-bottom:12px;">New unique QR generated ✅</div>
          <div class="qr-code-text">{new_code}</div>
        </div>
        """, unsafe_allow_html=True)

        col_img, col_dl = st.columns([1,1])
        with col_img:
            st.image(qr_bytes, width=200, caption=new_code)
        with col_dl:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.download_button("⬇️ Download QR PNG", data=qr_bytes,
                               file_name=f"{new_code}.png", mime="image/png",
                               use_container_width=True)
            if st.button("🔍 Verify this QR now", key="verify_gen"):
                st.session_state['prefill_scan'] = new_code
                st.session_state.page = 'scan'
                st.session_state.gen_result = None
                st.rerun()

        st.markdown("""
        <div class="info-box" style="margin-top:12px;">
          ✅ This QR is now <b>registered in VeriScan</b>. Print it on your product packaging.
          Customers who scan it will see a <b>Genuine Product</b> verification.
        </div>
        """, unsafe_allow_html=True)

    # Show existing units for selected brand
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.8rem;font-weight:700;color:#475569;margin-bottom:10px;">Previously generated QR units for {sel_brand}</div>', unsafe_allow_html=True)

    from database.db import get_conn as _gc2
    _cnn2 = _gc2()
    units = _cnn2.execute("SELECT * FROM qr_units WHERE brand=? ORDER BY created_at DESC LIMIT 10", (sel_brand,)).fetchall()
    _cnn2.close()

    if units:
        for u in units:
            u = dict(u)
            uc1, uc2, uc3 = st.columns([3,2,1])
            with uc1:
                st.markdown(f'<div style="font-family:monospace;font-size:0.82rem;color:#1d4ed8;font-weight:700;">{u["qr_code"]}</div>'
                            f'<div style="font-size:0.75rem;color:#64748b;">{u["product"]}</div>', unsafe_allow_html=True)
            with uc2:
                st.markdown(f'<div style="font-size:0.73rem;color:#94a3b8;">Exp: {u.get("exp_date","—")}</div>'
                            f'<div style="font-size:0.73rem;color:#94a3b8;">Batch: {u.get("batch","—")}</div>', unsafe_allow_html=True)
            with uc3:
                qi = qrcode.make(u["qr_code"])
                qb = io.BytesIO(); qi.save(qb, "PNG"); qb.seek(0)
                st.download_button("⬇️", qb.getvalue(), f"{u['qr_code']}.png",
                                   "image/png", key=f"dl_{u['qr_code']}")
            st.markdown('<hr style="margin:8px 0;">', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#94a3b8;font-size:0.82rem;">No QR units yet for this brand.</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ── Footer spacer for bottom nav ──────────────────────────────────────────────
st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
