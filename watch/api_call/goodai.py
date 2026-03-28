import io
import json
import logging
import math
import os
import re
import sys
import time
from datetime import datetime

import cv2
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import speech_recognition as sr
import streamlit as st
import google.generativeai as genai

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
        "voice_transcript": "",
        "voice_fills": {},
        "voice_suggestions": [],
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
        st.markdown("### 🔑 Gemini API Key")
        api_key = st.text_input("Enter your API key", type="password",
                     placeholder="AIza...", key="api_key_input",
                     label_visibility="collapsed")
        st.caption("Optional — powers Gemini analysis. Leave blank for demo mode.")
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
# VOICE HELPERS
# ─────────────────────────────────────────────
def _transcribe_audio(audio_bytes: bytes) -> str | None:
    """Transcribe audio bytes using speech_recognition; returns text or None on failure."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except Exception:
        return None


def _parse_voice_fields(text: str) -> dict:
    """Lightweight rule-based parser to extract fields from transcript."""
    t = text.lower()

    def _extract_number(segment: str):
        m = re.search(r"([0-9]+\.?[0-9]*)\s*(k|thousand)?", segment)
        if not m:
            return None
        val = float(m.group(1))
        if m.group(2):
            val *= 1000
        return val

    def _num_near(keyword: str):
        # Find number after the keyword
        m_after = re.search(rf"{keyword}[^0-9]*(.+)", t)
        if m_after:
            num = _extract_number(m_after.group(1))
            if num is not None:
                return num
        # Find number before the keyword (e.g., "10 thousand steps")
        m_before = re.search(rf"(.+){keyword}", t)
        if m_before:
            num = _extract_number(m_before.group(1))
            if num is not None:
                return num
        return None

    def _num_any(keywords: list[str]):
        for kw in keywords:
            num = _num_near(kw)
            if num is not None:
                return num
        return None

    sex = None
    if "female" in t: sex = "Female"
    elif "male" in t: sex = "Male"
    elif "other" in t or "non binary" in t: sex = "Other"

    def _match_quality(q_words, default):
        for word, label in q_words:
            if word in t:
                return label
        return default

    sleep_quality = _match_quality(
        [("terrible", "Poor"), ("poor", "Poor"), ("fair", "Fair"), ("okay", "Fair"),
         ("average", "Fair"), ("good", "Good"), ("great", "Excellent"), ("excellent", "Excellent")],
        None,
    )

    diet_quality = _match_quality(
        [("junk", "Poor"), ("unhealthy", "Poor"), ("average", "Fair"), ("okay", "Fair"),
         ("balanced", "Good"), ("healthy", "Good"), ("clean", "Excellent"), ("mediterranean", "Excellent")],
        None,
    )

    processed_food_freq = _match_quality(
        [("daily", "Often"), ("often", "Often"), ("frequent", "Often"),
         ("sometimes", "Sometimes"), ("occasionally", "Sometimes"), ("rarely", "Rarely"), ("seldom", "Rarely"), ("never", "Rarely")],
        None,
    )

    smoking_status = None
    if "never smoked" in t or "non smoker" in t or "nonsmoker" in t:
        smoking_status = "Never"
    elif "quit smoking" in t or "former smoker" in t or "ex smoker" in t:
        smoking_status = "Former"
    elif "smoke" in t or "smoker" in t:
        smoking_status = "Current"

    family_history = {
        "heart_disease_parent": "heart" in t and "no heart" not in t,
        "diabetes_parent": "diabetes" in t and "no diabetes" not in t,
        "cancer_parent": "cancer" in t and "no cancer" not in t,
        "parent_longevity_85plus": "lived past 85" in t or "over 85" in t,
    }

    bp_match = re.search(r"(\d{2,3})\s*(?:/|over)\s*(\d{2,3})", t)
    systolic_bp = float(bp_match.group(1)) if bp_match else None
    diastolic_bp = float(bp_match.group(2)) if bp_match else None

    return {
        "age": _num_near("age"),
        "sex": sex,
        "height_cm": _num_near("height"),
        "weight_kg": _num_near("weight") or _num_near("weigh"),
        "resting_hr": _num_near("resting") or _num_near("heart"),
        "sleep_hours": _num_any(["sleep", "slept", "sleeping", "bed"]),
        "sleep_quality": sleep_quality,
        "exercise_hours": _num_any(["exercise", "workout", "gym", "train", "training"]),
        "steps_per_day": _num_near("steps"),
        "sedentary_screen_time": _num_near("screen") or _num_near("sedentary") or _num_near("sitting"),
        "water_intake_liters": _num_near("water"),
        "diet_quality": diet_quality,
        "processed_food_freq": processed_food_freq,
        "alcohol_drinks_per_week": _num_near("alcohol") or _num_near("drinks") or _num_near("wine") or _num_near("beer"),
        "smoking_status": smoking_status,
        "stress_level": _num_near("stress"),
        "mental_health_score": _num_near("mental") or _num_near("mood"),
        "bmi": _num_near("bmi"),
        "systolic_bp": systolic_bp or _num_near("systolic") or _num_near("upper") or _num_near("blood pressure"),
        "diastolic_bp": diastolic_bp or _num_near("diastolic") or _num_near("lower") or _num_near("blood pressure"),
        "family_history": family_history,
    }


def _generate_static_suggestions(inputs: dict, family_history: dict) -> list[str]:
    """Deterministic suggestions based on provided values; not auto-updating."""
    recs = []
    sleep = inputs.get("sleep_hours")
    steps = inputs.get("steps_per_day")
    bmi = inputs.get("bmi")
    hr = inputs.get("resting_hr")

    if sleep is not None and sleep < 7:
        recs.append("Aim for 7–8h sleep; move bedtime 30 minutes earlier this week.")
    if steps is not None and steps < 8000:
        recs.append("Add one 10–15 minute walk after meals to push steps toward 8k.")
    if bmi is not None and bmi > 25:
        recs.append("Shift one sugary drink to water daily to start nudging BMI down.")
    if hr is not None and hr > 75:
        recs.append("Add 5 minutes of slow breathing in the evening to lower resting HR.")
    if family_history.get("heart_disease_parent"):
        recs.append("Check blood pressure weekly and log results; share with your clinician.")
    if not recs:
        recs.append("Maintain current habits; retest in 4 weeks to confirm trajectory.")
    return recs[:4]


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

    with st.expander("🎤 Fill this form by voice (beta)"):
        st.caption("Speak slowly: e.g., 'Age 32, female, height 165 centimeters, weight 70 kilograms, resting heart rate 72, sleep 6 hours, 5000 steps per day, no heart disease, no diabetes.'")
        audio_clip = st.audio_input("Record voice note", key="voice_audio")
        if st.button("Transcribe & fill", key="voice_btn"):
            if audio_clip is None:
                st.warning("Record a quick voice note first.")
            else:
                transcript = _transcribe_audio(audio_clip.getvalue())
                if not transcript:
                    st.error("Couldn't transcribe that audio. Try speaking closer to the mic.")
                else:
                    fills = _parse_voice_fields(transcript)
                    st.session_state.voice_transcript = transcript
                    st.session_state.voice_fills = fills
                    # Push parsed values into widget states so they show up immediately
                    if fills.get("age") is not None: st.session_state["inp_age"] = int(fills["age"])
                    if fills.get("weight_kg") is not None: st.session_state["inp_weight"] = float(fills["weight_kg"])
                    if fills.get("resting_hr") is not None: st.session_state["inp_hr"] = int(fills["resting_hr"])
                    if fills.get("sex") is not None: st.session_state["inp_sex"] = fills["sex"]
                    if fills.get("height_cm") is not None: st.session_state["inp_height"] = int(fills["height_cm"])
                    if fills.get("sleep_hours") is not None: st.session_state["inp_sleep"] = float(fills["sleep_hours"])
                    if fills.get("steps_per_day") is not None: st.session_state["inp_steps"] = int(round(fills["steps_per_day"]))
                    if fills.get("sleep_quality") is not None: st.session_state["inp_sleep_quality"] = fills["sleep_quality"]
                    if fills.get("exercise_hours") is not None: st.session_state["inp_exercise_hours"] = float(fills["exercise_hours"])
                    if fills.get("sedentary_screen_time") is not None: st.session_state["inp_sedentary"] = float(fills["sedentary_screen_time"])
                    if fills.get("water_intake_liters") is not None: st.session_state["inp_water"] = float(fills["water_intake_liters"])
                    if fills.get("diet_quality") is not None: st.session_state["inp_diet_quality"] = fills["diet_quality"]
                    if fills.get("processed_food_freq") is not None: st.session_state["inp_processed_food"] = fills["processed_food_freq"]
                    if fills.get("alcohol_drinks_per_week") is not None: st.session_state["inp_alcohol"] = float(fills["alcohol_drinks_per_week"])
                    if fills.get("smoking_status") is not None: st.session_state["inp_smoking"] = fills["smoking_status"]
                    if fills.get("stress_level") is not None: st.session_state["inp_stress"] = int(round(float(fills["stress_level"])))
                    if fills.get("mental_health_score") is not None: st.session_state["inp_mental"] = int(round(float(fills["mental_health_score"])))
                    if fills.get("bmi") is not None: st.session_state["inp_bmi"] = float(fills["bmi"])
                    if fills.get("systolic_bp") is not None: st.session_state["inp_sys_bp"] = int(round(float(fills["systolic_bp"])))
                    if fills.get("diastolic_bp") is not None: st.session_state["inp_dia_bp"] = int(round(float(fills["diastolic_bp"])))
                    fh = fills.get("family_history", {}) or {}
                    if "heart_disease_parent" in fh: st.session_state["fh_heart"] = bool(fh["heart_disease_parent"])
                    if "diabetes_parent" in fh: st.session_state["fh_diabetes"] = bool(fh["diabetes_parent"])
                    if "cancer_parent" in fh: st.session_state["fh_cancer"] = bool(fh["cancer_parent"])
                    if "parent_longevity_85plus" in fh: st.session_state["fh_longevity"] = bool(fh["parent_longevity_85plus"])
                    st.success("Transcribed and pre-filled fields. You can edit anything before submitting.")
                    st.caption(f"Transcript: {transcript}")
                    st.rerun()

    use_sample = st.session_state.get("_sample_loaded", False)
    d = RIYA_DATA if use_sample else {}
    voice_fills = st.session_state.get("voice_fills", {}) or {}
    merged_defaults = {**d, **{k: v for k, v in voice_fills.items() if k != "family_history" and v is not None}}
    merged_fh = d.get("family_history", {}).copy()
    merged_fh.update({k: v for k, v in (voice_fills.get("family_history") or {}).items() if v is not None})
    if merged_fh:
        merged_defaults["family_history"] = merged_fh

    # Ensure numeric defaults are the correct types for sliders/inputs
    def _safe_int(val, default):
        try:
            return int(round(float(val)))
        except Exception:
            return default

    def _safe_float(val, default):
        try:
            return float(val)
        except Exception:
            return default

    def _calc_bmi(height_cm_val, weight_kg_val):
        try:
            if not height_cm_val:
                return 0.0
            return round(weight_kg_val / ((height_cm_val / 100) ** 2), 1)
        except Exception:
            return 0.0

    merged_defaults["age"] = _safe_int(merged_defaults.get("age"), 30)
    merged_defaults["weight_kg"] = _safe_int(merged_defaults.get("weight_kg"), 70)
    merged_defaults["resting_hr"] = _safe_int(merged_defaults.get("resting_hr"), 72)
    merged_defaults["height_cm"] = _safe_int(merged_defaults.get("height_cm"), 170)
    merged_defaults["sleep_hours"] = _safe_float(merged_defaults.get("sleep_hours"), 7.0)
    merged_defaults["steps_per_day"] = _safe_int(merged_defaults.get("steps_per_day"), 7000)
    merged_defaults["sleep_quality"] = merged_defaults.get("sleep_quality", "Good")
    merged_defaults["exercise_hours"] = _safe_float(merged_defaults.get("exercise_hours"), 3.0)
    merged_defaults["sedentary_screen_time"] = _safe_float(merged_defaults.get("sedentary_screen_time"), 6.0)
    merged_defaults["water_intake_liters"] = _safe_float(merged_defaults.get("water_intake_liters"), 2.5)
    merged_defaults["diet_quality"] = merged_defaults.get("diet_quality", "Good")
    merged_defaults["processed_food_freq"] = merged_defaults.get("processed_food_freq", "Sometimes")
    merged_defaults["alcohol_drinks_per_week"] = _safe_float(merged_defaults.get("alcohol_drinks_per_week"), 2.0)
    merged_defaults["smoking_status"] = merged_defaults.get("smoking_status", "Never")
    merged_defaults["stress_level"] = _safe_int(merged_defaults.get("stress_level"), 4)
    merged_defaults["mental_health_score"] = _safe_int(merged_defaults.get("mental_health_score"), 75)
    merged_defaults["systolic_bp"] = _safe_int(merged_defaults.get("systolic_bp"), 120)
    merged_defaults["diastolic_bp"] = _safe_int(merged_defaults.get("diastolic_bp"), 80)

    with st.container():
        st.markdown('<div class="g-card">', unsafe_allow_html=True)
        st.markdown("#### 👤 Basic info")
        col1, col2 = st.columns(2)
        with col1:
            age_val = merged_defaults.get("age", 30)
            age = st.number_input("Chronological age (years)", min_value=18, max_value=90,
                                  value=int(round(age_val)) if age_val is not None else 30, step=1, key="inp_age")
            wt_val = merged_defaults.get("weight_kg", 70)
            weight_kg = st.number_input("Weight (kg)", min_value=35, max_value=220,
                                         value=int(round(wt_val)) if wt_val is not None else 70, step=1, key="inp_weight")
            hr_val = merged_defaults.get("resting_hr", 72)
            resting_hr = st.number_input("Resting heart rate (bpm)", min_value=40, max_value=120,
                                          value=int(round(hr_val)) if hr_val is not None else 72, step=1, key="inp_hr")
        with col2:
            sex_options = ["Male", "Female", "Other"]
            default_sex = merged_defaults.get("sex", "Male")
            try:
                sex_index = sex_options.index(default_sex)
            except ValueError:
                sex_index = 0
            sex = st.selectbox("Biological sex", sex_options,
                               index=sex_index, key="inp_sex")
            h_val = merged_defaults.get("height_cm", 170)
            height_cm = st.number_input("Height (cm)", min_value=140, max_value=220,
                                         value=int(round(h_val)) if h_val is not None else 170, step=1, key="inp_height")

        st.markdown("#### 🏃 Activity & Sleep")
        sleep_val = merged_defaults.get("sleep_hours", 7.0)
        sleep_hours = st.slider("Average sleep per night (hours)",
                     min_value=3.0, max_value=12.0,
                     value=float(sleep_val) if sleep_val is not None else 7.0,
                                         step=0.5, key="inp_sleep")
        sleep_quality = st.selectbox("Sleep quality", ["Poor", "Fair", "Good", "Excellent"],
                                                                         index=["Poor","Fair","Good","Excellent"].index(merged_defaults.get("sleep_quality","Good")),
                                                                         key="inp_sleep_quality")
        exercise_hours = st.slider("Exercise hours per week",
                                   min_value=0.0, max_value=20.0,
                                                                     value=float(merged_defaults.get("exercise_hours", 3.0)), step=0.5,
                                                                     key="inp_exercise_hours")
        steps_val = merged_defaults.get("steps_per_day", 7000)
        steps_per_day = st.slider("Daily steps",
                       min_value=1000, max_value=25000,
                       value=int(round(steps_val)) if steps_val is not None else 7000,
                       step=500, key="inp_steps")
        sedentary_screen_time = st.slider("Sedentary / screen time (hrs/day)",
                                          min_value=0.0, max_value=16.0,
                                                                                    value=float(merged_defaults.get("sedentary_screen_time", 6.0)), step=0.5,
                                                                                    key="inp_sedentary")

        st.markdown("#### 🍎 Diet & Consumption")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            water_intake_liters = st.slider("Water intake (liters/day)",
                                            min_value=0.5, max_value=6.0,
                                            value=float(merged_defaults.get("water_intake_liters", 2.5)), step=0.1,
                                            key="inp_water")
            diet_quality = st.selectbox("Diet quality", ["Poor", "Fair", "Good", "Excellent"],
                                        index=["Poor","Fair","Good","Excellent"].index(merged_defaults.get("diet_quality","Good")),
                                        key="inp_diet_quality")
            processed_food_freq = st.selectbox("Processed foods", ["Rarely", "Sometimes", "Often"],
                                               index=["Rarely","Sometimes","Often"].index(merged_defaults.get("processed_food_freq","Sometimes")),
                                               key="inp_processed_food")
        with col_d2:
            alcohol_drinks_per_week = st.slider("Alcohol (drinks/week)", min_value=0.0, max_value=40.0,
                                                value=float(merged_defaults.get("alcohol_drinks_per_week", 2.0)), step=1.0,
                                                key="inp_alcohol")
            smoking_status = st.selectbox("Smoking status", ["Never", "Former", "Current"],
                                          index=["Never","Former","Current"].index(merged_defaults.get("smoking_status","Never")),
                                          key="inp_smoking")

        st.markdown("#### 🧠 Mental wellbeing")
        stress_level = st.slider("Stress level (1-10)", min_value=1, max_value=10,
                         value=int(merged_defaults.get("stress_level", 4)), step=1,
                         key="inp_stress")
        mental_health_score = st.slider("Mental health score (10-100)", min_value=10, max_value=100,
                             value=int(merged_defaults.get("mental_health_score", 75)), step=1,
                             key="inp_mental")

        st.markdown("#### 👨‍👩‍👧 Family history")
        fh_defaults = merged_defaults.get("family_history", {})
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

    st.markdown("#### ❤️ Clinical vitals")
    bmi = _calc_bmi(height_cm, weight_kg)
    st.markdown(f"**BMI (auto):** {bmi}")
    col_bp = st.columns(2)
    with col_bp[0]:
        systolic_bp = st.number_input("Systolic BP", min_value=80, max_value=220,
                                      value=int(merged_defaults.get("systolic_bp", 120)), step=1,
                                      key="inp_sys_bp")
    with col_bp[1]:
        diastolic_bp = st.number_input("Diastolic BP", min_value=50, max_value=140,
                                       value=int(merged_defaults.get("diastolic_bp", 80)), step=1,
                                       key="inp_dia_bp")

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    col_sug_btn, col_sug_list = st.columns([1, 2])
    with col_sug_btn:
        if st.button("Generate static suggestions", use_container_width=True):
            snapshot_inputs = {
                "age": age,
                "weight_kg": weight_kg,
                "height_cm": height_cm,
                "resting_hr": resting_hr,
                "sleep_hours": sleep_hours,
                "steps_per_day": steps_per_day,
                "sleep_quality": sleep_quality,
                "exercise_hours": exercise_hours,
                "sedentary_screen_time": sedentary_screen_time,
                "water_intake_liters": water_intake_liters,
                "diet_quality": diet_quality,
                "processed_food_freq": processed_food_freq,
                "alcohol_drinks_per_week": alcohol_drinks_per_week,
                "smoking_status": smoking_status,
                "stress_level": stress_level,
                "mental_health_score": mental_health_score,
                "systolic_bp": systolic_bp,
                "diastolic_bp": diastolic_bp,
            }
            snapshot_inputs["bmi"] = _calc_bmi(height_cm, weight_kg)
            family_history = {
                "heart_disease_parent": fh_heart,
                "diabetes_parent": fh_diabetes,
                "cancer_parent": fh_cancer,
                "parent_longevity_85plus": fh_longevity,
            }
            st.session_state.voice_suggestions = _generate_static_suggestions(snapshot_inputs, family_history)
    with col_sug_list:
        if st.session_state.voice_suggestions:
            st.info("Static suggestions (won't auto-change unless you click Generate again):\n- " + "\n- ".join(st.session_state.voice_suggestions))

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    col_back, col_fwd = st.columns([1, 2])
    with col_back:
        if st.button("← Home", use_container_width=True):
            st.session_state.screen = "landing"; st.rerun()
    with col_fwd:
        if st.button("🧬 Analyse my signals →", type="primary", use_container_width=True):
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
                "sleep_quality": sleep_quality,
                "exercise_hours": exercise_hours,
                "sedentary_screen_time": sedentary_screen_time,
                "water_intake_liters": water_intake_liters,
                "diet_quality": diet_quality,
                "processed_food_freq": processed_food_freq,
                "alcohol_drinks_per_week": alcohol_drinks_per_week,
                "smoking_status": smoking_status,
                "stress_level": stress_level,
                "mental_health_score": mental_health_score,
                "systolic_bp": systolic_bp,
                "diastolic_bp": diastolic_bp,
            }
            with st.spinner("🔬 Analysing your signals…"):
                api_data = None
                api_raw_body = None
                api_url = "https://parthiv04.app.n8n.cloud/webhook-test/bioage"
                headers = {"Content-Type": "application/json"}
                api_key = st.session_state.get("api_key_input")
                voice_transcript = st.session_state.get("voice_transcript", "")
                photo_uploaded = photo_file is not None
                wearable_csv_name = wearable_csv.name if wearable_csv is not None else None
                prompt_text = (
                    "You are a biological age analysis assistant for the GoodAI health platform.\n"
                    "YOUR ONLY JOB:\n"
                    "Explain in exactly 3 sentences why the user's estimated biological age is higher or lower than their chronological age, based solely on the data provided.\n"
                    "STRICT RULES — follow all of these without exception:\n"
                    "1. Write EXACTLY 3 sentences. No more, no less.\n"
                    "2. Only reference values that are present in the input data. Do not invent or assume any values.\n"
                    "3. Do not give medical advice, diagnoses, or treatment recommendations.\n"
                    "4. Do not suggest the user see a doctor or any health professional.\n"
                    "5. Do not ask the user any questions.\n"
                    "6. Do not add disclaimers, caveats, or warnings.\n"
                    "7. Do not say things like \"I am an AI\" or \"consult a professional\".\n"
                    "8. Do not explain what biological age is — just explain the difference.\n"
                    "9. Cite at least 2 specific data values (numbers) from the input in your response.\n"
                    "10. End your response after the 3rd sentence. Nothing else.\n"
                    "OUTPUT FORMAT:\n"
                    "Return only the 3 sentences. No intro, no sign-off, no bullet points."
                )
                payload = {
                    "prompt": prompt_text,
                    "inputs": inputs,
                    "family_history": family_history,
                    "csv_uploaded": wearable_csv is not None,
                    "wearable_csv_name": wearable_csv_name,
                    "photo_uploaded": photo_uploaded,
                    "voice_transcript": voice_transcript,
                }
                if api_key:
                    headers["x-api-key"] = api_key
                    payload["api_key"] = api_key

                try:
                    resp = requests.post(api_url, json=payload, headers=headers, timeout=20)
                    resp.raise_for_status()
                    api_raw_body = resp.text if resp.content else ""
                    try:
                        api_data = resp.json() if resp.content else {}
                    except Exception:
                        api_data = None
                    st.session_state.api_http_status = resp.status_code
                    st.session_state.api_raw_body = api_raw_body
                except Exception as e:
                    logging.warning(f"API call failed: {e}")
                    st.warning("API call failed — showing local estimate instead.")
                    st.session_state.api_http_status = None
                    st.session_state.api_raw_body = None

                csv_path = None
                if wearable_csv is not None:
                    csv_path = wearable_csv  # pass file object; backend accepts path or object

                api_response_bundle = {
                    "http_status": st.session_state.get("api_http_status"),
                    "raw_body": api_raw_body,
                    "parsed": api_data,
                }

                if api_data and api_data.get("bio_age") is not None:
                    cosinor_result = {
                        "bio_age": api_data.get("bio_age"),
                        "confidence": api_data.get("confidence", 0.75),
                        "top_features": api_data.get("top_features", []),
                    }
                    fused_bio_age = api_data.get("bio_age")
                    risk_result = api_data.get("risk_result") or _stub_predict_risk(fused_bio_age, age, family_history)
                    recs = api_data.get("recommendations") or _stub_recommendations(
                        cosinor_result["top_features"], family_history, fused_bio_age)
                    st.session_state.api_raw_response = api_response_bundle
                else:
                    # Fallback to local stubs but still surface what the API returned
                    cosinor_result = _stub_cosinor(inputs, csv_path=csv_path)
                    fused_bio_age  = _stub_fuse([cosinor_result])
                    risk_result    = _stub_predict_risk(fused_bio_age, age, family_history)
                    recs           = _stub_recommendations(cosinor_result["top_features"],
                                                           family_history, fused_bio_age)
                    st.session_state.api_raw_response = api_response_bundle

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
    api_raw    = st.session_state.get("api_raw_response")

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

    if api_raw:
        with st.expander("📡 API response", expanded=False):
            st.json(api_raw)
            st.download_button(
                label="Download API response JSON",
                data=json.dumps(api_raw, indent=2),
                file_name="bioage_api_response.json",
                mime="application/json",
            )

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
        value=int(round(inp.get("steps_per_day", 7000))), step=500,
        key="sim_steps",
    )
    weight_val = st.slider(
        "⚖️ What if your weight was X kg?",
        min_value=40, max_value=150,
        value=int(round(inp.get("weight_kg", 70))), step=1,
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
