import html
import streamlit as st
import requests
import base64
import time
import math

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE = "https://ygg42zzgs1.execute-api.ap-southeast-2.amazonaws.com"

st.set_page_config(
    page_title="Jal Drishti · जल दृष्टि",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Theme toggle ──────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# ── CSS ───────────────────────────────────────────────────────────────────────
dark = st.session_state.dark_mode
bg_main   = "#0f1117" if dark else "#f8fafc"
bg_card   = "#1e2130" if dark else "#ffffff"
text_main = "#e8eaf6" if dark else "#1a1a2e"
text_sub  = "#9fa8da" if dark else "#555"
border    = "#2d3250" if dark else "#edf0f4"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap');
* {{ font-family: 'Inter', sans-serif !important; }}

/* ── Animations ── */
@keyframes gradientFlow {{
    0%   {{ background-position: 0% 50%; }}
    50%  {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(24px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeInLeft {{
    from {{ opacity: 0; transform: translateX(-16px); }}
    to   {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes pulse {{
    0%, 100% {{ box-shadow: 0 0 0 0 rgba(220,53,69,0.5); }}
    50%       {{ box-shadow: 0 0 0 14px rgba(220,53,69,0); }}
}}
@keyframes shimmer {{
    0%   {{ background-position: -200% 0; }}
    100% {{ background-position: 200% 0; }}
}}
@keyframes float {{
    0%, 100% {{ transform: translateY(0px); }}
    50%       {{ transform: translateY(-8px); }}
}}
@keyframes spin {{
    from {{ transform: rotate(0deg); }}
    to   {{ transform: rotate(360deg); }}
}}
@keyframes ripple {{
    0%   {{ transform: scale(0.8); opacity: 1; }}
    100% {{ transform: scale(2.4); opacity: 0; }}
}}
@keyframes countUp {{
    from {{ opacity: 0; transform: scale(0.6) translateY(10px); }}
    to   {{ opacity: 1; transform: scale(1) translateY(0); }}
}}

/* ── App background ── */
.stApp {{ background: {bg_main} !important; }}

/* ── Hero ── */
.hero {{
    background: linear-gradient(-45deg, #0f2027, #1a3a4a, #1a6b8a, #0d3b52, #2c5364);
    background-size: 400% 400%;
    animation: gradientFlow 10s ease infinite;
    color: white; padding: 60px 48px; border-radius: 28px;
    margin-bottom: 32px; text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.35);
    position: relative; overflow: hidden;
}}
.hero::before {{
    content: ''; position: absolute; top: -60%; left: -60%;
    width: 220%; height: 220%;
    background: radial-gradient(circle at 30% 40%, rgba(255,255,255,0.04) 0%, transparent 50%),
                radial-gradient(circle at 70% 60%, rgba(26,107,138,0.15) 0%, transparent 50%);
    animation: gradientFlow 8s ease infinite reverse;
}}
.hero-icon {{
    font-size: 4rem;
    animation: float 3s ease-in-out infinite;
    display: inline-block;
    filter: drop-shadow(0 8px 20px rgba(0,150,255,0.5));
}}
.hero h1 {{
    font-size: 3.4rem; font-weight: 900; margin: 12px 0 0;
    letter-spacing: -2.5px; animation: fadeInUp 0.6s ease;
    text-shadow: 0 2px 24px rgba(0,0,0,0.4);
    background: linear-gradient(135deg, #ffffff, #a8d8ea);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.hero .sub {{
    font-size: 1.1rem; opacity: 0.75; margin-top: 12px;
    animation: fadeInUp 0.8s ease; color: white;
    -webkit-text-fill-color: rgba(255,255,255,0.75);
}}
.hero .badges {{
    margin-top: 20px; display: flex; gap: 10px;
    justify-content: center; flex-wrap: wrap;
    animation: fadeInUp 1s ease;
}}
.hero .badge {{
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 20px; padding: 6px 18px; font-size: 0.8rem;
    backdrop-filter: blur(10px); transition: all 0.25s;
    color: white; -webkit-text-fill-color: white;
}}
.hero .badge:hover {{
    background: rgba(255,255,255,0.22);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}}

/* ── Stat cards ── */
.stat-row {{ display: flex; gap: 14px; margin: 20px 0; flex-wrap: wrap; }}
.stat-card {{
    flex: 1; min-width: 110px; border-radius: 20px;
    padding: 24px 16px; text-align: center; color: white;
    transition: transform 0.25s, box-shadow 0.25s;
    animation: countUp 0.5s ease;
    position: relative; overflow: hidden; cursor: default;
}}
.stat-card::after {{
    content: ''; position: absolute; top: 0; left: -100%;
    width: 60%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent);
    animation: shimmer 3.5s infinite;
}}
.stat-card:hover {{ transform: translateY(-6px) scale(1.03); }}
.stat-card.blue   {{ background: linear-gradient(135deg,#667eea,#764ba2); box-shadow: 0 8px 28px rgba(102,126,234,0.5); }}
.stat-card.green  {{ background: linear-gradient(135deg,#11998e,#38ef7d); box-shadow: 0 8px 28px rgba(17,153,142,0.5); }}
.stat-card.red    {{ background: linear-gradient(135deg,#eb3349,#f45c43); box-shadow: 0 8px 28px rgba(235,51,73,0.5); }}
.stat-card.orange {{ background: linear-gradient(135deg,#f7971e,#ffd200); box-shadow: 0 8px 28px rgba(247,151,30,0.5); }}
.stat-card.teal   {{ background: linear-gradient(135deg,#2193b0,#6dd5ed); box-shadow: 0 8px 28px rgba(33,147,176,0.5); }}
.stat-card.pink   {{ background: linear-gradient(135deg,#f953c6,#b91d73); box-shadow: 0 8px 28px rgba(249,83,198,0.5); }}
.stat-card.indigo {{ background: linear-gradient(135deg,#4776e6,#8e54e9); box-shadow: 0 8px 28px rgba(71,118,230,0.5); }}
.stat-card .val   {{ font-size: 2.6rem; font-weight: 900; line-height: 1; }}
.stat-card .lbl   {{ font-size: 0.7rem; opacity: 0.9; margin-top: 8px; text-transform: uppercase; letter-spacing: 1.2px; }}

/* ── Verdict ── */
.verdict-safe {{
    background: linear-gradient(135deg,#d4edda,#a8d5b5);
    border-left: 7px solid #28a745; padding: 28px; border-radius: 20px;
    font-size: 1.7rem; font-weight: 900;
    box-shadow: 0 8px 28px rgba(40,167,69,0.35);
    animation: fadeInUp 0.5s ease;
}}
.verdict-unsafe {{
    background: linear-gradient(135deg,#f8d7da,#f1a8b0);
    border-left: 7px solid #dc3545; padding: 28px; border-radius: 20px;
    font-size: 1.7rem; font-weight: 900;
    animation: pulse 2s infinite, fadeInUp 0.5s ease;
}}
.verdict-caution {{
    background: linear-gradient(135deg,#fff3cd,#ffe08a);
    border-left: 7px solid #ffc107; padding: 28px; border-radius: 20px;
    font-size: 1.7rem; font-weight: 900;
    box-shadow: 0 8px 28px rgba(255,193,7,0.35);
    animation: fadeInUp 0.5s ease;
}}

/* ── Glass card ── */
.glass-card {{
    background: {bg_card};
    border: 1px solid {border};
    border-radius: 20px; padding: 28px;
    box-shadow: 0 4px 24px rgba(0,0,0,{"0.2" if dark else "0.07"});
    margin-bottom: 16px;
    animation: fadeInUp 0.4s ease;
    transition: all 0.3s ease;
    color: {text_main};
}}
.glass-card:hover {{
    box-shadow: 0 14px 44px rgba(0,0,0,{"0.3" if dark else "0.13"});
    transform: translateY(-4px);
    border-color: {"#4776e6" if dark else "#c5e0f7"};
}}

/* ── Kiosk card ── */
.kiosk-card {{
    background: {bg_card}; border: 1px solid {border};
    border-radius: 20px; padding: 22px; margin-bottom: 14px;
    box-shadow: 0 2px 14px rgba(0,0,0,{"0.2" if dark else "0.06"});
    animation: fadeInLeft 0.35s ease;
    transition: all 0.28s ease;
    position: relative; overflow: hidden;
}}
.kiosk-card::before {{
    content: ''; position: absolute; left: 0; top: 0;
    width: 4px; height: 100%;
    background: linear-gradient(180deg,#1a73e8,#34a853);
    border-radius: 4px 0 0 4px;
}}
.kiosk-card:hover {{
    box-shadow: 0 12px 36px rgba(0,0,0,{"0.3" if dark else "0.13"});
    transform: translateY(-4px);
    border-color: #1a73e8;
}}

/* ── Tags ── */
.tag {{ display:inline-block; border-radius:8px; padding:3px 11px; font-size:0.78rem; font-weight:700; margin:2px; }}
.tag-green  {{ background:#d4edda; color:#155724; }}
.tag-red    {{ background:#f8d7da; color:#721c24; }}
.tag-blue   {{ background:#cce5ff; color:#004085; }}
.tag-yellow {{ background:#fff3cd; color:#856404; }}
.tag-purple {{ background:#e2d9f3; color:#4a235a; }}
.tag-teal   {{ background:#d1ecf1; color:#0c5460; }}

/* ── Chips ── */
.chip       {{ display:inline-block; background:#e8f4fd; color:#1a73e8; border-radius:20px; padding:5px 14px; margin:3px; font-size:0.8rem; font-weight:600; border:1px solid #c5e0f7; transition:all 0.2s; cursor:default; }}
.chip:hover {{ background:#1a73e8; color:white; transform:scale(1.05); }}
.chip-red   {{ background:#fdecea; color:#c62828; border-color:#f5c6cb; }}
.chip-red:hover {{ background:#c62828; color:white; }}
.chip-amber {{ background:#fff8e1; color:#e65100; border-color:#ffe082; }}
.chip-amber:hover {{ background:#e65100; color:white; }}
.chip-green {{ background:#e8f5e9; color:#2e7d32; border-color:#c8e6c9; }}
.chip-green:hover {{ background:#2e7d32; color:white; }}

/* ── Steps ── */
.step {{
    display:flex; align-items:flex-start; gap:16px;
    padding:14px 0; border-bottom:1px solid {border};
    animation: fadeInLeft 0.3s ease;
}}
.step-num {{
    background: linear-gradient(135deg,#667eea,#764ba2); color:white;
    border-radius:50%; width:36px; height:36px; min-width:36px;
    display:flex; align-items:center; justify-content:center;
    font-weight:800; font-size:0.85rem;
    box-shadow: 0 4px 12px rgba(102,126,234,0.5);
}}
.step-text {{ font-size:0.93rem; color:{text_sub}; line-height:1.5; padding-top:6px; }}

/* ── Upload zone ── */
.upload-zone {{
    background: {"linear-gradient(135deg,#1a2035,#1e2a40)" if dark else "linear-gradient(135deg,#f0f7ff,#e4f0ff)"};
    border: 2.5px dashed {"#4776e6" if dark else "#90caf9"};
    border-radius: 20px; padding: 52px 24px; text-align:center;
    color: {text_sub}; transition: all 0.25s;
}}
.upload-zone:hover {{
    border-color: #1a73e8;
    background: {"linear-gradient(135deg,#1e2a40,#22304a)" if dark else "linear-gradient(135deg,#e4f0ff,#d8eaff)"};
}}

/* The global font rule renders this icon ligature as text in Streamlit's uploader. */
div[data-testid="stFileUploader"] [data-testid="stIconMaterial"] {{
    display: none !important;
}}

/* ── Advisory ── */
.advisory-low      {{ background:linear-gradient(135deg,#d4edda,#c3e6cb); border-left:5px solid #28a745; padding:14px 18px; border-radius:12px; }}
.advisory-moderate {{ background:linear-gradient(135deg,#fff3cd,#ffeeba); border-left:5px solid #ffc107; padding:14px 18px; border-radius:12px; }}
.advisory-high     {{ background:linear-gradient(135deg,#ffe5d0,#ffd0b0); border-left:5px solid #fd7e14; padding:14px 18px; border-radius:12px; }}
.advisory-extreme  {{ background:linear-gradient(135deg,#f8d7da,#f5c6cb); border-left:5px solid #dc3545; padding:14px 18px; border-radius:12px; }}

/* ── Endpoint pill ── */
.endpoint {{
    background: #1e1e2e; color: #cdd6f4; border-radius: 12px;
    padding: 14px 20px; font-family: monospace; font-size: 0.85rem;
    margin-bottom: 10px; border: 1px solid #313244;
    transition: all 0.2s; position: relative;
}}
.endpoint:hover {{ border-color: #89dceb; background: #252535; }}
.method-get  {{ color: #89dceb; font-weight: 800; }}
.method-post {{ color: #cba6f7; font-weight: 800; }}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg,#0a1628 0%,#0f2027 40%,#1a3a4a 100%) !important;
}}
section[data-testid="stSidebar"] * {{ color: white !important; }}
section[data-testid="stSidebar"] .stRadio label {{
    padding: 10px 14px !important; border-radius: 10px !important;
    transition: background 0.2s !important;
}}
section[data-testid="stSidebar"] .stRadio label:hover {{
    background: rgba(255,255,255,0.1) !important;
}}

/* ── Progress ── */
.stProgress > div > div {{
    background: linear-gradient(90deg,#1a73e8,#34a853,#1a73e8) !important;
    background-size: 200% 100% !important;
    animation: shimmer 2s infinite !important;
    border-radius: 10px;
}}

/* ── Scrollable ── */
.scroll-list {{ max-height: 520px; overflow-y: auto; padding-right: 6px; }}
.scroll-list::-webkit-scrollbar {{ width: 5px; }}
.scroll-list::-webkit-scrollbar-track {{ background: {"#1a2035" if dark else "#f5f5f5"}; border-radius:10px; }}
.scroll-list::-webkit-scrollbar-thumb {{ background: {"#4776e6" if dark else "#ddd"}; border-radius:10px; }}
.scroll-list::-webkit-scrollbar-thumb:hover {{ background: {"#667eea" if dark else "#bbb"}; }}

/* ── Metric ── */
[data-testid="stMetric"] {{
    background: {bg_card}; border-radius: 14px; padding: 16px !important;
    box-shadow: 0 2px 10px rgba(0,0,0,{"0.2" if dark else "0.06"});
    border: 1px solid {border};
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: {bg_card}; border-radius: 12px; padding: 4px;
    border: 1px solid {border};
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px; font-weight: 600;
    color: {text_sub} !important;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg,#1a73e8,#34a853) !important;
    color: white !important;
}}

/* ── Notification dot ── */
.notif-dot {{
    display: inline-block; width: 8px; height: 8px;
    background: #ef4444; border-radius: 50%; margin-left: 6px;
    animation: pulse 1.5s infinite;
}}

/* ── Ripple button ── */
.ripple-btn {{
    position: relative; overflow: hidden;
    background: linear-gradient(135deg,#1a73e8,#34a853);
    color: white; border: none; border-radius: 12px;
    padding: 12px 24px; font-weight: 700; font-size: 1rem;
    cursor: pointer; transition: all 0.2s;
    box-shadow: 0 4px 16px rgba(26,115,232,0.4);
}}
.ripple-btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(26,115,232,0.5);
}}

/* ── Ticker ── */
.ticker {{
    background: {"#1e2130" if dark else "#1e1e2e"};
    color: #a6e3a1; border-radius: 12px; padding: 10px 20px;
    font-family: monospace; font-size: 0.82rem;
    margin-bottom: 24px; border: 1px solid {"#2d3250" if dark else "#313244"};
    display: flex; gap: 32px; overflow: hidden; align-items: center;
}}
.ticker-dot {{ color: #89dceb; }}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [
    ("flood_result", None), ("kiosk_result", None),
    ("report_count", 0),    ("api_calls", 0),
    ("api_test_result", None), ("last_verdict", None),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:36px 0 20px;'>
        <div style='font-size:4.5rem; animation: float 3s ease-in-out infinite;
                    filter:drop-shadow(0 8px 20px rgba(0,150,255,0.6));
                    display:inline-block;'>💧</div>
        <div style='font-size:1.8rem; font-weight:900; letter-spacing:-1.5px; margin-top:12px;'>
            Jal Drishti
        </div>
        <div style='font-size:0.75rem; opacity:0.5; margin-top:5px; letter-spacing:2px;'>
            जल दृष्टि · WATER VISION
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(255,255,255,0.1); margin:0 0 16px;'>",
                unsafe_allow_html=True)

    page = st.radio("", [
        "🌊  Flood Safety",
        "🚰  Water Kiosks",
        "🌧️  Report Issue",
        "📊  Dashboard",
        "ℹ️  About & API",
    ], label_visibility="collapsed")

    st.markdown("<hr style='border-color:rgba(255,255,255,0.1); margin:16px 0;'>",
                unsafe_allow_html=True)

    # Dark mode toggle
    dark_toggle = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()

    st.markdown("<hr style='border-color:rgba(255,255,255,0.1); margin:14px 0;'>",
                unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size:0.78rem; line-height:2.4; padding:0 4px;'>
        <div>🟢 &nbsp;GET /api/summer/coolers</div>
        <div>🟢 &nbsp;POST /api/monsoon/report</div>
        <div>🟡 &nbsp;POST /api/flood/analyze</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(255,255,255,0.1); margin:14px 0;'>",
                unsafe_allow_html=True)

    st.markdown(f"""
    <div style='font-size:0.7rem; opacity:0.45; text-align:center; line-height:2.4;'>
        API calls: <b style='color:white;opacity:1;'>{st.session_state.api_calls}</b> &nbsp;|&nbsp;
        Reports: <b style='color:white;opacity:1;'>{st.session_state.report_count}</b><br><br>
        Amazon Rekognition · AWS Lambda<br>
        API Gateway · Amazon S3<br>
        Elastic Beanstalk · ap-southeast-2
    </div>
    """, unsafe_allow_html=True)

# ── Ticker ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class='ticker'>
    <span class='ticker-dot'>●</span>
    <span>💧 Jal Drishti</span>
    <span class='ticker-dot'>●</span>
    <span>🌊 Flood Safety AI · Amazon Rekognition</span>
    <span class='ticker-dot'>●</span>
    <span>🚰 Water Kiosk Finder · AWS Lambda</span>
    <span class='ticker-dot'>●</span>
    <span>🌧️ Monsoon Reporter · API Gateway</span>
    <span class='ticker-dot'>●</span>
    <span>📍 ap-southeast-2 · Sydney</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — FLOOD SAFETY
# ══════════════════════════════════════════════════════════════════════════════
if "Flood" in page:
    st.markdown("""
    <div class='hero'>
        <div class='hero-icon'>🌊</div>
        <h1>Flood Road Safety</h1>
        <div class='sub'>Upload a photo · Amazon Rekognition analyzes it · Instant verdict</div>
        <div class='badges'>
            <span class='badge'>⚡ Amazon Rekognition</span>
            <span class='badge'>☁️ AWS Lambda</span>
            <span class='badge'>🪣 Amazon S3</span>
            <span class='badge'>🔒 Secure upload</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_analyze, tab_howto, tab_history = st.tabs([
        "📸 Analyze Photo", "📖 How It Works", "🕐 Last Result"
    ])

    with tab_analyze:
        left, right = st.columns([1, 1], gap="large")

        with left:
            uploaded = st.file_uploader(
                "Upload flood photo",
                type=["jpg","jpeg","png","webp"],
                label_visibility="collapsed"
            )
            if uploaded:
                st.image(uploaded, use_container_width=True,
                         caption=f"📁 {uploaded.name} · {uploaded.size//1024} KB")
                st.markdown("---")

                sensitivity = st.select_slider(
                    "Detection Sensitivity",
                    options=["Low","Medium","High"], value="Medium",
                    help="High = flags even minor water presence"
                )
                go = st.button(
                    "🔍 Analyze with Amazon Rekognition",
                    type="primary", use_container_width=True
                )
            else:
                st.caption("Upload a clear road photo (JPG, PNG, or WEBP).")
                go = False

        with right:
            if uploaded and go:
                with st.spinner("Analyzing image for flood risk..."):
                    try:
                        uploaded.seek(0)
                        image_bytes = uploaded.read()
                        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                        response = requests.post(
                            f"{API_BASE}/api/flood/analyze",
                            json={
                                "image_base64": image_b64,
                                "sensitivity": sensitivity,
                                "min_confidence": 70,
                            },
                            timeout=30,
                        )
                        result = response.json()

                        if response.status_code == 200:
                            st.session_state.flood_result = result
                            st.session_state.last_verdict = result
                            st.session_state.api_calls += 1
                        else:
                            st.error(f"API Error: {result.get('error', 'Unknown error')}")
                            st.session_state.flood_result = None
                    except requests.exceptions.Timeout:
                        st.error("Request timed out. Please try again.")
                        st.session_state.flood_result = None
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        st.session_state.flood_result = None

            result = st.session_state.flood_result
            if result:
                verdict = result.get("verdict", "UNKNOWN")
                confidence = result.get("confidence", 0)

                if verdict == "SAFE":
                    st.markdown("""
                        <div style='background:#1a472a; color:#ffffff; padding:20px;
                                    border-radius:12px; text-align:center; font-size:1.4rem; font-weight:700;'>
                            ✅ SAFE — No flood indicators detected.
                        </div>
                    """, unsafe_allow_html=True)
                elif verdict == "CAUTION":
                    if confidence >= 85:
                        level = "HIGH CAUTION"
                        color = "#ff6b00"
                        guidelines = [
                            "🚫 Avoid driving through standing water — even 15cm can stall a car",
                            "📍 Find an alternate route immediately",
                            "📞 Call emergency services if already in water: 112",
                            "🚗 If car stalls, exit immediately and move to high ground",
                        ]
                    elif confidence >= 60:
                        level = "MODERATE CAUTION"
                        color = "#e6a817"
                        guidelines = [
                            "🐢 Slow down — road surface may be slippery or submerged",
                            "👁️ Watch for water depth markers before crossing",
                            "📻 Monitor local flood alerts (indiarealtime.com)",
                            "🔄 Be ready to turn back if water level rises",
                        ]
                    else:
                        level = "LOW CAUTION"
                        color = "#c8b400"
                        guidelines = [
                            "👀 Stay alert — minor water presence detected",
                            "🌧️ Conditions may worsen if rain continues",
                            "📱 Check live traffic updates before proceeding",
                        ]

                    message = html.escape(str(result.get("message", "")))
                    st.markdown("""
                        <div style='background:linear-gradient(135deg,#3d2b00,#5c3d00);
                                    border-left:5px solid {color}; color:#000000;
                                    padding:20px; border-radius:12px; margin-bottom:16px;'>
                            <div style='font-size:1.4rem; font-weight:800; color:#000000;'>
                                ⚠️ {level}
                            </div>
                            <div style='font-size:0.95rem; opacity:0.85; margin-top:4px;'>
                                {message} &nbsp;·&nbsp; Confidence: {confidence}%
                            </div>
                        </div>
                    """.format(
                        color=color,
                        level=level,
                        message=message,
                        confidence=html.escape(str(confidence)),
                    ), unsafe_allow_html=True)
                    st.markdown(
                        "<div style='color:#000000; font-weight:700; font-size:1rem; "
                        "margin-bottom:8px;'>📋 Safety Guidelines</div>",
                        unsafe_allow_html=True,
                    )
                    for guideline in guidelines:
                        st.markdown(
                            "<div style='color:#000000; font-size:0.92rem; padding:6px 0; "
                            "border-bottom:1px solid rgba(255,255,255,0.08);'>"
                            f"{guideline}</div>",
                            unsafe_allow_html=True,
                        )
                elif verdict == "UNSAFE":
                    st.markdown("""
                        <div style='background:#7b1c1c; color:#ffffff; padding:20px;
                                    border-radius:12px; text-align:center; font-size:1.4rem; font-weight:700;'>
                            🚨 UNSAFE — Flood conditions detected. Do NOT enter.
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"Unexpected flood verdict: {verdict}")

                st.markdown(f"""
                    <div style='color:#ffffff; font-size:1.1rem; margin-top:12px; font-weight:600;'>
                        Confidence: {html.escape(str(confidence))}%
                    </div>
                """, unsafe_allow_html=True)

                with st.expander("🏷️ All labels detected"):
                    for label in result.get("labels_detected", []):
                        name = html.escape(str(label["name"]))
                        label_confidence = html.escape(str(label["confidence"]))
                        st.markdown(
                            f"<span style='color:#ffffff; font-weight:500;'>"
                            f"• {name} — {label_confidence}%</span>",
                            unsafe_allow_html=True,
                        )

            elif not uploaded:
                st.markdown(f"""
                <div style='background:{bg_card}; border-radius:20px; padding:72px 20px;
                            text-align:center; border:1px solid {border};'>
                    <div style='font-size:5rem; animation: float 3s ease-in-out infinite; display:inline-block;'>🤖</div>
                    <div style='font-size:1.05rem; margin-top:18px; font-weight:700; color:{text_sub};'>
                        Upload a photo to see the AI analysis
                    </div>
                    <div style='font-size:0.85rem; margin-top:8px; color:{text_sub}; opacity:0.7;'>
                        Amazon Rekognition detects flood, water & danger labels
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with tab_howto:
        st.markdown("### How Flood Detection Works")
        cols = st.columns(3)
        for i, (icon, title, desc) in enumerate([
            ("📷","Upload Photo",   "Take a clear photo of the road ahead and upload it"),
            ("☁️","Amazon S3",      "Image is securely stored in S3 in ap-southeast-2"),
            ("🔍","Rekognition",    "DetectLabels API scans for flood & water labels"),
            ("🧠","Lambda Scoring", "Lambda scores labels and determines risk level"),
            ("🚦","Verdict",        "SAFE / CAUTION / UNSAFE with confidence score"),
            ("📊","Confidence",     "Higher confidence = more flood labels detected"),
        ]):
            with cols[i % 3]:
                st.markdown(f"""
                <div class='glass-card' style='text-align:center; padding:32px 16px;'>
                    <div style='font-size:2.8rem; animation: float 3s ease-in-out {i*0.5}s infinite; display:inline-block;'>{icon}</div>
                    <div style='font-weight:800; margin-top:12px; font-size:1rem; color:{text_main};'>{title}</div>
                    <div style='font-size:0.85rem; color:{text_sub}; margin-top:8px; line-height:1.6;'>{desc}</div>
                </div>
                """, unsafe_allow_html=True)

    with tab_history:
        if st.session_state.last_verdict:
            r = st.session_state.last_verdict
            st.markdown("### Last Analysis Result")
            verdict = r.get("verdict","UNKNOWN")
            vmap = {
                "UNSAFE":  ("verdict-unsafe",  "🔴 UNSAFE"),
                "CAUTION": ("verdict-caution", "🟡 CAUTION"),
                "SAFE":    ("verdict-safe",    "🟢 SAFE"),
            }
            css, text = vmap.get(verdict, ("verdict-caution", verdict))
            st.markdown(f'<div class="{css}">{text} — {r.get("message","")}</div>',
                        unsafe_allow_html=True)
            st.metric("Confidence", f"{r.get('confidence',0):.1f}%")
            st.json(r)
        else:
            st.info("No analysis run yet this session. Upload a photo on the Analyze tab.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — WATER KIOSKS
# ══════════════════════════════════════════════════════════════════════════════
elif "Kiosk" in page:
    st.markdown("""
    <div class='hero'>
        <div class='hero-icon'>🚰</div>
        <h1>Find Water Kiosks</h1>
        <div class='sub'>Locate clean drinking water near you · Real-time via AWS Lambda</div>
        <div class='badges'>
            <span class='badge'>📍 GPS-powered</span>
            <span class='badge'>🔍 Smart filters</span>
            <span class='badge'>🗺️ Live map</span>
            <span class='badge'>⏱️ Walking time</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("#### 📍 Location")
        preset = st.selectbox("Quick presets", [
            "Custom coordinates",
            "Connaught Place, Delhi",
            "India Gate, Delhi",
            "Chandni Chowk, Delhi",
            "Lajpat Nagar, Delhi",
            "Karol Bagh, Delhi",
            "Saket, Delhi",
            "Dwarka, Delhi",
        ])
        coords = {
            "Connaught Place, Delhi": (28.6315, 77.2167),
            "India Gate, Delhi":      (28.6129, 77.2295),
            "Chandni Chowk, Delhi":   (28.6506, 77.2334),
            "Lajpat Nagar, Delhi":    (28.5677, 77.2433),
            "Karol Bagh, Delhi":      (28.6519, 77.1909),
            "Saket, Delhi":           (28.5245, 77.2066),
            "Dwarka, Delhi":          (28.5921, 77.0460),
        }
        dlat, dlon = coords.get(preset, (28.6315, 77.2167))
        c1, c2 = st.columns(2)
        with c1: lat = st.number_input("Latitude",  value=dlat, format="%.4f")
        with c2: lon = st.number_input("Longitude", value=dlon, format="%.4f")

        radius = st.slider("Search Radius", 200, 5000, 800, 100, format="%d m")

        st.markdown("#### 🔧 Filters")
        fc1, fc2 = st.columns(2)
        with fc1:
            only_shade = st.toggle("🌿 Shade only",       value=False)
            only_open  = st.toggle("🟢 Open only",        value=True)
        with fc2:
            only_ro    = st.toggle("💧 RO purified only", value=False)
            only_conf  = st.toggle("👍 Confirmed only",   value=False)

        sort_by = st.selectbox("Sort by", [
            "📏 Distance (nearest first)",
            "👍 Most citizen confirms",
            "💧 Best water quality",
        ])

        search = st.button("🔍 Search Kiosks", type="primary", use_container_width=True)

        st.markdown("---")
        st.markdown("**Your location:**")
        st.map({"lat": [lat], "lon": [lon]}, zoom=13)

    with right:
        if search:
            with st.spinner("Searching nearby kiosks..."):
                try:
                    resp = requests.get(
                        f"{API_BASE}/api/summer/coolers",
                        params={"lat": lat, "lon": lon, "radius": radius},
                        timeout=15
                    )
                    resp.raise_for_status()
                    st.session_state.kiosk_result = resp.json()
                    st.session_state.api_calls += 1
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        data = st.session_state.kiosk_result
        if data:
            temp  = data.get("surface_temperature", {})
            adv   = data.get("heat_advisory", {})
            level = adv.get("level","LOW").upper()
            adv_cls = {
                "LOW":"advisory-low","MODERATE":"advisory-moderate",
                "HIGH":"advisory-high","EXTREME":"advisory-extreme"
            }.get(level,"advisory-low")
            icons = {"LOW":"🟢","MODERATE":"🟡","HIGH":"🟠","EXTREME":"🔴"}

            w1, w2, w3, w4 = st.columns(4)
            w1.metric("🌡️ Air",        f"{temp.get('air_celsius','--')}°C")
            w2.metric("🥵 Feels Like", f"{temp.get('feels_like_celsius','--')}°C",
                      delta=f"+{temp.get('feels_like_celsius',0)-temp.get('air_celsius',0):.0f}°C")
            w3.metric("🛣️ Asphalt",    f"{temp.get('asphalt_celsius','--')}°C")
            w4.metric("☀️ UV",         temp.get("uv_index","--"))

            st.markdown(f"""
            <div class='{adv_cls}' style='margin:14px 0;'>
                {icons.get(level,'🟢')} <b>Heat Advisory — {level}:</b> {adv.get('message','')}
            </div>
            """, unsafe_allow_html=True)

            kiosks = data.get("kiosks", [])
            if only_shade: kiosks = [k for k in kiosks if k.get("shade_available")]
            if only_open:  kiosks = [k for k in kiosks if k.get("operational")]
            if only_ro:    kiosks = [k for k in kiosks if k.get("water_quality")=="RO_PURIFIED"]
            if only_conf:  kiosks = [k for k in kiosks if k.get("citizen_confirms",0)>0]

            if "confirms" in sort_by:
                kiosks.sort(key=lambda k: k.get("citizen_confirms",0), reverse=True)
            elif "quality" in sort_by:
                order = {"RO_PURIFIED":0,"FILTERED":1,"POTABLE":2}
                kiosks.sort(key=lambda k: order.get(k.get("water_quality",""),9))

            if kiosks:
                nearest = min(k.get("distance_m",0) for k in kiosks)
                st.markdown(f"""
                <div class='stat-row'>
                    <div class='stat-card teal'>
                        <div class='val'>{len(kiosks)}</div><div class='lbl'>Found</div>
                    </div>
                    <div class='stat-card green'>
                        <div class='val'>{sum(1 for k in kiosks if k.get("operational"))}</div>
                        <div class='lbl'>Open now</div>
                    </div>
                    <div class='stat-card blue'>
                        <div class='val'>{nearest:.0f}m</div><div class='lbl'>Nearest</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.map({
                    "lat": [k["location"]["lat"] for k in kiosks] + [lat],
                    "lon": [k["location"]["lon"] for k in kiosks] + [lon],
                }, zoom=14)

            st.markdown("<div class='scroll-list'>", unsafe_allow_html=True)
            for i, k in enumerate(kiosks):
                dist     = k.get("distance_m", 0)
                walk_min = max(1, int(dist / 80))
                quality  = k.get("water_quality","")
                q_cls    = {
                    "FILTERED":"tag-blue","POTABLE":"tag-green","RO_PURIFIED":"tag-purple"
                }.get(quality,"tag-yellow")
                st.markdown(f"""
                <div class='kiosk-card'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                        <div style='flex:1;'>
                            <div style='font-size:1rem; font-weight:800; color:{text_main};'>
                                #{i+1} &nbsp; {k['name']}
                            </div>
                            <div style='font-size:0.83rem; color:{text_sub}; margin-top:6px; line-height:2;'>
                                🏷️ {k['type'].replace('_',' ').title()}<br>
                                🕐 {k.get('open_hours','N/A')}
                            </div>
                            <div style='margin-top:10px;'>
                                <span class='tag {q_cls}'>💧 {quality}</span>
                                {'<span class="tag tag-green">🌿 Shade</span>' if k.get('shade_available') else ''}
                                {'<span class="tag tag-green">🟢 Open</span>' if k.get('operational') else '<span class="tag tag-red">🔴 Closed</span>'}
                                <span class='tag tag-teal'>👍 {k.get('citizen_confirms',0)}</span>
                            </div>
                        </div>
                        <div style='text-align:right; margin-left:20px; flex-shrink:0;'>
                            <div style='font-size:1.9rem; font-weight:900; color:#1a73e8;'>{dist:.0f}m</div>
                            <div style='font-size:0.78rem; color:{text_sub}; margin-top:2px;'>~{walk_min} min walk</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            routes = data.get("canopy_routes", [])
            if routes:
                with st.expander("🌳 Shaded Routes Nearby"):
                    for r in routes:
                        st.markdown(f"**{r['name']}**")
                        st.caption(
                            f"🌡️ -{r.get('shade_reduction_celsius',0)}°C cooler · "
                            f"📏 {r.get('distance_to_start_m',0):.0f}m away"
                        )
                        st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — REPORT ISSUE
# ══════════════════════════════════════════════════════════════════════════════
elif "Report" in page:
    st.markdown("""
    <div class='hero'>
        <div class='hero-icon'>🌧️</div>
        <h1>Report an Issue</h1>
        <div class='sub'>Help your community · Report flooding, waterlogging & road damage</div>
        <div class='badges'>
            <span class='badge'>📤 Sent to AWS Lambda</span>
            <span class='badge'>🔒 Stored securely</span>
            <span class='badge'>📸 Photo support</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1, 1], gap="large")

    with left:
        with st.form("report_form", clear_on_submit=True):
            st.markdown("#### 📋 Issue Details")
            report_type = st.selectbox("Issue Type", [
                "🌊 Flooding","💧 Waterlogging","🚧 Road Damage",
                "🕳️ Drain Overflow","⚠️ Other"
            ])
            severity = st.select_slider("Severity",
                options=["🟢 Low","🟡 Medium","🟠 High","🔴 Critical"])
            description = st.text_area(
                "Description",
                placeholder="Water depth, road condition, vehicles stuck, people at risk...",
                height=130
            )
            st.markdown("#### 📍 Location")
            rc1, rc2 = st.columns(2)
            with rc1: r_lat = st.number_input("Latitude",  value=28.6315, format="%.4f", key="rl")
            with rc2: r_lon = st.number_input("Longitude", value=77.2167, format="%.4f", key="rn")

            st.markdown("#### 📸 Attach Photo (optional)")
            photo = st.file_uploader("photo", type=["jpg","jpeg","png"],
                                     label_visibility="collapsed", key="rphoto")
            if photo:
                st.image(photo, use_container_width=True)

            submitted = st.form_submit_button(
                "📤 Submit Report", use_container_width=True, type="primary"
            )

        if submitted:
            if not description.strip():
                st.warning("Please add a description.")
            else:
                bar = st.progress(0)
                for pct, msg in [
                    (25,"📦 Preparing report..."),
                    (55,"☁️ Sending to AWS Lambda..."),
                    (85,"💾 Saving report..."),
                    (100,"✅ Done!"),
                ]:
                    time.sleep(0.3); bar.progress(pct, text=msg)
                time.sleep(0.3); bar.empty()
                try:
                    payload = {
                        "lat": r_lat, "lon": r_lon,
                        "report_type": report_type,
                        "description": description,
                        "severity": severity
                    }
                    if photo:
                        photo.seek(0)
                        payload["photo_base64"] = base64.b64encode(photo.read()).decode("utf-8")
                    resp = requests.post(
                        f"{API_BASE}/api/monsoon/report",
                        json=payload, timeout=15
                    )
                    resp.raise_for_status()
                    st.session_state.report_count += 1
                    st.session_state.api_calls += 1
                    st.success("✅ Report submitted. Thank you for keeping your community safe!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Failed: {str(e)}")

    with right:
        st.markdown("#### 💡 Severity Guide")
        for sev, depth, bg in [
            ("🟢 Low",      "Ankle deep — passable with care",  "#d4edda"),
            ("🟡 Medium",   "Knee deep — slow traffic",         "#fff3cd"),
            ("🟠 High",     "Waist deep — road blocked",        "#ffe5d0"),
            ("🔴 Critical", "Above waist — danger to life",     "#f8d7da"),
        ]:
            st.markdown(f"""
            <div style='background:{bg}; border-radius:12px; padding:14px 18px;
                        margin-bottom:10px; transition:all 0.2s;'>
                <b>{sev}</b> — {depth}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"""
        <div class='stat-card blue' style='border-radius:18px; padding:24px; text-align:center;'>
            <div class='val'>{st.session_state.report_count}</div>
            <div class='lbl'>Reports submitted this session</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🗺️ Report location")
        st.map({"lat": [28.6315], "lon": [77.2167]}, zoom=13)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif "Dashboard" in page:
    st.markdown("""
    <div class='hero'>
        <div class='hero-icon'>📊</div>
        <h1>Live Dashboard</h1>
        <div class='sub'>Real-time overview · Kiosks · Heat conditions · Analytics</div>
        <div class='badges'>
            <span class='badge'>🔄 Live AWS data</span>
            <span class='badge'>🗺️ Interactive map</span>
            <span class='badge'>📈 Analytics</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    top1, top2 = st.columns([1, 2])
    with top1:
        refresh = st.button("🔄 Refresh Live Data", type="primary", use_container_width=True)
    with top2:
        dash_preset = st.selectbox("Location", [
            "Connaught Place, Delhi","India Gate, Delhi",
            "Chandni Chowk, Delhi","Karol Bagh, Delhi",
        ], label_visibility="collapsed")

    dash_coords = {
        "Connaught Place, Delhi": (28.6315, 77.2167),
        "India Gate, Delhi":      (28.6129, 77.2295),
        "Chandni Chowk, Delhi":   (28.6506, 77.2334),
        "Karol Bagh, Delhi":      (28.6519, 77.1909),
    }
    dlat, dlon = dash_coords.get(dash_preset, (28.6315, 77.2167))

    if refresh:
        with st.spinner("Fetching live data from AWS Lambda..."):
            try:
                resp = requests.get(
                    f"{API_BASE}/api/summer/coolers",
                    params={"lat": dlat, "lon": dlon, "radius": 5000},
                    timeout=15
                )
                resp.raise_for_status()
                st.session_state.kiosk_result = resp.json()
                st.session_state.api_calls += 1
            except Exception as e:
                st.error(f"Failed: {str(e)}")

    data = st.session_state.kiosk_result
    if data:
        kiosks   = data.get("kiosks", [])
        temp     = data.get("surface_temperature", {})
        adv      = data.get("heat_advisory", {})
        level    = adv.get("level","LOW").upper()
        total    = len(kiosks)
        open_k   = sum(1 for k in kiosks if k.get("operational"))
        shaded   = sum(1 for k in kiosks if k.get("shade_available"))
        confirms = sum(k.get("citizen_confirms",0) for k in kiosks)
        ro_count = sum(1 for k in kiosks if k.get("water_quality")=="RO_PURIFIED")

        st.markdown(f"""
        <div class='stat-row'>
            <div class='stat-card teal'>
                <div class='val'>{total}</div><div class='lbl'>Total Kiosks</div>
            </div>
            <div class='stat-card green'>
                <div class='val'>{open_k}</div><div class='lbl'>Open Now</div>
            </div>
            <div class='stat-card blue'>
                <div class='val'>{shaded}</div><div class='lbl'>With Shade</div>
            </div>
            <div class='stat-card orange'>
                <div class='val'>{confirms}</div><div class='lbl'>Confirms</div>
            </div>
            <div class='stat-card pink'>
                <div class='val'>{ro_count}</div><div class='lbl'>RO Purified</div>
            </div>
            <div class='stat-card indigo'>
                <div class='val'>{st.session_state.api_calls}</div><div class='lbl'>API Calls</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        dash_tab1, dash_tab2, dash_tab3 = st.tabs([
            "🌡️ Heat & Advisory", "🗺️ Map & Kiosks", "📈 Analytics"
        ])

        with dash_tab1:
            h1, h2, h3, h4 = st.columns(4)
            h1.metric("Air Temp",   f"{temp.get('air_celsius','--')}°C")
            h2.metric("Feels Like", f"{temp.get('feels_like_celsius','--')}°C")
            h3.metric("Asphalt",    f"{temp.get('asphalt_celsius','--')}°C")
            h4.metric("UV Index",   temp.get("uv_index","--"))

            adv_cls = {
                "LOW":"advisory-low","MODERATE":"advisory-moderate",
                "HIGH":"advisory-high","EXTREME":"advisory-extreme"
            }.get(level,"advisory-low")
            icons = {"LOW":"🟢","MODERATE":"🟡","HIGH":"🟠","EXTREME":"🔴"}
            st.markdown(f"""
            <div class='{adv_cls}' style='margin-top:16px;'>
                {icons.get(level,'🟢')} <b>Heat Advisory — {level}:</b> {adv.get('message','')}
            </div>
            """, unsafe_allow_html=True)

        with dash_tab2:
            if kiosks:
                st.map({
                    "lat": [k["location"]["lat"] for k in kiosks] + [dlat],
                    "lon": [k["location"]["lon"] for k in kiosks] + [dlon],
                }, zoom=13)
            for k in kiosks:
                status = "🟢" if k.get("operational") else "🔴"
                shade  = "🌿" if k.get("shade_available") else "☀️"
                st.markdown(
                    f"{status} {shade} **{k['name']}** · "
                    f"`{k.get('water_quality','')}` · 👍 {k.get('citizen_confirms',0)}"
                )

        with dash_tab3:
            st.markdown("#### 💧 Water Quality Breakdown")
            quality_counts = {}
            for k in kiosks:
                q = k.get("water_quality","UNKNOWN")
                quality_counts[q] = quality_counts.get(q, 0) + 1
            for q, cnt in sorted(quality_counts.items(), key=lambda x: x[1], reverse=True):
                pct = int((cnt / total) * 100) if total else 0
                ca, cb = st.columns([4, 1])
                with ca: st.progress(pct/100, text=f"  {q}")
                with cb: st.markdown(f"<div style='padding-top:6px; font-weight:700; text-align:right;'>{cnt}</div>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### 📏 Distance Distribution")
            distances = [k.get("distance_m",0) for k in kiosks]
            if distances:
                buckets = {"0–500m":0,"500m–1km":0,"1–2km":0,"2km+":0}
                for d in distances:
                    if d < 500:    buckets["0–500m"] += 1
                    elif d < 1000: buckets["500m–1km"] += 1
                    elif d < 2000: buckets["1–2km"] += 1
                    else:          buckets["2km+"] += 1
                for bucket, cnt in buckets.items():
                    if cnt > 0:
                        pct = int((cnt / len(distances)) * 100)
                        ca, cb = st.columns([4, 1])
                        with ca: st.progress(pct/100, text=f"  {bucket}")
                        with cb: st.markdown(f"<div style='padding-top:6px; font-weight:700; text-align:right;'>{cnt}</div>", unsafe_allow_html=True)
    else:
        st.info("Click **Refresh Live Data** to load the dashboard.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — ABOUT & API
# ══════════════════════════════════════════════════════════════════════════════
elif "About" in page:
    st.markdown("""
    <div class='hero'>
        <div class='hero-icon'>ℹ️</div>
        <h1>About Jal Drishti</h1>
        <div class='sub'>Smart water safety for Indian cities · Built entirely on AWS · ap-southeast-2</div>
    </div>
    """, unsafe_allow_html=True)

    tab_arch, tab_api, tab_test = st.tabs([
        "🏗️ Architecture", "🌐 API Reference", "🧪 Live API Tester"
    ])

    with tab_arch:
        cols = st.columns(3)
        for i, (icon, svc, desc, badge) in enumerate([
            ("🌐","Amazon API Gateway", "HTTP API routing all requests",       "tag-blue"),
            ("⚡","AWS Lambda",         "jal-drishti-brain + flood_analyzer",  "tag-blue"),
            ("🪣","Amazon S3",          "Secure flood image storage",          "tag-green"),
            ("🔍","Amazon Rekognition", "AI image analysis · DetectLabels",    "tag-purple"),
            ("🖥️","Elastic Beanstalk",  "Hosts this Streamlit frontend",       "tag-green"),
            ("📍","ap-southeast-2",     "Sydney · All services co-located",    "tag-teal"),
        ]):
            with cols[i % 3]:
                st.markdown(f"""
                <div class='glass-card' style='text-align:center; padding:32px 16px;'>
                    <div style='font-size:2.8rem; animation: float 3s ease-in-out {i*0.4}s infinite; display:inline-block;'>{icon}</div>
                    <div style='margin-top:12px;'><span class='tag {badge}'>{svc}</span></div>
                    <div style='font-size:0.85rem; color:{text_sub}; margin-top:10px; line-height:1.6;'>{desc}</div>
                </div>
                """, unsafe_allow_html=True)

    with tab_api:
        st.markdown("#### Live Endpoints")
        for method, path, live, desc in [
            ("GET",  "/api/summer/coolers", True,  "Find nearby water kiosks · params: lat, lon, radius"),
            ("POST", "/api/monsoon/report", True,  "Submit a flood or waterlogging report"),
            ("POST", "/api/flood/analyze",  False, "Analyze a flood image with Amazon Rekognition"),
        ]:
            m_cls  = "method-get" if method == "GET" else "method-post"
            status = "🟢 Live" if live else "🟡 Deploy flood_analyzer Lambda"
            st.markdown(f"""
            <div class='endpoint'>
                <span class='{m_cls}'>{method}</span> {path}
                &nbsp;&nbsp;<span style='opacity:0.6; font-size:0.8rem;'>{status}</span>
                <div style='font-size:0.78rem; opacity:0.5; margin-top:6px;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Base URL")
        st.code("https://ygg42zzgs1.execute-api.ap-southeast-2.amazonaws.com", language="bash")

    with tab_test:
        st.markdown("#### 🧪 Live API Tester")
        t1, t2 = st.columns(2)
        with t1:
            test_lat = st.number_input("Latitude",  value=28.6315, format="%.4f", key="tl")
            test_lon = st.number_input("Longitude", value=77.2167, format="%.4f", key="tn")
        with t2:
            test_radius = st.slider("Radius", 200, 2000, 800, 100, key="tr")

        if st.button("▶️ Run GET /api/summer/coolers", type="primary", use_container_width=True):
            with st.spinner("Calling API..."):
                try:
                    r = requests.get(
                        f"{API_BASE}/api/summer/coolers",
                        params={"lat": test_lat, "lon": test_lon, "radius": test_radius},
                        timeout=10
                    )
                    st.session_state.api_test_result = {"status": r.status_code, "body": r.json()}
                    st.session_state.api_calls += 1
                except Exception as e:
                    st.error(f"❌ {str(e)}")

        if st.session_state.api_test_result:
            res  = st.session_state.api_test_result
            code = res["status"]
            st.markdown(f"""
            <div style='background:{"#d4edda" if code==200 else "#f8d7da"};
                        border-radius:12px; padding:14px 18px; margin-bottom:14px;'>
                <b>HTTP {code}</b> — {"✅ Success" if code==200 else "❌ Error"}
            </div>
            """, unsafe_allow_html=True)
            st.json(res["body"])
