# 🛡️ VeriScan — Anti-Counterfeiting Platform

**India's Crowd-Powered Anti-Counterfeiting Intelligence System**

A full-stack Streamlit app that lets consumers scan QR codes, report fakes, and automatically escalates when multiple users report the same counterfeit product at the same location.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 📷 **QR Scan & Verify** | Upload QR image or enter ID to check against brand registry |
| 🚨 **Report Filing** | GPS + shop name + anomaly type sent to brand team |
| 🔴 **Auto-Escalation** | 5+ reports → CRITICAL alert + PDF report generated |
| 📊 **Brand Dashboard** | Charts, maps, escalation table, reports view |
| 🏛️ **Government Portal** | Links to 6 real Indian portals + pre-filled complaint text |
| 🔖 **QR Generator** | Brands register products and generate authentic QR codes |
| 📧 **Email Logs** | View all sent brand alert emails |
| 📄 **PDF Reports** | Professional escalation PDF with all evidence |

---

## ⚡ Quick Start

```bash
# 1. Install dependencies
py -m pip install -r requirements.txt

# 2. Run the app
py -m streamlit run app.py
```

App opens at: **http://localhost:8501**

---

## 🧪 Demo Flow

1. Go to **Brand Dashboard** → Click **"Add Demo Reports"** to seed 7 demo reports
2. Go to **Scan & Verify QR** → Test tab → Try different QR codes
3. Go to **File a Report** → Submit with QR ID `QR-NIKE-001` and shop `Sadar Bazaar Electronics` (5th report triggers escalation)
4. Go to **Email Logs** → See simulated brand alerts
5. Go to **Government Portal** → See pre-filled complaint form

---

## 📁 Project Structure

```
anticounterfeit/
├── app.py                    # Main dashboard
├── pages/
│   ├── 1_Scan_QR.py          # QR scan & verify
│   ├── 2_Report.py           # Report filing + escalation
│   ├── 3_Brand_Dashboard.py  # Analytics dashboard
│   ├── 4_Government_Portal.py # Govt portal links
│   ├── 5_Generate_QR.py      # QR code generator
│   └── 6_Email_Logs.py       # Email audit trail
├── database/
│   └── db.py                 # SQLite database layer
├── utils/
│   ├── qr_utils.py           # QR generation/decoding
│   ├── email_utils.py        # Email alerts (real + simulated)
│   └── pdf_utils.py          # PDF report generation
├── .streamlit/
│   └── config.toml           # Dark theme config
├── .env.example              # Email config template
└── requirements.txt
```

---

## 🏛️ Government Portals Integrated

| Portal | Purpose |
|---|---|
| National Consumer Helpline (1915) | Primary consumer grievance |
| Cybercrime Portal (1930) | IP crime cell, MHA |
| IP India | Trademark registry complaints |
| NITI Aayog | Startup/MSME IP violations |
| e-DAAKHIL | Consumer court online filing |
| CDSCO | Fake medicines/drugs |

---

## 🔴 Escalation Logic

```
Reports ≥ 5 at same QR + same shop → HIGH PRIORITY
Reports ≥ 10 at same QR + same shop → CRITICAL PRIORITY
                ↓
Auto-escalation triggers:
• Priority flag on all related reports
• PDF evidence report generated
• Brand email with ESCALATION header
• Escalation record in DB
• Download button for PDF
```

---

## ⚙️ Real Email Setup (Optional)

Copy `.env.example` to `.env` and fill in:
```
SMTP_USER=your_gmail@gmail.com
SMTP_PASS=your_16_char_app_password
BRAND_EMAIL=antifake@yourbrand.com
```

**Without `.env`** → emails are fully simulated (shown in UI + logged to DB). Perfect for demos.

---

## 🚀 Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → set `app.py` as entry point
4. Add secrets in dashboard (SMTP config)
5. Deploy!

---

*Built for India 🇮🇳 | Powered by crowd intelligence*
