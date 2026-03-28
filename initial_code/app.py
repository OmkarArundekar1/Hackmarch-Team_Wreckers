import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import json
import math
import time

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="VitalMirror — See the age your body feels",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS INJECTION
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap');

/* ── Reset & Global ── */
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
.main { background: #0D0D1A; }
.block-container { padding-top: 1.5rem; padding-bottom: 4rem; max-width: 860px; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #13132A !important;
    border-right: 1px solid rgba(108,92,231,0.2) !important;
}
[data-testid="stSidebar"] * { color: #C8C8E8 !important; }
[data-testid="stSidebar"] h3 { color: #fff !important; font-size: 14px !important; }

/* ── Logo / Header ── */
.vm-header {
    display: flex; align-items: center; gap: 14px;
    padding: 0 0 1.8rem; border-bottom: 1px solid rgba(108,92,231,0.2);
    margin-bottom: 1.8rem;
}
.vm-logo-text {
    font-family: 'DM Serif Display', serif;
    font-size: 26px; color: #fff; letter-spacing: -0.5px;
}
.vm-logo-text span { color: #6C5CE7; }
.vm-badge {
    margin-left: auto; font-size: 11px; font-weight: 600;
    color: #6C5CE7; background: rgba(108,92,231,0.12);
    border: 1px solid rgba(108,92,231,0.35);
    padding: 5px 14px; border-radius: 99px; letter-spacing: 0.5px;
}

/* ── Hero ── */
.hero-eyebrow {
    font-size: 11px; font-weight: 700; letter-spacing: 3px;
    text-transform: uppercase; color: #6C5CE7;
    display: flex; align-items: center; gap: 10px; margin-bottom: 14px;
}
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 56px; line-height: 1.05; letter-spacing: -2px;
    color: #fff; margin-bottom: 16px;
}
.hero-title em { font-style: italic; color: #6C5CE7; }
.hero-title .green { color: #1D9E75; }
.hero-sub {
    font-size: 17px; font-weight: 300; color: #9090B8;
    line-height: 1.75; max-width: 560px; margin-bottom: 2rem;
}
.hero-tagline {
    font-size: 13px; font-weight: 600; color: #1D9E75;
    letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 2.5rem;
}

/* ── Cards ── */
.g-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(108,92,231,0.2);
    border-radius: 18px; padding: 28px 32px;
    box-shadow: 0 4px 40px rgba(0,0,0,0.4);
    margin-bottom: 20px;
}
.g-card-title {
    font-family: 'DM Serif Display', serif;
    font-size: 22px; letter-spacing: -0.4px; color: #fff; margin-bottom: 5px;
}
.g-card-sub { font-size: 14px; color: #7A7AA0; font-weight: 300; line-height: 1.65; margin-bottom: 20px; }

/* ── Metric cards ── */
.metric-row { display: flex; gap: 12px; flex-wrap: wrap; margin: 18px 0; }
.metric-box {
    flex: 1; min-width: 120px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(108,92,231,0.18);
    border-radius: 14px; padding: 16px 18px;
}
.metric-box-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1.2px; color: #6060A0; margin-bottom: 6px; }
.metric-box-val { font-size: 22px; font-weight: 700; color: #fff; }
.metric-box-sub { font-size: 12px; color: #7A7AA0; margin-top: 3px; }
.metric-box.good { border-color: rgba(29,158,117,0.35); }
.metric-box.good .metric-box-val { color: #1D9E75; }
.metric-box.warn { border-color: rgba(186,117,23,0.35); }
.metric-box.warn .metric-box-val { color: #E09020; }
.metric-box.bad  { border-color: rgba(216,90,48,0.35); }
.metric-box.bad  .metric-box-val { color: #D85A30; }

/* ── Bio age reveal ── */
.bio-ring-wrap { text-align: center; padding: 24px 0 10px; }
.bio-age-big {
    font-family: 'DM Serif Display', serif;
    font-size: 100px; line-height: 1; color: #6C5CE7;
    animation: fadeInUp 0.6s ease;
}
.bio-age-big.older { color: #D85A30; }
.bio-age-big.younger { color: #1D9E75; }
.bio-reveal-label { font-size: 12px; color: #6060A0; letter-spacing: 2px; text-transform: uppercase; margin-top: 4px; }
.bio-reveal-text {
    font-family: 'DM Serif Display', serif;
    font-size: 24px; color: #fff; margin: 16px 0 6px; line-height: 1.3;
}
.bio-reveal-sub { font-size: 14px; color: #7A7AA0; line-height: 1.6; }

/* ── Risk banner ── */
.risk-banner {
    display: flex; align-items: flex-start; gap: 14px;
    padding: 18px 22px; border-radius: 14px; margin: 18px 0; border: 1px solid;
}
.risk-banner.high { background: rgba(216,90,48,0.12); border-color: rgba(216,90,48,0.3); }
.risk-banner.medium { background: rgba(186,117,23,0.12); border-color: rgba(224,144,32,0.3); }
.risk-banner.low { background: rgba(29,158,117,0.12); border-color: rgba(29,158,117,0.3); }
.risk-banner-text { font-size: 14px; color: #C8C8E0; line-height: 1.65; }

/* ── Insight factor cards ── */
.factor-card {
    background: rgba(255,255,255,0.04);
    border-left: 4px solid #6C5CE7;
    border-radius: 0 12px 12px 0;
    padding: 16px 20px; margin-bottom: 12px;
}
.factor-card.bad  { border-left-color: #D85A30; }
.factor-card.warn { border-left-color: #E09020; }
.factor-card.good { border-left-color: #1D9E75; }
.factor-name { font-size: 15px; font-weight: 600; color: #fff; margin-bottom: 4px; }
.factor-desc { font-size: 13px; color: #7A7AA0; line-height: 1.5; }
.factor-bar-track { height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; margin-top: 10px; }
.factor-bar-fill { height: 100%; border-radius: 3px; transition: width 1s ease; }

/* ── Years gained ── */
.years-gained-hero {
    background: linear-gradient(135deg, rgba(108,92,231,0.18) 0%, rgba(29,158,117,0.18) 100%);
    border: 1px solid rgba(108,92,231,0.25);
    border-radius: 18px; padding: 32px 24px; text-align: center; margin: 18px 0;
}
.years-number {
    font-family: 'DM Serif Display', serif;
    font-size: 84px; line-height: 1; color: #6C5CE7;
}
.years-label { font-size: 16px; font-weight: 500; color: #9090B8; margin-top: 8px; }
.years-sub { font-size: 13px; color: #6060A0; margin-top: 5px; }

/* ── Progress bar ── */
.prog-bar-wrap { display: flex; align-items: center; gap: 14px; margin: 12px 0; }
.prog-label { font-size: 13px; color: #7A7AA0; min-width: 100px; }
.prog-track { flex: 1; height: 8px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden; }
.prog-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #1D9E75, #0F6E56); }
.prog-val { font-size: 14px; font-weight: 700; color: #1D9E75; min-width: 44px; text-align: right; }

/* ── Habit cards ── */
.habit-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(108,92,231,0.2);
    border-left: 5px solid #6C5CE7;
    border-radius: 14px; padding: 20px 22px; margin-bottom: 14px;
    transition: all 0.3s;
}
.habit-card.added {
    border-color: rgba(29,158,117,0.3);
    border-left-color: #1D9E75;
    background: rgba(29,158,117,0.08);
}
.habit-action { font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 8px; }
.habit-impact { font-size: 13px; color: #7A7AA0; line-height: 1.6; margin-bottom: 12px; }
.credit-badge {
    display: inline-block;
    font-size: 12px; font-weight: 700; color: #6C5CE7;
    background: rgba(108,92,231,0.15); padding: 4px 14px; border-radius: 99px;
}
.credit-badge.green { color: #1D9E75; background: rgba(29,158,117,0.15); }

/* ── Streak ── */
.streak-num {
    font-family: 'DM Serif Display', serif;
    font-size: 68px; color: #1D9E75; text-align: center; line-height: 1;
}
.streak-label { font-size: 12px; color: #6060A0; text-align: center; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; }

/* ── Share card ── */
.share-card {
    background: linear-gradient(135deg, #4B3FBB 0%, #6C5CE7 50%, #0F6E56 100%);
    border-radius: 18px; padding: 36px 28px; text-align: center;
    color: white; margin: 20px 0;
}
.share-number { font-family: 'DM Serif Display', serif; font-size: 76px; line-height: 1; }
.share-label { font-size: 18px; opacity: 0.9; margin-top: 8px; }
.share-sub { font-size: 13px; opacity: 0.65; margin-top: 6px; }

/* ── Sample bar ── */
.sample-bar {
    background: rgba(108,92,231,0.12);
    border: 1px dashed rgba(108,92,231,0.4);
    border-radius: 14px; padding: 16px 22px;
    margin-bottom: 20px;
    display: flex; align-items: center; justify-content: space-between;
}
.sample-bar-text { font-size: 14px; font-weight: 600; color: #A0A0D8; }
.sample-bar-sub { font-size: 12px; color: #6060A0; margin-top: 2px; }

/* ── Label overrides ── */
[data-testid="stNumberInput"] label,
[data-testid="stSlider"] label,
[data-testid="stSelectbox"] label,
[data-testid="stCheckbox"] label,
[data-testid="stFileUploader"] label { color: #9090B8 !important; font-size: 13px !important; font-weight: 500 !important; }
[data-testid="stSlider"] { background: transparent !important; }

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; border-radius: 99px !important;
    transition: all 0.25s !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(108,92,231,0.3) !important;
    color: #C8C8E8 !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #4B3FBB, #6C5CE7) !important;
    border: none !important;
    box-shadow: 0 4px 24px rgba(108,92,231,0.4) !important;
    color: #fff !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    box-shadow: 0 6px 32px rgba(108,92,231,0.55) !important;
    transform: translateY(-1px);
}

/* ── Animations ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Divider ── */
.section-divider { height: 1px; background: rgba(108,92,231,0.15); margin: 24px 0; }

/* ── Info boxes ── */
[data-testid="stInfo"] { background: rgba(108,92,231,0.12) !important; border-color: rgba(108,92,231,0.3) !important; color: #C8C8E8 !important; }
[data-testid="stSuccess"] { background: rgba(29,158,117,0.12) !important; border-color: rgba(29,158,117,0.3) !important; color: #C8C8E8 !important; }
[data-testid="stWarning"] { background: rgba(224,144,32,0.12) !important; border-color: rgba(224,144,32,0.3) !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "screen": "landing",
        "inputs": {},
        "bio_age": None,
        "confidence": None,
        "chrono_age": None,
        "top_features": [],
        "family_history": {},
        "risk_result": None,
        "recommendations": [],
        "sim_bio_age": None,
        "sim_years_gained": 0.0,
        "sim_risk_delta": 0.0,
        "added_habits": [],
        "total_life_credits": 0.0,
        "_sample_loaded": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

SCREEN_ORDER = ["landing", "input", "reveal", "dashboard", "simulation", "coach"]
SCREEN_LABELS = {
    "landing":    ("🧬", "Start"),
    "input":      ("📋", "Your Data"),
    "reveal":     ("🪞", "Bio Age"),
    "dashboard":  ("📊", "Insights"),
    "simulation": ("⏳", "Time Machine"),
    "coach":      ("🏆", "Coach"),
}


# ─────────────────────────────────────────────
# SIDEBAR PROGRESS
# ─────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("### 🧬 VitalMirror")
        st.markdown("---")
        current = st.session_state.screen
        cur_idx = SCREEN_ORDER.index(current)
        for i, key in enumerate(SCREEN_ORDER):
            icon, label = SCREEN_LABELS[key]
            if i < cur_idx:
                st.markdown(f"✅ &nbsp; **{label}**", unsafe_allow_html=True)
            elif i == cur_idx:
                st.markdown(f"▶️ &nbsp; **{label}**", unsafe_allow_html=True)
            else:
                st.markdown(f"○ &nbsp; {label}", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### 🔑 Anthropic API Key")
        api_key = st.text_input("Enter your API key", type="password",
                                 placeholder="sk-ant-...", key="api_key_input",
                                 label_visibility="collapsed")
        st.caption("Optional — powers Claude analysis. Leave blank for demo mode.")
        st.markdown("---")
        st.caption("Built for **Hackmarch 2025** by Team Wreckers 🚀")

render_sidebar()


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
def render_header():
    st.markdown("""
    <div class="vm-header">
      <div class="vm-logo-text">Vital<span>Mirror</span></div>
      <div class="vm-badge">🏆 Hackathon Demo</div>
    </div>
    """, unsafe_allow_html=True)

render_header()


# ─────────────────────────────────────────────
# BACKEND STUB HELPERS
# ─────────────────────────────────────────────
def _stub_cosinor(inputs: dict, csv_path=None) -> dict:
    """Stub for cosinor_run — replace with real import when ready."""
    # TODO: connect backend
    # from cosinor_module import run as cosinor_run
    # return cosinor_run(inputs, csv_path=csv_path)
    age = inputs.get("age", 30)
    sleep = inputs.get("sleep_hours", 7)
    steps = inputs.get("steps_per_day", 7000)
    rhr = inputs.get("resting_hr", 72)
    penalty = 0.0
    if sleep < 6:    penalty += (6 - sleep) * 2.2
    if rhr > 75:     penalty += (rhr - 75) * 0.08
    if steps < 5000: penalty += (5000 - steps) / 1000 * 0.5
    return {
        "bio_age": round(age + penalty, 1),
        "confidence": round(0.72 + min(0.20, penalty / 30), 2),
        "top_features": ["sleep_hours", "resting_hr", "steps_per_day", "weight_kg"],
    }


def _stub_fuse(results: list) -> float:
    """Stub for fuse_bio_ages."""
    # TODO: connect backend
    # from fusion import fuse_bio_ages
    # return fuse_bio_ages(results)
    if not results:
        return 35.0
    total_w = sum(r["confidence"] for r in results)
    return round(sum(r["bio_age"] * r["confidence"] for r in results) / total_w, 1)


def _stub_predict_risk(bio_age: float, chrono_age: int, family_history: dict) -> dict:
    """Stub for predict_risk."""
    # TODO: connect backend
    # from risk_predictor import predict_risk
    # return predict_risk(bio_age, chrono_age, family_history)
    diff = bio_age - chrono_age
    base_risk = max(3, min(35, 10 + diff * 1.5))
    if family_history.get("heart_disease_parent"): base_risk += 4
    if family_history.get("diabetes_parent"):      base_risk += 2
    curve = [(yr, round(100 - base_risk * (yr / 10) * (1 + 0.05 * yr), 1))
             for yr in range(1, 11)]
    return {"risk_10yr": round(base_risk, 1), "kaplan_curve": curve}


def _stub_simulate(feature_name: str, new_value: float, base_bio_age: float) -> dict:
    """Stub for simulate."""
    # TODO: connect backend
    # from habit_simulator import simulate
    # return simulate(feature_name, new_value, base_bio_age)
    deltas = {
        "sleep_hours":    lambda v: (8 - v) * (-0.7),
        "steps_per_day":  lambda v: (10000 - v) / 10000 * (-1.2),
        "weight_kg":      lambda v: 0.0,
    }
    fn = deltas.get(feature_name, lambda v: 0.0)
    delta = fn(new_value)
    new_age = round(max(18, base_bio_age + delta), 1)
    return {
        "new_bio_age": new_age,
        "risk_delta": round(delta * 1.5, 1),
        "life_credits": round(abs(delta) * 0.8, 2),
    }


def _stub_recommendations(top_features: list, family_history: dict, bio_age: float) -> list:
    """Stub for get_recommendations."""
    # TODO: connect backend
    # from recommendation_engine import get_recommendations
    # return get_recommendations(top_features, family_history, bio_age)
    recs = [
        {"habit": "Sleep 7–8 hours tonight",
         "impact_pct": 18, "life_credits": 1.4, "months_equiv": 5},
        {"habit": "10-min walk after dinner",
         "impact_pct": 14, "life_credits": 1.1, "months_equiv": 4},
        {"habit": "Replace one sugary drink with water",
         "impact_pct": 9, "life_credits": 0.7, "months_equiv": 2},
    ]
    if family_history.get("heart_disease_parent"):
        recs.insert(0, {"habit": "Check blood pressure weekly",
                        "impact_pct": 22, "life_credits": 1.8, "months_equiv": 7})
    return recs[:3]


# ─────────────────────────────────────────────
# PLOTLY GAUGE
# ─────────────────────────────────────────────
def bio_age_gauge(bio_age: float, chrono_age: int, animate_steps: int = 0) -> go.Figure:
    diff = bio_age - chrono_age
    if diff > 4:
        needle_color = "#D85A30"
    elif diff > 0:
        needle_color = "#E09020"
    else:
        needle_color = "#1D9E75"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=bio_age,
        number={"font": {"size": 56, "color": needle_color, "family": "DM Serif Display"}},
        gauge={
            "axis": {"range": [18, 80], "tickwidth": 1, "tickcolor": "#444468",
                     "tickfont": {"color": "#6060A0", "size": 11}},
            "bar": {"color": needle_color, "thickness": 0.28},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [18, 30], "color": "rgba(29,158,117,0.35)"},
                {"range": [30, 45], "color": "rgba(108,92,231,0.25)"},
                {"range": [45, 60], "color": "rgba(224,144,32,0.30)"},
                {"range": [60, 80], "color": "rgba(216,90,48,0.35)"},
            ],
            "threshold": {
                "line": {"color": "#6C5CE7", "width": 3},
                "thickness": 0.8,
                "value": chrono_age,
            },
        },
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#fff"},
    )
    fig.add_annotation(
        x=0.5, y=0.12, xref="paper", yref="paper",
        text=f"<b>Chronological age: {chrono_age}</b> (purple line)",
        showarrow=False,
        font={"size": 11, "color": "#7A7AAA"},
    )
    return fig


# ─────────────────────────────────────────────
# SCREEN 1 — LANDING
# ─────────────────────────────────────────────
def render_landing():
    st.markdown("""
    <div>
      <div class="hero-eyebrow"><span>──</span> Mirror · Time Machine · Coach <span>──</span></div>
      <div class="hero-title">See the age your<br><em>body truly feels.</em></div>
      <div class="hero-tagline">See the age your body feels. Change one habit. Gain years back.</div>
      <div class="hero-sub">
        In 60 seconds, VitalMirror calculates your biological age from your health signals —
        then shows you exactly which one habit would add the most years back to your life.
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown("""
        <div class="g-card" style="text-align:center;">
          <div style="font-size:32px;margin-bottom:8px;">🪞</div>
          <div class="g-card-title" style="font-size:16px;">Mirror</div>
          <div class="g-card-sub" style="margin-bottom:0;">Your biological age revealed — not just a number, a story.</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="g-card" style="text-align:center;">
          <div style="font-size:32px;margin-bottom:8px;">⏳</div>
          <div class="g-card-title" style="font-size:16px;">Time Machine</div>
          <div class="g-card-sub" style="margin-bottom:0;">Simulate any habit change. See the years you'd gain.</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="g-card" style="text-align:center;">
          <div style="font-size:32px;margin-bottom:8px;">🏆</div>
          <div class="g-card-title" style="font-size:16px;">Coach</div>
          <div class="g-card-sub" style="margin-bottom:0;">Your top 2 micro-habits, ranked by life impact.</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    if st.button("🧬 Start — Reveal my biological age", type="primary", use_container_width=True):
        st.session_state.screen = "input"
        st.rerun()


# ─────────────────────────────────────────────
# SCREEN 2 — DATA INPUT
# ─────────────────────────────────────────────
RIYA_DATA = {
    "age": 32, "sex": "Female", "height_cm": 165, "weight_kg": 72,
    "resting_hr": 80, "sleep_hours": 5.0, "steps_per_day": 3000,
    "family_history": {
        "heart_disease_parent": True,
        "diabetes_parent": False,
        "cancer_parent": False,
        "parent_longevity_85plus": False,
    },
}

def render_input():
    st.markdown("""
    <div class="g-card-title" style="font-size:28px;color:#fff;font-family:'DM Serif Display',serif;margin-bottom:4px;">Your health data</div>
    <div class="g-card-sub">Tell us about yourself. Only age, weight, and height are required — everything else sharpens the picture.</div>
    """, unsafe_allow_html=True)

    # Riya demo loader
    st.markdown("""
    <div class="sample-bar">
      <div>
        <div class="sample-bar-text">📊 Try with Riya's data — 2-min judge demo</div>
        <div class="sample-bar-sub">Age 32 · Sedentary · 5h sleep · 3,000 steps · Family heart history</div>
      </div>
      <div style="color:#6C5CE7;font-weight:700;font-size:18px;">↓</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⚡ Load Riya's data", use_container_width=False):
        st.session_state["_sample_loaded"] = True
        st.rerun()

    use_sample = st.session_state.get("_sample_loaded", False)
    d = RIYA_DATA if use_sample else {}

    with st.container():
        st.markdown('<div class="g-card">', unsafe_allow_html=True)
        st.markdown("#### 👤 Basic info")
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age (years)", min_value=18, max_value=90,
                                  value=d.get("age", 30), step=1, key="inp_age")
            weight_kg = st.number_input("Weight (kg)", min_value=35, max_value=220,
                                         value=d.get("weight_kg", 70), step=1, key="inp_weight")
            resting_hr = st.number_input("Resting heart rate (bpm)", min_value=40, max_value=120,
                                          value=d.get("resting_hr", 72), step=1, key="inp_hr")
        with col2:
            sex = st.selectbox("Biological sex", ["Female", "Male", "Other / prefer not to say"],
                               index=0 if d.get("sex") == "Female" else 1, key="inp_sex")
            height_cm = st.number_input("Height (cm)", min_value=140, max_value=220,
                                         value=d.get("height_cm", 170), step=1, key="inp_height")

        st.markdown("#### 🏃 Daily habits")
        sleep_hours = st.slider("💤 What if you slept X hours tonight?",
                                 min_value=4.0, max_value=10.0,
                                 value=d.get("sleep_hours", 7.0), step=0.5, key="inp_sleep")
        steps_per_day = st.slider("🚶 How many steps do you average per day?",
                                   min_value=1000, max_value=15000,
                                   value=d.get("steps_per_day", 7000), step=500, key="inp_steps")

        st.markdown("#### 👨‍👩‍👧 Family history")
        fh_defaults = d.get("family_history", {})
        col3, col4 = st.columns(2)
        with col3:
            fh_heart   = st.checkbox("Parent had heart disease",    value=fh_defaults.get("heart_disease_parent", False), key="fh_heart")
            fh_diabetes = st.checkbox("Parent had diabetes",        value=fh_defaults.get("diabetes_parent", False), key="fh_diabetes")
        with col4:
            fh_cancer   = st.checkbox("Parent had cancer",         value=fh_defaults.get("cancer_parent", False), key="fh_cancer")
            fh_longevity = st.checkbox("Parents lived past 85",    value=fh_defaults.get("parent_longevity_85plus", False), key="fh_longevity")

        st.markdown("#### 📁 Optional uploads")
        col5, col6 = st.columns(2)
        with col5:
            wearable_csv = st.file_uploader("🏷 Wearable CSV (sleep/steps data)",
                                             type=["csv"], key="wearable_csv",
                                             help="Upload a .csv from Fitbit, Apple Health, Garmin, etc.")
        with col6:
            photo_file = st.file_uploader("📷 Photo (optional — adds facial age signal)",
                                           type=["jpg", "jpeg", "png"], key="photo_file",
                                           help="Optional. Used only to estimate facial age cues.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    col_back, col_fwd = st.columns([1, 2])
    with col_back:
        if st.button("← Home", use_container_width=True):
            st.session_state.screen = "landing"; st.rerun()
    with col_fwd:
        if st.button("🧬 Analyse my signals →", type="primary", use_container_width=True):
            bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)
            family_history = {
                "heart_disease_parent": fh_heart,
                "diabetes_parent": fh_diabetes,
                "cancer_parent": fh_cancer,
                "parent_longevity_85plus": fh_longevity,
            }
            inputs = {
                "age": age, "sex": sex, "height_cm": height_cm,
                "weight_kg": weight_kg, "bmi": bmi,
                "resting_hr": resting_hr, "sleep_hours": sleep_hours,
                "steps_per_day": steps_per_day,
            }
            with st.spinner("🔬 Analysing your signals…"):
                time.sleep(1.0)
                csv_path = None
                if wearable_csv is not None:
                    csv_path = wearable_csv  # pass file object; backend accepts path or object

                # TODO: connect backend — replace stubs below
                cosinor_result = _stub_cosinor(inputs, csv_path=csv_path)
                fused_bio_age  = _stub_fuse([cosinor_result])
                risk_result    = _stub_predict_risk(fused_bio_age, age, family_history)
                recs           = _stub_recommendations(cosinor_result["top_features"],
                                                       family_history, fused_bio_age)

            st.session_state.inputs          = inputs
            st.session_state.bio_age         = fused_bio_age
            st.session_state.confidence      = cosinor_result["confidence"]
            st.session_state.chrono_age      = age
            st.session_state.top_features    = cosinor_result["top_features"]
            st.session_state.family_history  = family_history
            st.session_state.risk_result     = risk_result
            st.session_state.recommendations = recs
            st.session_state.sim_bio_age     = fused_bio_age
            st.session_state.sim_years_gained = 0.0
            st.session_state.screen          = "reveal"
            st.rerun()


# ─────────────────────────────────────────────
# SCREEN 3 — BIOLOGICAL AGE REVEAL
# ─────────────────────────────────────────────
def render_reveal():
    bio_age    = st.session_state.bio_age
    chrono_age = st.session_state.chrono_age
    confidence = st.session_state.confidence
    inp        = st.session_state.inputs
    diff       = round(bio_age - chrono_age, 1)

    if diff > 0:
        color_cls   = "older"
        reveal_text = f"Your body feels {diff} years older than you are."
        reveal_sub  = "But that's just today. One habit change can start reversing the clock."
    elif diff < 0:
        color_cls   = "younger"
        reveal_text = f"Your body feels {abs(diff)} years younger — impressive!"
        reveal_sub  = "Keep it up. The Time Machine will show you how to maintain this edge."
        st.balloons()
    else:
        color_cls   = ""
        reveal_text = "Your biological age matches your chronological age."
        reveal_sub  = "Room to improve — see which levers move the needle most."

    # Big reveal
    with st.container():
        st.markdown(f"""
        <div class="g-card bio-ring-wrap">
          <div class="bio-reveal-label">biological age</div>
          <div class="bio-age-big {color_cls}">{bio_age}</div>
          <div class="bio-reveal-text">{reveal_text}</div>
          <div class="bio-reveal-sub">{reveal_sub}</div>
        </div>
        """, unsafe_allow_html=True)

    # Gauge chart
    fig = bio_age_gauge(bio_age, chrono_age)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Confidence + diff metrics
    diff_label = f"+{diff} yrs" if diff >= 0 else f"{diff} yrs"
    diff_color = "#D85A30" if diff > 0 else "#1D9E75"
    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-box {'bad' if diff > 4 else ('warn' if diff > 0 else 'good')}">
        <div class="metric-box-label">Vs chronological</div>
        <div class="metric-box-val">{diff_label}</div>
        <div class="metric-box-sub">{"Needs attention" if diff > 4 else ("Slightly elevated" if diff > 0 else "Excellent!")}</div>
      </div>
      <div class="metric-box">
        <div class="metric-box-label">Model confidence</div>
        <div class="metric-box-val">{round(confidence*100)}%</div>
        <div class="metric-box-sub">Signal quality</div>
      </div>
      <div class="metric-box {'bad' if inp['bmi'] > 30 else ('warn' if inp['bmi'] > 25 else 'good')}">
        <div class="metric-box-label">BMI</div>
        <div class="metric-box-val">{inp['bmi']}</div>
        <div class="metric-box-sub">{'Obese' if inp['bmi'] > 30 else ('Overweight' if inp['bmi'] > 25 else 'Healthy')}</div>
      </div>
      <div class="metric-box {'bad' if inp['resting_hr'] > 80 else ('warn' if inp['resting_hr'] > 70 else 'good')}">
        <div class="metric-box-label">Resting HR</div>
        <div class="metric-box-val">{inp['resting_hr']} bpm</div>
        <div class="metric-box-sub">{'Elevated' if inp['resting_hr'] > 80 else ('Normal' if inp['resting_hr'] > 65 else 'Athletic')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_back, col_fwd = st.columns([1, 2])
    with col_back:
        if st.button("← Edit data", use_container_width=True):
            st.session_state.screen = "input"; st.rerun()
    with col_fwd:
        if st.button("📊 See what's driving this →", type="primary", use_container_width=True):
            st.session_state.screen = "dashboard"; st.rerun()


# ─────────────────────────────────────────────
# SCREEN 4 — INSIGHT DASHBOARD
# ─────────────────────────────────────────────
FEATURE_META = {
    "sleep_hours":   {"label": "Sleep duration",       "ideal": "7–8 h/night",  "icon": "💤"},
    "resting_hr":    {"label": "Resting heart rate",   "ideal": "< 65 bpm",     "icon": "❤️"},
    "steps_per_day": {"label": "Daily movement",       "ideal": "> 8,000 steps","icon": "🚶"},
    "weight_kg":     {"label": "Body weight / BMI",    "ideal": "BMI 18.5–24.9","icon": "⚖️"},
    "bmi":           {"label": "BMI",                  "ideal": "18.5–24.9",    "icon": "⚖️"},
}

def _feature_severity(name: str, inp: dict) -> str:
    v = inp.get(name)
    if v is None: return "warn"
    if name == "sleep_hours":   return "bad"  if v < 6 else ("warn" if v < 7 else "good")
    if name == "resting_hr":    return "bad"  if v > 80 else ("warn" if v > 70 else "good")
    if name == "steps_per_day": return "bad"  if v < 3000 else ("warn" if v < 6000 else "good")
    if name in ("weight_kg", "bmi"):
        bmi = inp.get("bmi", 22)
        return "bad" if bmi > 30 else ("warn" if bmi > 25 else "good")
    return "warn"

def _feature_bar_pct(name: str, inp: dict) -> int:
    v = inp.get(name)
    if v is None: return 50
    if name == "sleep_hours":   return int(min(100, max(0, (v / 9) * 100)))
    if name == "resting_hr":    return int(min(100, max(0, ((100 - v) / 60) * 100)))
    if name == "steps_per_day": return int(min(100, max(0, (v / 10000) * 100)))
    if name in ("weight_kg", "bmi"):
        bmi = inp.get("bmi", 22)
        return int(min(100, max(0, ((30 - bmi) / 12) * 100)))
    return 50

def render_dashboard():
    bio_age    = st.session_state.bio_age
    chrono_age = st.session_state.chrono_age
    inp        = st.session_state.inputs
    risk       = st.session_state.risk_result or {}
    features   = st.session_state.top_features

    st.markdown("""
    <div class="g-card-title" style="font-size:28px;color:#fff;font-family:'DM Serif Display',serif;margin-bottom:4px;">What's driving your age</div>
    <div class="g-card-sub">Your top contributing factors, colour-coded by impact. Green = good, amber = needs work, coral = urgent.</div>
    """, unsafe_allow_html=True)

    for feat in features[:4]:
        meta     = FEATURE_META.get(feat, {"label": feat, "ideal": "—", "icon": "📌"})
        severity = _feature_severity(feat, inp)
        bar_pct  = _feature_bar_pct(feat, inp)
        bar_color = {"good": "#1D9E75", "warn": "#E09020", "bad": "#D85A30"}.get(severity, "#6C5CE7")
        val = inp.get(feat, "—")
        if feat == "sleep_hours": val_str = f"{val}h / night"
        elif feat == "resting_hr": val_str = f"{val} bpm"
        elif feat == "steps_per_day": val_str = f"{int(val):,} steps/day"
        elif feat in ("weight_kg",): val_str = f"{val} kg (BMI {inp.get('bmi','—')})"
        else: val_str = str(val)

        st.markdown(f"""
        <div class="factor-card {severity}">
          <div class="factor-name">{meta['icon']} {meta['label']} — {val_str}</div>
          <div class="factor-desc">Ideal: {meta['ideal']}</div>
          <div class="factor-bar-track">
            <div class="factor-bar-fill" style="width:{bar_pct}%;background:{bar_color};"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Risk summary
    risk_10yr = risk.get("risk_10yr", 12)
    risk_lvl  = "high" if risk_10yr > 20 else ("medium" if risk_10yr > 12 else "low")
    risk_icon = {"high": "⚠️", "medium": "📊", "low": "✅"}[risk_lvl]
    st.markdown(f"""
    <div class="risk-banner {risk_lvl}">
      <div style="font-size:22px;">{risk_icon}</div>
      <div class="risk-banner-text">
        <strong>10-year cardiovascular risk: {risk_10yr}%</strong><br>
        {"Elevated — your sleep deficit and low daily movement are the primary drivers. Small, consistent habit changes can meaningfully lower this." if risk_10yr > 15 else "Moderate — maintaining or improving your habits will keep your risk in check."}
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_back, col_fwd = st.columns([1, 2])
    with col_back:
        if st.button("← Back to Reveal", use_container_width=True):
            st.session_state.screen = "reveal"; st.rerun()
    with col_fwd:
        if st.button("⏳ Open the Time Machine →", type="primary", use_container_width=True):
            st.session_state.screen = "simulation"; st.rerun()


# ─────────────────────────────────────────────
# SCREEN 5 — TIME MACHINE / SIMULATION
# ─────────────────────────────────────────────
def render_simulation():
    bio_age    = st.session_state.bio_age
    chrono_age = st.session_state.chrono_age
    inp        = st.session_state.inputs

    st.markdown("""
    <div class="g-card-title" style="font-size:28px;color:#fff;font-family:'DM Serif Display',serif;margin-bottom:4px;">The Time Machine</div>
    <div class="g-card-sub">Adjust one habit. Watch your projected biological age update instantly.</div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="g-card">', unsafe_allow_html=True)
    sleep_val = st.slider(
        "💤 What if you slept X hours tonight?",
        min_value=4.0, max_value=10.0,
        value=float(inp.get("sleep_hours", 7.0)), step=0.5,
        key="sim_sleep",
    )
    steps_val = st.slider(
        "🚶 What if you walked X steps per day?",
        min_value=1000, max_value=15000,
        value=int(inp.get("steps_per_day", 7000)), step=500,
        key="sim_steps",
    )
    weight_val = st.slider(
        "⚖️ What if your weight was X kg?",
        min_value=40, max_value=150,
        value=int(inp.get("weight_kg", 70)), step=1,
        key="sim_weight",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # TODO: connect backend — replace stubs below
    r_sleep  = _stub_simulate("sleep_hours",   sleep_val,  bio_age)
    r_steps  = _stub_simulate("steps_per_day", steps_val,  bio_age)
    r_weight = _stub_simulate("weight_kg",     weight_val, bio_age)

    # Combine deltas (simple sum of improvements)
    total_delta = (r_sleep["new_bio_age"] - bio_age) + \
                  (r_steps["new_bio_age"] - bio_age) + \
                  (r_weight["new_bio_age"] - bio_age)
    new_bio_age = round(max(18, bio_age + total_delta), 1)
    years_gained = round(bio_age - new_bio_age, 1)
    total_life_credits = round(r_sleep["life_credits"] + r_steps["life_credits"] + r_weight["life_credits"], 2)

    st.session_state.sim_bio_age      = new_bio_age
    st.session_state.sim_years_gained = max(0, years_gained)
    st.session_state.total_life_credits = total_life_credits

    # Gauge — updated bio age
    fig = bio_age_gauge(new_bio_age, chrono_age)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Years gained hero
    if years_gained > 0:
        st.markdown(f"""
        <div class="years-gained-hero">
          <div class="years-number">+{years_gained:.1f}</div>
          <div class="years-label">years gained back</div>
          <div class="years-sub">= {round(years_gained * 12)} months of healthier life</div>
        </div>
        """, unsafe_allow_html=True)
        st.metric("Years gained", f"+{years_gained:.1f} yrs",
                  delta=f"Risk ↓ {abs(round(total_delta * 1.5, 1))}%")
    else:
        st.info("Move the sliders toward healthier values to see years gained.")

    # Projection chart
    st.markdown("<div style='margin-top:20px;font-size:13px;font-weight:600;color:#7A7AA0;margin-bottom:8px;'>Biological age projection to 2040</div>", unsafe_allow_html=True)
    years  = list(range(2025, 2041, 2))
    cur_traj  = [round(bio_age + i * 0.85, 1) for i in range(len(years))]
    new_traj  = [round(new_bio_age + i * 0.55, 1) for i in range(len(years))]
    chart_df = pd.DataFrame({
        "Current trajectory":  cur_traj,
        "With habit changes":  new_traj,
    }, index=years)
    st.line_chart(chart_df, color=["#AFA9EC", "#1D9E75"])

    col_back, col_fwd = st.columns([1, 2])
    with col_back:
        if st.button("← Back to Insights", use_container_width=True):
            st.session_state.screen = "dashboard"; st.rerun()
    with col_fwd:
        if st.button("🏆 Get my Coach plan →", type="primary", use_container_width=True):
            st.session_state.screen = "coach"; st.rerun()


# ─────────────────────────────────────────────
# SCREEN 6 — COACH
# ─────────────────────────────────────────────
def render_coach():
    bio_age      = st.session_state.bio_age
    chrono_age   = st.session_state.chrono_age
    years_gained = st.session_state.sim_years_gained
    recs         = st.session_state.recommendations
    inp          = st.session_state.inputs

    # Share card
    st.markdown(f"""
    <div class="share-card">
      <div class="share-number">+{years_gained:.1f}</div>
      <div class="share-label">years you can gain back 🎉</div>
      <div class="share-sub">Starting with one micro-habit below</div>
    </div>
    """, unsafe_allow_html=True)

    # Habits
    st.markdown("""
    <div class="g-card-title" style="font-size:24px;color:#fff;font-family:'DM Serif Display',serif;margin-bottom:4px;">Your top micro-habits</div>
    <div class="g-card-sub">Ranked by life impact. Each shows how many months of healthy life you gain — not just a percentage.</div>
    """, unsafe_allow_html=True)

    if "added_habits" not in st.session_state:
        st.session_state.added_habits = []

    for i, rec in enumerate(recs):
        added     = i in st.session_state.added_habits
        card_cls  = "habit-card added" if added else "habit-card"
        badge_cls = "credit-badge green" if added else "credit-badge"
        months    = rec.get("months_equiv", round(rec["life_credits"] * 3))

        st.markdown(f"""
        <div class="{card_cls}">
          <div class="habit-action">{'✓ ' if added else ''}{rec['habit']}</div>
          <div class="habit-impact">Impact: {rec['impact_pct']}% improvement · <strong>= {months} months of healthy life</strong></div>
          <div><span class="{badge_cls}">⚡ +{rec['life_credits']} life credits</span></div>
        </div>
        """, unsafe_allow_html=True)
        if not added:
            if st.button(f"＋ Add to my plan", key=f"add_{i}"):
                st.session_state.added_habits.append(i)
                st.rerun()

    # Streak tracker
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    added_list    = st.session_state.added_habits
    total_credits = sum(recs[i]["life_credits"] for i in added_list if i < len(recs))
    streak_days   = len(added_list) * 3

    st.markdown('<div class="g-card">', unsafe_allow_html=True)
    st.markdown('<div class="g-card-title">Your streak dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="g-card-sub">Habits committed. Each earns life credits toward your year total.</div>', unsafe_allow_html=True)

    col_streak, col_info = st.columns([1, 2])
    with col_streak:
        st.markdown(f"""
        <div style="text-align:center;padding:16px 0;">
          <div class="streak-num">{streak_days}</div>
          <div class="streak-label">day streak 🔥</div>
        </div>
        """, unsafe_allow_html=True)
    with col_info:
        if not added_list:
            st.info("Add a habit above to start your streak. Your body responds after just 3 days.")
        else:
            st.success(f"**{streak_days}-day streak!** You've earned **{total_credits:.1f} life credits** — that's **{round(total_credits * 3)} months** of healthy life.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Shareable summary card
    top2 = [recs[i]["habit"] for i in range(min(2, len(recs)))]
    habit_str = " · ".join(top2) if top2 else "—"
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.info(f"""
**📋 Your VitalMirror Summary**

🧬 Biological age: **{bio_age}** &nbsp;|&nbsp; Chronological age: **{chrono_age}**

🏆 Top habits: {habit_str}

⏳ Potential years gained: **+{years_gained:.1f} years**
""")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Back to Time Machine", use_container_width=True):
            st.session_state.screen = "simulation"; st.rerun()
    with col2:
        if st.button("↺ Try a new profile", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            init_state()
            st.rerun()
    with col3:
        share_text = f"VitalMirror says my bio age is {bio_age}. I can gain +{years_gained:.1f} years back! #VitalMirror #Hackmarch2025"
        st.code(share_text, language=None)


# ─────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────
screen = st.session_state.screen

if screen == "landing":
    render_landing()
elif screen == "input":
    render_input()
elif screen == "reveal":
    render_reveal()
elif screen == "dashboard":
    render_dashboard()
elif screen == "simulation":
    render_simulation()
elif screen == "coach":
    render_coach()
