import streamlit as st
from utils.fssai_utils import verify_fssai_license, DEMO_LICENSES
import sys, os, io, uuid
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))

import qrcode
from PIL import Image
import cv2
from datetime import datetime

from database.db import (
    init_db, verify_and_scan, create_qr_unit,
    get_brands, get_products, get_sample_qr, get_units_for_brand,
    file_report, report_count, escalate,
    get_feed, get_escalations, stats, CATALOG
)

init_db()

try:
    from utils.crypto_utils import crypto_available
    CRYPTO_ON = crypto_available()
except Exception:
    CRYPTO_ON = False

st.set_page_config(page_title="VeriScan — Beat the Fake",
                   page_icon="shield", layout="centered",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
* { font-family:'Inter',sans-serif !important; box-sizing:border-box; }
.stApp { background:#f0f4f8; }
#MainMenu,footer,header,[data-testid="stSidebarNav"]{ visibility:hidden; }
.block-container{ padding:0 !important; max-width:680px !important; margin:0 auto !important; }

.navbar{ background:#0f172a; padding:14px 20px; display:flex;
         align-items:center; justify-content:space-between; }
.nav-logo{ color:#fff; font-size:1.15rem; font-weight:900; letter-spacing:-0.3px; }
.nav-logo em{ color:#38bdf8; font-style:normal; }
.nav-sub{ color:#475569; font-size:0.72rem; }

.hero{ background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 55%,#0369a1 100%);
       padding:38px 24px 32px; text-align:center; color:#fff; }
.hero-badge{ background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.3);
             color:#7dd3fc; font-size:0.7rem; font-weight:700; letter-spacing:0.1em;
             text-transform:uppercase; padding:4px 14px; border-radius:20px;
             display:inline-block; margin-bottom:14px; }
.hero h1{ font-size:2rem; font-weight:900; margin:0 0 8px; letter-spacing:-0.5px; }
.hero p{ font-size:0.88rem; color:#94a3b8; margin:0 0 12px; line-height:1.6; }

.stats{ display:flex; background:#fff; border-radius:16px; overflow:hidden;
        box-shadow:0 2px 12px rgba(0,0,0,0.08); margin-bottom:20px; }
.stat{ flex:1; padding:14px 6px; text-align:center; }
.stat+.stat{ border-left:1px solid #f1f5f9; }
.stat-n{ font-size:1.5rem; font-weight:900; color:#0f172a; line-height:1; }
.stat-n.red{ color:#dc2626; } .stat-n.green{ color:#16a34a; } .stat-n.blue{ color:#2563eb; }
.stat-l{ font-size:0.62rem; font-weight:700; color:#94a3b8;
          text-transform:uppercase; letter-spacing:0.05em; margin-top:3px; }

.card-genuine{ background:linear-gradient(135deg,#f0fdf4,#dcfce7);
  border:2px solid #22c55e; border-radius:18px; padding:22px; margin-top:16px; }
.card-clone{ background:linear-gradient(135deg,#fffbeb,#fef3c7);
  border:2px solid #f59e0b; border-radius:18px; padding:22px; margin-top:16px; }
.card-fake{ background:linear-gradient(135deg,#fff1f2,#fee2e2);
  border:2px solid #ef4444; border-radius:18px; padding:22px; margin-top:16px; }
.card-tampered{ background:linear-gradient(135deg,#1a0000,#2d0000);
  border:2px solid #dc2626; border-radius:18px; padding:22px; margin-top:16px; }
.card-title{ font-size:1.1rem; font-weight:800; margin-bottom:14px; }
.row{ display:flex; justify-content:space-between; align-items:center;
      padding:8px 0; border-bottom:1px solid rgba(0,0,0,0.06); font-size:0.85rem; }
.row:last-child{ border:none; }
.rk{ color:#64748b; } .rv{ font-weight:700; color:#0f172a; text-align:right; }

.sig-ok{ display:inline-flex; align-items:center; gap:6px; background:#dcfce7;
  color:#15803d; border:1px solid #bbf7d0; border-radius:20px; padding:4px 12px;
  font-size:0.75rem; font-weight:700; }
.sig-fail{ display:inline-flex; align-items:center; gap:6px; background:#fee2e2;
  color:#dc2626; border:1px solid #fecaca; border-radius:20px; padding:4px 12px;
  font-size:0.75rem; font-weight:700; }
.sig-none{ display:inline-flex; align-items:center; gap:6px; background:#f1f5f9;
  color:#64748b; border:1px solid #e2e8f0; border-radius:20px; padding:4px 12px;
  font-size:0.75rem; font-weight:700; }

.feed-card{ background:#fff; border-radius:14px; padding:14px 16px;
            margin-bottom:8px; border:1px solid #e2e8f0;
            display:flex; gap:12px; align-items:flex-start; }
.feed-dot{ width:9px; height:9px; border-radius:50%; flex-shrink:0; margin-top:5px; }
.feed-title{ font-size:0.88rem; font-weight:700; color:#0f172a; }
.feed-sub  { font-size:0.76rem; color:#64748b; margin-top:2px; }
.feed-qr   { font-family:monospace; font-size:0.72rem; color:#94a3b8; margin-top:2px; }
.esc-badge { background:#fee2e2; color:#dc2626; font-size:0.65rem; font-weight:800;
             border-radius:20px; padding:2px 8px; display:inline-block; margin-top:4px; }

.esc-card{ background:linear-gradient(135deg,#fff1f2,#fff5f5);
           border:1.5px solid #fca5a5; border-radius:14px; padding:16px; margin-bottom:10px; }
.esc-head{ font-size:0.9rem; font-weight:800; color:#dc2626; margin-bottom:6px; }

.qr-box{ background:#f8fafc; border:2px dashed #cbd5e1; border-radius:16px;
         padding:24px; text-align:center; margin-top:16px; }
.qr-code-text{ font-family:monospace; font-size:0.82rem; color:#0369a1;
               background:#e0f2fe; padding:6px 14px; border-radius:8px;
               display:inline-block; margin-top:8px; font-weight:700; letter-spacing:1px; }

.warn-box{ background:#fff7ed; border:1px solid #fed7aa; border-radius:10px;
           padding:12px 16px; color:#c2410c; font-size:0.82rem; margin:10px 0; }
.ok-box  { background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px;
           padding:14px 16px; color:#15803d; font-size:0.88rem; font-weight:600; margin:10px 0; }

.stButton>button{ border-radius:12px !important; font-weight:700 !important;
  font-size:0.88rem !important; padding:11px 22px !important; border:none !important;
  background:#0f172a !important; color:#fff !important; width:100%;
  transition:all 0.15s !important; }
.stButton>button:hover{ opacity:0.85 !important; transform:translateY(-1px) !important; }
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,#1d4ed8,#2563eb) !important; }

.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div{
  background:#fff !important; border:1.5px solid #e2e8f0 !important;
  border-radius:10px !important; color:#0f172a !important; font-size:0.88rem !important; }
label{ color:#475569 !important; font-size:0.8rem !important; font-weight:600 !important; }

.stTabs [data-baseweb="tab-list"]{
  background:#f1f5f9; border-radius:12px; padding:4px; gap:4px; border:none; }
.stTabs [data-baseweb="tab"]{
  border-radius:9px; font-size:0.82rem; font-weight:600; color:#64748b; padding:8px 14px; }
.stTabs [aria-selected="true"]{
  background:#fff !important; color:#0f172a !important; box-shadow:0 2px 8px rgba(0,0,0,0.1); }

.brand-chip{ display:inline-block; background:#f1f5f9; color:#334155;
             border-radius:20px; padding:5px 13px; font-size:0.78rem;
             font-weight:600; margin:3px; border:1px solid #e2e8f0; }

hr{ border:none; border-top:1px solid #f1f5f9; margin:16px 0; }
.sec-title{ font-size:0.72rem; font-weight:700; color:#94a3b8;
             text-transform:uppercase; letter-spacing:0.07em; margin-bottom:12px; }
.page-title{ font-size:1.05rem; font-weight:800; color:#0f172a; margin-bottom:4px; }
.page-sub  { font-size:0.82rem; color:#64748b; margin-bottom:20px; }
</style>
""", unsafe_allow_html=True)

crypto_badge = "Lock Crypto ON" if CRYPTO_ON else "Crypto OFF"
st.markdown(f"""
<div class="navbar">
  <div><div class="nav-logo">VeriScan</div></div>
  <div class="nav-sub">{crypto_badge} · India Anti-Counterfeit</div>
</div>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
defaults = {
    'page': 'home', 'gen_result': None, 'report_qr': '',
    'scan_input': '', 'scan_result': None,
    'fssai_result': None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── BOTTOM NAV ────────────────────────────────────────────────────────────────
nav_items = [("Home","home"), ("Scan QR","scan"), ("Food Verify","food"),
             ("Report","report"), ("Brand QR","brand")]
cols = st.columns(len(nav_items))
for col, (label, pg) in zip(cols, nav_items):
    with col:
        active = st.session_state.page == pg
        marker = "* " if active else ""
        if st.button(f"{marker}{label}", key=f"nav_{pg}"):
            st.session_state.page = pg
            st.session_state.gen_result = None
            st.session_state.scan_result = None
            st.session_state.fssai_result = None
            st.rerun()

page = st.session_state.page
PAD = "<div style='padding:18px 14px 100px;'>"


# ─────────────────────────────────────────────────────────────────────────────
# RENDER RESULT helper
# ─────────────────────────────────────────────────────────────────────────────
def render_result(result):
    status     = result['status']
    info       = result['info']
    sig_valid  = result['sig_valid']
    scan_count = result['scan_count']

    if sig_valid is True:
        sig_html = '<span class="sig-ok">Signature Valid - Cryptographically Genuine</span>'
    elif sig_valid is False:
        sig_html = '<span class="sig-fail">Signature INVALID - CLONED or TAMPERED</span>'
    else:
        sig_html = '<span class="sig-none">Unsigned QR - Legacy format</span>'

    if status == 'invalid_signature':
        st.markdown(f"""
        <div class="card-tampered">
          <div class="card-title" style="color:#ff4444;">CRYPTOGRAPHIC ALERT - TAMPERED QR!</div>
          {sig_html}
          <div style="color:#fca5a5;font-size:0.85rem;margin-top:14px;line-height:1.7;">
            The digital signature is <b>INVALID</b>. This QR has been <b>cloned, copied, or tampered with</b>.
            Do NOT purchase this product.
          </div>
        </div>
        """, unsafe_allow_html=True)
        return

    if status == 'fake':
        st.markdown(f"""
        <div class="card-fake">
          <div class="card-title" style="color:#dc2626;">Not Registered - Likely Fake!</div>
          {sig_html}
          <div class="row"><span class="rk">Status</span>
            <span class="rv" style="color:#dc2626;">QR not found in VeriScan registry</span></div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Report This Product", type="primary", key="report_btn_fake"):
            st.session_state.report_qr = result.get('raw_code','')
            st.session_state.page = 'report'
            st.rerun()
        return

    if status == 'genuine_clone_alert':
        st.markdown(f"""
        <div class="card-clone">
          <div class="card-title" style="color:#b45309;">CLONE ALERT - Suspicious Activity!</div>
          {sig_html}
          <div class="row"><span class="rk">Brand</span><span class="rv">{info.get('brand','--')}</span></div>
          <div class="row"><span class="rk">Product</span><span class="rv">{info.get('product','--')}</span></div>
          <div class="row"><span class="rk">Scan count</span><span class="rv" style="color:#dc2626;">Scan #{scan_count}</span></div>
          <div style="background:#fef3c7;border-radius:10px;padding:12px;margin-top:12px;
                      font-size:0.82rem;color:#92400e;line-height:1.6;">
            {result['clone_details']}
          </div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"""
    <div class="card-genuine">
      <div class="card-title" style="color:#15803d;">Genuine Product Verified!</div>
      {sig_html}
      <div class="row"><span class="rk">Brand</span><span class="rv">{info.get('brand','--')}</span></div>
      <div class="row"><span class="rk">Product</span><span class="rv">{info.get('product','--')}</span></div>
      <div class="row"><span class="rk">Category</span><span class="rv">{info.get('category','--')}</span></div>
      <div class="row"><span class="rk">Batch No.</span><span class="rv">{info.get('batch','--')}</span></div>
      <div class="row"><span class="rk">Mfg Date</span><span class="rv">{info.get('mfg_date','--')}</span></div>
      <div class="row"><span class="rk">Expiry</span><span class="rv">{info.get('exp_date','--')}</span></div>
      <div class="row"><span class="rk">Total Scans</span><span class="rv">{scan_count}</span></div>
    </div>
    """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# HOME
# ═════════════════════════════════════════════════════════════════════════════
if page == 'home':
    sample = get_sample_qr()
    crypto_line = "Cryptographically signed - Cannot be cloned" if CRYPTO_ON else "Crypto signatures inactive"

    st.markdown(f"""
    <div class="hero">
      <div class="hero-badge">India's Anti-Counterfeit Network</div>
      <h1>Real or Fake?<br>Know in Seconds.</h1>
      <p>Scan any QR code on a product. VeriScan checks it against<br>
         our brand registry with <b>cryptographic verification</b>.</p>
      <div style="font-size:0.75rem;color:#38bdf8;">{crypto_line}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='background:#fff;padding:16px;border-bottom:1px solid #f1f5f9;'>", unsafe_allow_html=True)
    c1, c2 = st.columns([5, 1])
    with c1:
        st.text_input("qr", placeholder="Type or paste QR code to verify...",
                      label_visibility="collapsed", key="home_input")
    with c2:
        if st.button("Go", key="home_go"):
            val = st.session_state.get('home_input', '').strip()
            if val:
                st.session_state['scan_input'] = val
                st.session_state['scan_result'] = None
                st.session_state.page = 'scan'
                st.rerun()

    if sample:
        st.markdown(f"""<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
        padding:10px 14px;color:#1e40af;font-size:0.8rem;margin-top:8px;">
        Demo code: <code style="font-size:0.78rem;">{sample['qr_code']}</code>
        &nbsp;—&nbsp;{sample['brand']} - {sample['product']}
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    s = stats()
    st.markdown(f"""
    <div style='padding:16px 14px 0;'>
    <div class="stats">
      <div class="stat"><div class="stat-n blue">{s['brands']}</div><div class="stat-l">Brands</div></div>
      <div class="stat"><div class="stat-n green">{s['signed']}</div><div class="stat-l">Crypto QRs</div></div>
      <div class="stat"><div class="stat-n">{s['scans']}</div><div class="stat-l">Scans</div></div>
      <div class="stat"><div class="stat-n red">{s['escalations']}</div><div class="stat-l">Escalated</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-title" style="margin-top:4px;">Registered Brands</div>', unsafe_allow_html=True)
    brands = get_brands()
    chips = "".join(f'<span class="brand-chip">{b}</span>' for b in brands)
    st.markdown(f'<div style="margin-bottom:20px;">{chips}</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# SCAN QR
# ═════════════════════════════════════════════════════════════════════════════
elif page == 'scan':
    st.markdown(PAD, unsafe_allow_html=True)
    st.markdown('<div class="page-title">Verify Product</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Upload QR image or type the code — cryptographic signature verified instantly</div>', unsafe_allow_html=True)

    city = st.text_input("Your city (helps detect clones)",
                          placeholder="e.g. Mumbai", key="scan_city")

    tab_upload, tab_type = st.tabs(["Upload QR Photo", "Type / Paste Code"])

    with tab_upload:
        uploaded = st.file_uploader("Upload QR code image",
                                     type=["png","jpg","jpeg","webp","bmp"],
                                     label_visibility="collapsed",
                                     key="qr_uploader")
        if uploaded:
            img_bytes = uploaded.read()
            col1, col2 = st.columns([1,1])
            with col1:
                st.image(img_bytes, caption="Uploaded", use_container_width=True)
            with col2:
                with st.spinner("Decoding QR..."):
                    nparr    = np.frombuffer(img_bytes, np.uint8)
                    img_cv   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    detector = cv2.QRCodeDetector()
                    decoded, _, _ = detector.detectAndDecode(img_cv)

                if decoded:
                    st.markdown(f"""<div class="ok-box">
                    QR Decoded: <code style="font-size:0.8rem;">{decoded[:60]}</code>
                    </div>""", unsafe_allow_html=True)
                    r = verify_and_scan(decoded, city.strip() or "Unknown")
                    r['raw_code'] = decoded
                    st.session_state['scan_result'] = r
                else:
                    st.markdown("""<div class="warn-box">
                    Could not read QR from image. Make sure it is clear and well-lit.
                    </div>""", unsafe_allow_html=True)

        if st.session_state.get('scan_result'):
            render_result(st.session_state['scan_result'])

    with tab_type:
        # key="scan_input" means Streamlit stores the value automatically
        st.text_input(
            "Enter QR code or signed payload",
            placeholder="VS-A1B2C3D4E5F6  or  VS:VS-A1B2C3D4E5F6:sig...",
            key="scan_input"
        )
        if st.button("Verify with Crypto Check", type="primary", key="verify_btn"):
            code = st.session_state.get('scan_input', '').strip()
            if code:
                r = verify_and_scan(code, city.strip() or "Unknown")
                r['raw_code'] = code
                st.session_state['scan_result'] = r
                st.rerun()
            else:
                st.warning("Enter a QR code first.")

        if st.session_state.get('scan_result'):
            render_result(st.session_state['scan_result'])

    st.markdown("</div>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# FOOD VERIFY - FSSAI
# ═════════════════════════════════════════════════════════════════════════════
elif page == 'food':
    st.markdown(PAD, unsafe_allow_html=True)
    st.markdown('<div class="page-title">Food Product Verifier</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Enter the 14-digit FSSAI number printed on any food product.</div>', unsafe_allow_html=True)

    demo_cols = st.columns(3)
    demo_brands = [
        ("10016011002115", "Dabur India"),
        ("10016022000564", "Amul (GCMMF)"),
        ("11217999000023", "Nestle India"),
        ("10013022000234", "HUL"),
        ("10014022008765", "Britannia"),
        ("99999999999999", "FAKE (Demo)"),
    ]
    for i, (lic, brand) in enumerate(demo_brands):
        with demo_cols[i % 3]:
            if st.button(brand, key=f"demo_lic_{i}", use_container_width=True):
                st.session_state['fssai_input'] = lic
                st.session_state['fssai_result'] = None
                st.rerun()

    st.text_input(
        "FSSAI License Number (14 digits)",
        placeholder="e.g. 10016011002115",
        max_chars=14,
        key="fssai_input"
    )

    if st.button("Verify FSSAI License", type="primary", key="fssai_check", use_container_width=True):
        lic = st.session_state.get('fssai_input', '').strip()
        if lic:
            with st.spinner("Checking FSSAI database..."):
                st.session_state['fssai_result'] = verify_fssai_license(lic)
            st.rerun()
        else:
            st.warning("Enter a license number first.")

    result = st.session_state.get('fssai_result')
    if result:
        lic_input = st.session_state.get('fssai_input', '')
        risk  = result.get('risk_level', 'warning')
        valid = result.get('valid')
        data  = result.get('data', {})
        msg   = result.get('message', '')
        source = result.get('source','')

        source_badge = (
            '<span style="background:#dcfce7;color:#15803d;font-size:0.7rem;font-weight:700;border-radius:20px;padding:2px 10px;">Verified via FSSAI API</span>'
            if source == 'api' else
            '<span style="background:#eff6ff;color:#1d4ed8;font-size:0.7rem;font-weight:700;border-radius:20px;padding:2px 10px;">Demo Database</span>'
        )

        if risk == 'safe' and valid:
            st.markdown(f"""
            <div class="card-genuine">
              <div class="card-title" style="color:#15803d;">FSSAI License VALID - Safe Food Product</div>
              {source_badge}
              <div class="row"><span class="rk">Company</span><span class="rv">{data.get('fbo_name','--')}</span></div>
              <div class="row"><span class="rk">License Type</span><span class="rv">{data.get('license_type','--')}</span></div>
              <div class="row"><span class="rk">State</span><span class="rv">{data.get('state','--')}</span></div>
              <div class="row"><span class="rk">Valid Till</span><span class="rv">{data.get('valid_till','--')}</span></div>
              <div class="row"><span class="rk">Status</span><span class="rv" style="color:#15803d;">{data.get('status','--')}</span></div>
              <div class="row"><span class="rk">Products</span><span class="rv">{data.get('products','--')}</span></div>
              <div class="row"><span class="rk">License No.</span><span class="rv" style="font-family:monospace;">{lic_input}</span></div>
            </div>
            <div class="ok-box" style="margin-top:10px;">This company is legally registered with FSSAI. Safe to consume!</div>
            """, unsafe_allow_html=True)

        elif risk == 'warning':
            st.markdown(f"""
            <div class="card-clone">
              <div class="card-title" style="color:#b45309;">License Issue - Verify Manually</div>
              {source_badge}
              <div class="row"><span class="rk">Company</span><span class="rv">{data.get('fbo_name','--')}</span></div>
              <div class="row"><span class="rk">Status</span><span class="rv" style="color:#d97706;">{data.get('status','UNKNOWN')}</span></div>
              <div style="margin-top:12px;font-size:0.82rem;color:#92400e;">{msg}</div>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
            <div class="card-fake">
              <div class="card-title" style="color:#dc2626;">INVALID / FAKE LICENSE - Do NOT consume!</div>
              {source_badge}
              <div class="row"><span class="rk">License No.</span><span class="rv" style="font-family:monospace;color:#dc2626;">{lic_input}</span></div>
              <div class="row"><span class="rk">Company</span><span class="rv">{data.get('fbo_name','Unknown')}</span></div>
              <div class="row"><span class="rk">Status</span><span class="rv" style="color:#dc2626;">{data.get('status','NOT FOUND')}</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            r1,r2,r3 = st.columns(3)
            with r1: st.link_button("1915 Helpline", "https://consumerhelpline.gov.in/", use_container_width=True)
            with r2: st.link_button("FSSAI Portal",  "https://fssai.gov.in",             use_container_width=True)
            with r3: st.link_button("Report Online", "https://foscos.fssai.gov.in",       use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# REPORT
# ═════════════════════════════════════════════════════════════════════════════
elif page == 'report':
    st.markdown(PAD, unsafe_allow_html=True)
    st.markdown('<div class="page-title">Report a Counterfeit</div>', unsafe_allow_html=True)
    st.markdown("""<div class="warn-box">
    5 reports from the same shop = automatic HIGH PRIORITY escalation to the brand + government portals.
    </div>""", unsafe_allow_html=True)

    with st.form("rf", clear_on_submit=True):
        qr = st.text_input("QR code on product *",
                            value=st.session_state.get('report_qr',''),
                            placeholder="Any code/text you see on packaging")
        c1, c2 = st.columns(2)
        with c1: shop = st.text_input("Shop Name *", placeholder="e.g. Sadar Electronics")
        with c2: city = st.text_input("City *",      placeholder="e.g. New Delhi")

        issue = st.selectbox("What's wrong? *", [
            "QR not in VeriScan - unregistered product",
            "Cryptographic signature invalid - definitely cloned",
            "Product quality clearly looks inferior / fake",
            "Price is suspiciously too low",
            "Poor packaging / spelling errors on label",
            "Multiple items share the same QR code",
            "Shopkeeper refused to let me scan",
            "Other",
        ])
        details = st.text_area("More details", placeholder="What made you suspicious?", height=70)
        c3, c4 = st.columns(2)
        with c3: reporter = st.text_input("Your Name *",  placeholder="Full name")
        with c4: phone    = st.text_input("Mobile No. *", placeholder="+91 XXXXX XXXXX")
        sub = st.form_submit_button("Submit Report", use_container_width=True, type="primary")

    if sub:
        missing = [f for f, v in [("QR",qr),("Shop",shop),("City",city),
                                    ("Name",reporter),("Phone",phone)] if not v.strip()]
        if missing:
            st.error(f"Fill in: {', '.join(missing)}")
        else:
            rid = file_report(dict(qr_code=qr.upper(), shop=shop, city=city,
                                    reporter=reporter, phone=phone,
                                    issue=issue, details=details))
            n = report_count(qr.upper(), shop)
            st.markdown(f'<div class="ok-box">Report #{rid} filed! Brand team notified.</div>',
                        unsafe_allow_html=True)
            if n >= 5:
                priority = escalate(qr.upper(), shop, city, n)
                st.markdown(f"""<div class="esc-card" style="margin-top:12px;">
                <div class="esc-head">AUTO-ESCALATED - {priority}!</div>
                <div style="font-size:0.82rem;color:#374151;">
                  <b>{n} users</b> reported at <b>"{shop}"</b>.
                  Flagged {priority} and sent to brand + National Consumer Helpline.
                </div></div>""", unsafe_allow_html=True)
                try:
                    from utils.pdf_utils import generate_escalation_pdf
                    all_r = get_feed(100)
                    rel = [r for r in all_r
                           if r['qr_code']==qr.upper() and r['shop'].lower()==shop.lower()]
                    pdf = generate_escalation_pdf(qr.upper(), shop, rel, n, city)
                    if pdf and os.path.exists(pdf):
                        with open(pdf,"rb") as f:
                            st.download_button("Download Evidence PDF", f,
                                               os.path.basename(pdf), "application/pdf",
                                               use_container_width=True)
                except Exception:
                    pass
            st.session_state.report_qr = ''

    st.markdown("</div>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# BRAND QR GENERATOR
# ═════════════════════════════════════════════════════════════════════════════
elif page == 'brand':
    st.markdown(PAD, unsafe_allow_html=True)
    st.markdown('<div class="page-title">Brand QR Generator</div>', unsafe_allow_html=True)

    brands    = get_brands()
    sel_brand = st.selectbox("Select Brand", brands, key="brand_sel")
    products  = get_products(sel_brand)
    prod_map  = {p['product']: p['category'] for p in products}
    sel_prod  = st.selectbox("Select Product", list(prod_map.keys()), key="prod_sel")

    c1, c2 = st.columns(2)
    with c1: mfg_d = st.date_input("Manufacture Date", key="mfg_d")
    with c2: exp_d = st.date_input("Expiry Date",      key="exp_d")
    batch = st.text_input("Batch Number (optional)", placeholder="e.g. BT2024001A")

    if st.button("Generate Cryptographically Signed QR", type="primary", key="gen_btn"):
        with st.spinner("Generating & signing..."):
            code, signed = create_qr_unit(
                sel_brand, sel_prod, prod_map[sel_prod],
                batch or f"BT-{uuid.uuid4().hex[:6].upper()}",
                str(mfg_d), str(exp_d)
            )
            qr_obj = qrcode.QRCode(version=None,
                                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                                    box_size=8, border=4)
            qr_obj.add_data(signed)
            qr_obj.make(fit=True)
            pil_img = qr_obj.make_image(fill_color="#0f172a", back_color="white")
            buf = io.BytesIO()
            pil_img.save(buf, "PNG")
            buf.seek(0)
            qr_bytes = buf.getvalue()
        st.session_state.gen_result = (code, signed, sel_brand, sel_prod, qr_bytes)

    if st.session_state.gen_result:
        code, signed, gb, gp, qr_bytes = st.session_state.gen_result
        is_signed = signed.startswith("VS:")
        sig_label = "ECDSA Signed - Clone-proof" if is_signed else "Unsigned"

        st.markdown(f"""
        <div class="qr-box">
          <div style="font-size:0.8rem;font-weight:700;color:#475569;">{gb} -- {gp}</div>
          <div style="margin:6px 0;font-size:0.75rem;font-weight:700;color:#15803d;">{sig_label}</div>
          <div class="qr-code-text">{code}</div>
        </div>
        """, unsafe_allow_html=True)

        img_col, dl_col = st.columns([1,1])
        with img_col:
            st.image(qr_bytes, width=190, caption="Scan to verify")
        with dl_col:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.download_button("Download QR PNG", qr_bytes,
                               f"{code}.png", "image/png", use_container_width=True)
            if st.button("Test Verify Now", key="verify_gen_btn"):
                st.session_state['scan_input'] = signed
                st.session_state['scan_result'] = None
                st.session_state.page = 'scan'
                st.session_state.gen_result = None
                st.rerun()

        st.markdown("""<div class="ok-box" style="margin-top:12px;">
        Registered in VeriScan. Print this QR on packaging. Customers who scan it will see Genuine with cryptographic proof.
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
