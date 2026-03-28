import streamlit as st
import anthropic
import json
import math
import time

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="GoodAI — AI for Longevity",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}
.main { background: #F7F6F2; }
.block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 900px; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Logo / Header ── */
.goodai-header {
    display: flex; align-items: center; gap: 12px;
    padding: 0 0 2rem; border-bottom: 1px solid rgba(75,63,187,0.12);
    margin-bottom: 2rem;
}
.goodai-logo-ring {
    width: 38px; height: 38px; border-radius: 50%;
    border: 2.5px solid #4B3FBB;
    display: flex; align-items: center; justify-content: center;
}
.goodai-logo-dot {
    width: 11px; height: 11px; background: #4B3FBB; border-radius: 50%;
}
.goodai-logo-text {
    font-family: 'DM Serif Display', serif;
    font-size: 24px; color: #4B3FBB; letter-spacing: -0.5px;
}
.goodai-badge {
    margin-left: auto;
    font-size: 12px; font-weight: 500;
    color: #4B3FBB; background: #EEEDFE;
    border: 1px solid rgba(75,63,187,0.25);
    padding: 5px 16px; border-radius: 99px;
}

/* ── Hero ── */
.hero-eyebrow {
    font-size: 11px; font-weight: 600; letter-spacing: 2.5px;
    text-transform: uppercase; color: #4B3FBB;
    display: flex; align-items: center; gap: 8px; margin-bottom: 12px;
}
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 52px; line-height: 1.05; letter-spacing: -2px;
    color: #1a1a2e; margin-bottom: 14px;
}
.hero-title em { font-style: italic; color: #4B3FBB; }
.hero-sub {
    font-size: 17px; font-weight: 300; color: #6B6A75;
    line-height: 1.7; max-width: 560px; margin-bottom: 2rem;
}

/* ── Cards ── */
.g-card {
    background: #FFFFFF;
    border: 1px solid rgba(75,63,187,0.12);
    border-radius: 16px; padding: 28px 32px;
    box-shadow: 0 2px 20px rgba(75,63,187,0.08);
    margin-bottom: 20px;
}
.g-card-title {
    font-family: 'DM Serif Display', serif;
    font-size: 24px; letter-spacing: -0.5px; color: #1a1a2e; margin-bottom: 6px;
}
.g-card-sub { font-size: 14px; color: #6B6A75; font-weight: 300; line-height: 1.6; margin-bottom: 22px; }

/* ── Metric row ── */
.metric-row { display: flex; gap: 14px; flex-wrap: wrap; margin: 20px 0; }
.metric-box {
    flex: 1; min-width: 120px;
    background: #F7F6F2;
    border: 1px solid rgba(75,63,187,0.12);
    border-radius: 12px; padding: 16px 18px;
}
.metric-box-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #A0A0B0; margin-bottom: 6px; }
.metric-box-val { font-size: 22px; font-weight: 600; color: #1a1a2e; }
.metric-box-sub { font-size: 12px; color: #6B6A75; margin-top: 2px; }
.metric-box.good .metric-box-val { color: #1D9E75; }
.metric-box.warn .metric-box-val { color: #BA7517; }
.metric-box.bad  .metric-box-val { color: #D85A30; }

/* ── Bio age ring ── */
.bio-ring-wrap { text-align: center; padding: 20px 0; }
.bio-age-big {
    font-family: 'DM Serif Display', serif;
    font-size: 96px; line-height: 1; color: #4B3FBB;
}
.bio-age-big.older { color: #D85A30; }
.bio-age-big.younger { color: #1D9E75; }
.bio-reveal-label { font-size: 14px; color: #6B6A75; letter-spacing: 1px; text-transform: uppercase; }
.bio-reveal-text {
    font-family: 'DM Serif Display', serif;
    font-size: 22px; color: #1a1a2e; margin: 16px 0 6px;
}
.bio-reveal-sub { font-size: 14px; color: #6B6A75; line-height: 1.6; }

/* ── Risk banner ── */
.risk-banner {
    display: flex; align-items: flex-start; gap: 14px;
    padding: 18px 20px; border-radius: 12px; margin: 18px 0;
    border: 1px solid;
}
.risk-banner.high { background: #FAECE7; border-color: rgba(216,90,48,0.3); }
.risk-banner.medium { background: #FAEEDA; border-color: rgba(186,117,23,0.3); }
.risk-banner.low { background: #E1F5EE; border-color: rgba(29,158,117,0.3); }
.risk-banner-text { font-size: 14px; color: #1a1a2e; line-height: 1.6; }

/* ── Years gained ── */
.years-gained-hero {
    background: linear-gradient(135deg, #EEEDFE 0%, #E1F5EE 100%);
    border: 1px solid rgba(75,63,187,0.15);
    border-radius: 16px; padding: 32px 24px; text-align: center; margin: 18px 0;
}
.years-number {
    font-family: 'DM Serif Display', serif;
    font-size: 80px; line-height: 1; color: #4B3FBB;
}
.years-label { font-size: 16px; font-weight: 500; color: #6B6A75; margin-top: 8px; }
.years-sub { font-size: 13px; color: #A0A0B0; margin-top: 4px; }

/* ── Habit cards ── */
.habit-card {
    background: #FFFFFF;
    border: 1.5px solid rgba(75,63,187,0.15);
    border-left: 5px solid #4B3FBB;
    border-radius: 14px; padding: 20px 22px; margin-bottom: 14px;
}
.habit-card.added {
    border-color: rgba(29,158,117,0.3);
    border-left-color: #1D9E75;
    background: #F0FBF7;
}
.habit-action { font-size: 16px; font-weight: 600; color: #1a1a2e; margin-bottom: 8px; }
.habit-impact { font-size: 13px; color: #6B6A75; line-height: 1.5; margin-bottom: 12px; }
.credit-badge {
    display: inline-block;
    font-size: 12px; font-weight: 600; color: #4B3FBB;
    background: #EEEDFE; padding: 4px 12px; border-radius: 99px;
}
.credit-badge.green { color: #1D9E75; background: #E1F5EE; }

/* ── Streak ── */
.streak-num {
    font-family: 'DM Serif Display', serif;
    font-size: 64px; color: #1D9E75; text-align: center;
}
.streak-label { font-size: 13px; color: #6B6A75; text-align: center; text-transform: uppercase; letter-spacing: 1px; }

/* ── Share card ── */
.share-card {
    background: linear-gradient(135deg, #4B3FBB 0%, #6C5CE7 50%, #0F6E56 100%);
    border-radius: 16px; padding: 36px 28px; text-align: center;
    color: white; margin: 20px 0;
}
.share-number { font-family: 'DM Serif Display', serif; font-size: 72px; line-height: 1; }
.share-label { font-size: 18px; opacity: 0.9; margin-top: 8px; }
.share-sub { font-size: 13px; opacity: 0.7; margin-top: 6px; }

/* ── Step indicator ── */
.step-indicator {
    display: flex; align-items: center; justify-content: center;
    gap: 0; margin: 0 0 2rem;
}
.step-dot {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 600;
    border: 2px solid rgba(75,63,187,0.3);
    color: #A0A0B0; background: white;
}
.step-dot.active { background: #4B3FBB; border-color: #4B3FBB; color: white; }
.step-dot.done { background: #E1F5EE; border-color: #1D9E75; color: #1D9E75; }
.step-line { width: 64px; height: 2px; background: rgba(75,63,187,0.2); }
.step-line.done { background: #1D9E75; }

/* ── Sample bar ── */
.sample-bar {
    background: #EEEDFE;
    border: 1px dashed rgba(75,63,187,0.4);
    border-radius: 12px; padding: 14px 20px;
    cursor: pointer; margin-bottom: 20px;
    display: flex; align-items: center; justify-content: space-between;
}
.sample-bar-text { font-size: 14px; font-weight: 500; color: #4B3FBB; }
.sample-bar-sub { font-size: 12px; color: #6B6A75; margin-top: 2px; }

/* ── Progress bar ── */
.prog-bar-wrap { display: flex; align-items: center; gap: 14px; margin: 12px 0; }
.prog-label { font-size: 13px; color: #6B6A75; min-width: 90px; }
.prog-track { flex: 1; height: 8px; background: rgba(75,63,187,0.12); border-radius: 4px; overflow: hidden; }
.prog-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #1D9E75, #0F6E56); transition: width 0.8s; }
.prog-val { font-size: 14px; font-weight: 600; color: #1D9E75; min-width: 44px; text-align: right; }

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; border-radius: 99px !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: #4B3FBB !important; border: none !important;
    box-shadow: 0 4px 20px rgba(75,63,187,0.35) !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: #6C5CE7 !important;
    box-shadow: 0 6px 28px rgba(75,63,187,0.45) !important;
}

/* ── Section divider ── */
.section-divider { height: 1px; background: rgba(75,63,187,0.1); margin: 24px 0; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "step": 1,
        "inputs": {},
        "bio_age": None,
        "chrono_age": None,
        "worst_metric": "sleep",
        "api_result": None,
        "added_habits": [],
        "sim_val": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────
# LAYER 1 — BIOLOGICAL AGE FORMULA
# ─────────────────────────────────────────────
def calc_bmi(weight_kg: float, height_cm: float) -> float:
    h = height_cm / 100
    return round(weight_kg / (h * h), 1)


def calc_bio_age(inp: dict) -> int:
    age         = inp["age"]
    bmi         = inp["bmi"]
    sleep_h     = inp["sleep_hours"]
    systolic    = inp["systolic"]
    resting_hr  = inp["resting_hr"]
    activity    = inp["activity_mins"]
    smoking     = inp["smoking"]
    stress      = inp["stress"]

    penalty = 0.0

    # BMI (optimal 21-23)
    if bmi > 25:  penalty += (bmi - 25) * 0.35
    if bmi > 30:  penalty += (bmi - 30) * 0.60
    if bmi < 18.5: penalty += (18.5 - bmi) * 0.40

    # Sleep (optimal 7-9 h)
    if sleep_h < 7:   penalty += (7 - sleep_h) * 1.8
    if sleep_h < 5:   penalty += (5 - sleep_h) * 2.5
    if sleep_h > 9.5: penalty += (sleep_h - 9.5) * 0.8

    # Blood pressure (optimal < 120)
    if systolic > 120: penalty += (systolic - 120) * 0.09
    if systolic > 140: penalty += (systolic - 140) * 0.15

    # Resting HR (optimal < 65)
    if resting_hr > 65: penalty += (resting_hr - 65) * 0.06
    if resting_hr > 80: penalty += (resting_hr - 80) * 0.10

    # Activity bonus (WHO baseline = 150 min/week)
    activity_bonus = min((activity / 150) * 2.5, 5.0)

    # Smoking
    if smoking == "Current smoker": penalty += 7
    elif smoking == "Ex-smoker":    penalty += 3

    # Stress
    if stress > 6: penalty += (stress - 6) * 0.5

    return round(age + penalty - activity_bonus)


def detect_worst_metric(inp: dict) -> str:
    scores = {
        "sleep":    3 if inp["sleep_hours"] < 6 else (2 if inp["sleep_hours"] < 7 else 0),
        "activity": 3 if inp["activity_mins"] < 30 else (2 if inp["activity_mins"] < 100 else 0),
        "bp":       3 if inp["systolic"] > 140 else (2 if inp["systolic"] > 130 else 0),
        "bmi":      3 if inp["bmi"] > 30 else (2 if inp["bmi"] > 27 else 0),
        "hr":       2 if inp["resting_hr"] > 80 else 0,
        "stress":   2 if inp["stress"] > 7 else 0,
    }
    return max(scores, key=scores.get)


# ─────────────────────────────────────────────
# SIMULATION CONFIG
# ─────────────────────────────────────────────
SIM_CONFIG = {
    "sleep":    {"label": "Sleep hours / night",       "unit": "h",    "min": 5.0, "max": 9.0,  "step": 0.5, "optimal": 8.0},
    "activity": {"label": "Exercise minutes / week",   "unit": " min", "min": 0,   "max": 300,  "step": 10,  "optimal": 200},
    "bp":       {"label": "Systolic BP (mmHg)",        "unit": "",     "min": 115, "max": 155,  "step": 1,   "optimal": 120},
    "bmi":      {"label": "BMI",                       "unit": "",     "min": 20,  "max": 35,   "step": 0.5, "optimal": 22},
    "hr":       {"label": "Resting heart rate (bpm)",  "unit": " bpm", "min": 50,  "max": 90,   "step": 1,   "optimal": 58},
    "stress":   {"label": "Stress level (1-10)",       "unit": "/10",  "min": 1,   "max": 10,   "step": 1,   "optimal": 3},
}

def sim_formula(metric: str, val: float) -> dict:
    formulas = {
        "sleep":    lambda v: {"years": round(((v-5)/4)*3.0, 1), "risk": round(((v-5)/4)*12)},
        "activity": lambda v: {"years": round((v/300)*2.5, 1),  "risk": round((v/300)*15)},
        "bp":       lambda v: {"years": round(((155-v)/40)*2.0, 1), "risk": round(((155-v)/40)*10)},
        "bmi":      lambda v: {"years": round(((35-v)/15)*1.8, 1),  "risk": round(((35-v)/15)*8)},
        "hr":       lambda v: {"years": round(((90-v)/40)*1.5, 1),  "risk": round(((90-v)/40)*7)},
        "stress":   lambda v: {"years": round(((10-v)/9)*1.2, 1),   "risk": round(((10-v)/9)*6)},
    }
    r = formulas[metric](val)
    return {"years": max(0, r["years"]), "risk": max(0, r["risk"])}


def get_current_metric_val(metric: str, inp: dict) -> float:
    mapping = {
        "sleep": inp["sleep_hours"], "activity": inp["activity_mins"],
        "bp": inp["systolic"], "bmi": inp["bmi"],
        "hr": inp["resting_hr"], "stress": inp["stress"],
    }
    return mapping[metric]


# ─────────────────────────────────────────────
# LAYER 2 — CLAUDE API
# ─────────────────────────────────────────────
def call_claude_api(inp: dict, bio_age: int) -> dict:
    diff = bio_age - inp["age"]
    system_prompt = (
        "You are a longevity health AI analyst. Given health metrics and a biological age estimate, "
        "return ONLY a valid JSON object — no markdown, no preamble, no explanation. "
        "The JSON must exactly match this schema:\n"
        '{\n'
        '  "riskSummary": "2 clear sentences describing main health risks motivatingly",\n'
        '  "riskLevel": "high|medium|low",\n'
        '  "topRisk": "cardiovascular|metabolic|cognitive|musculoskeletal",\n'
        '  "heartRiskPercent": <integer 5-35>,\n'
        '  "yearsGainedMax": <number 1.0-4.0 with 1 decimal>,\n'
        '  "microHabits": [\n'
        '    { "action": "Specific habit", "impact": "Clear benefit with a number", "lifeCredits": <0.5-3.0> },\n'
        '    { "action": "...", "impact": "...", "lifeCredits": <number> },\n'
        '    { "action": "...", "impact": "...", "lifeCredits": <number> }\n'
        '  ]\n'
        '}\n'
        "microHabits must be ranked by lifeCredits descending. Each targets a different health aspect."
    )
    user_prompt = (
        f"Chronological age: {inp['age']}\n"
        f"Biological age: {bio_age} (diff: {diff:+d} years)\n"
        f"BMI: {inp['bmi']}\n"
        f"Sleep: {inp['sleep_hours']}h/night\n"
        f"Resting HR: {inp['resting_hr']} bpm\n"
        f"Systolic BP: {inp['systolic']} mmHg\n"
        f"Weekly activity: {inp['activity_mins']} min\n"
        f"Stress: {inp['stress']}/10\n"
        f"Smoking: {inp['smoking']}\n"
        f"Worst metric: {detect_worst_metric(inp)}\n\n"
        "Generate the health analysis JSON."
    )

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = message.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def get_fallback_result(inp: dict, bio_age: int) -> dict:
    diff = bio_age - inp["age"]
    direction = f"{diff} years older" if diff > 0 else f"{abs(diff)} years younger"
    culprit = "insufficient sleep" if inp["sleep_hours"] < 6.5 else "low physical activity"
    return {
        "riskSummary": (
            f"Your biological age is {direction} than your chronological age, "
            f"primarily driven by {culprit} and elevated stress. "
            "With targeted habit changes you can meaningfully reduce your 10-year cardiovascular risk."
        ),
        "riskLevel": "high" if diff > 5 else "medium" if diff > 2 else "low",
        "topRisk": "cardiovascular",
        "heartRiskPercent": min(35, max(8, round(12 + diff * 1.2))),
        "yearsGainedMax": round(min(4.0, max(1.2, diff * 0.4 + 1.0)), 1),
        "microHabits": [
            {"action": "Sleep 30 minutes earlier each night",
             "impact": "Reduces cortisol and inflammatory markers, lowering 10-year heart risk by ~4%. Adds 1.2 life credits.",
             "lifeCredits": 1.2},
            {"action": "Add a 15-minute brisk walk after lunch",
             "impact": "Improves insulin sensitivity and cardiovascular fitness. Targets activity deficit and adds 1.0 life credit.",
             "lifeCredits": 1.0},
            {"action": "Replace one sugary drink with water daily",
             "impact": "Reduces visceral fat accumulation. Adds 0.7 life credits within 30 days.",
             "lifeCredits": 0.7},
        ],
    }


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="goodai-header">
  <div class="goodai-logo-ring"><div class="goodai-logo-dot"></div></div>
  <div class="goodai-logo-text">GoodAI</div>
  <div class="goodai-badge">AI for Longevity · Hackathon Demo</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STEP INDICATOR
# ─────────────────────────────────────────────
def render_steps(current: int):
    dots = []
    for i in range(1, 5):
        if i < current:
            cls = "done"; label = "✓"
        elif i == current:
            cls = "active"; label = str(i)
        else:
            cls = ""; label = str(i)
        dots.append(f'<div class="step-dot {cls}">{label}</div>')
        if i < 4:
            line_cls = "done" if i < current else ""
            dots.append(f'<div class="step-line {line_cls}"></div>')
    st.markdown(f'<div class="step-indicator">{"".join(dots)}</div>', unsafe_allow_html=True)

step_labels = {1: "Data Input", 2: "Bio Age Reveal", 3: "Time Machine", 4: "Action Plan"}
render_steps(st.session_state.step)


# ═══════════════════════════════════════════════
# SCREEN 1 — DATA INPUT
# ═══════════════════════════════════════════════
if st.session_state.step == 1:
    st.markdown("""
    <div>
      <div class="hero-eyebrow"><span>──</span> Predict · Simulate · Act <span>──</span></div>
      <div class="hero-title">See the age your<br><em>body truly feels.</em></div>
      <div class="hero-sub">Enter your health data and watch your biological age reveal itself — then change one habit and see the years you gain back.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="g-card">', unsafe_allow_html=True)
    st.markdown('<div class="g-card-title">Your health data</div>', unsafe_allow_html=True)
    st.markdown('<div class="g-card-sub">Enter your current metrics below. All fields help improve accuracy, but only age, weight, and height are required.</div>', unsafe_allow_html=True)

    # Sample data loader
    st.markdown("""
    <div class="sample-bar">
      <div>
        <div class="sample-bar-text">📊 Load sample profile — Riya, 32</div>
        <div class="sample-bar-sub">Sedentary job · poor sleep · no regular exercise</div>
      </div>
      <div style="color:#4B3FBB;font-weight:600;font-size:13px;">↓</div>
    </div>
    """, unsafe_allow_html=True)

    load_sample = st.button("Load Riya's sample profile →", use_container_width=False)
    if load_sample:
        st.session_state["_sample"] = True

    use_sample = st.session_state.get("_sample", False)

    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age (years)", min_value=18, max_value=90, value=32 if use_sample else 30, step=1)
        weight = st.number_input("Weight (kg)", min_value=40, max_value=200, value=70 if use_sample else 70, step=1)
        resting_hr = st.number_input("Resting heart rate (bpm)", min_value=40, max_value=120, value=78 if use_sample else 72, step=1)
        stress = st.slider("Stress level (1–10)", 1, 10, value=7 if use_sample else 5)
    with col2:
        sex = st.selectbox("Biological sex", ["Female", "Male", "Other / prefer not to say"], index=0)
        height = st.number_input("Height (cm)", min_value=140, max_value=220, value=165 if use_sample else 170, step=1)
        systolic = st.number_input("Systolic blood pressure (mmHg)", min_value=80, max_value=200, value=128 if use_sample else 120, step=1)
        smoking = st.selectbox("Smoking history", ["Never smoked", "Ex-smoker", "Current smoker"], index=0)

    sleep_h = st.slider("Sleep hours per night", 3.0, 12.0, value=5.5 if use_sample else 7.0, step=0.5)
    activity = st.slider("Exercise minutes per week", 0, 500, value=30 if use_sample else 120, step=10)

    st.markdown("</div>", unsafe_allow_html=True)  # close card

    # API key input (sidebar)
    with st.sidebar:
        st.markdown("### 🔑 Anthropic API Key")
        api_key = st.text_input("Enter your API key", type="password", placeholder="sk-ant-...")
        st.markdown("*Used for Claude analysis. Leave blank to use demo data.*")
        st.markdown("---")
        st.markdown("### About")
        st.markdown("Built for the **GoodAI Longevity Hackathon** using Claude Sonnet as the AI reasoning layer.")

    if st.button("🧬 Reveal my biological age →", type="primary", use_container_width=True):
        if not age or not weight or not height:
            st.error("Please fill in your age, weight, and height at minimum.")
        else:
            bmi = calc_bmi(weight, height)
            inp = {
                "age": age, "sex": sex, "weight": weight, "height": height,
                "bmi": bmi, "sleep_hours": sleep_h, "resting_hr": resting_hr,
                "systolic": systolic, "activity_mins": activity,
                "stress": stress, "smoking": smoking,
            }
            bio_age = calc_bio_age(inp)
            worst   = detect_worst_metric(inp)

            with st.spinner("Analysing your signals… computing biological age…"):
                time.sleep(0.8)
                if api_key:
                    try:
                        import os; os.environ["ANTHROPIC_API_KEY"] = api_key
                        result = call_claude_api(inp, bio_age)
                    except Exception as e:
                        st.warning(f"Claude API failed ({e}). Using demo data.")
                        result = get_fallback_result(inp, bio_age)
                else:
                    result = get_fallback_result(inp, bio_age)

            st.session_state.inputs       = inp
            st.session_state.bio_age      = bio_age
            st.session_state.chrono_age   = age
            st.session_state.worst_metric = worst
            st.session_state.api_result   = result
            st.session_state.sim_val      = get_current_metric_val(worst, inp)
            st.session_state.step         = 2
            st.rerun()


# ═══════════════════════════════════════════════
# SCREEN 2 — BIO AGE REVEAL
# ═══════════════════════════════════════════════
elif st.session_state.step == 2:
    bio_age    = st.session_state.bio_age
    chrono_age = st.session_state.chrono_age
    inp        = st.session_state.inputs
    result     = st.session_state.api_result
    diff       = bio_age - chrono_age

    if diff > 0:
        color_cls = "older"
        reveal_text = f"Your body feels {diff} years older than you are."
    elif diff < 0:
        color_cls = "younger"
        reveal_text = f"Your body feels {abs(diff)} years younger — impressive!"
    else:
        color_cls = ""
        reveal_text = "Your biological age matches your chronological age exactly."

    st.markdown(f"""
    <div class="g-card bio-ring-wrap">
      <div class="bio-age-big {color_cls}">{bio_age}</div>
      <div class="bio-reveal-label">biological age</div>
      <div class="bio-reveal-text">{reveal_text}</div>
      <div class="bio-reveal-sub">But that's just today — let's see which habits move the needle most.</div>
    </div>
    """, unsafe_allow_html=True)

    # Metric cards
    bmi = inp["bmi"]
    bmi_cls  = "good" if bmi < 25 else ("warn" if bmi < 30 else "bad")
    bmi_lbl  = "Healthy" if bmi < 25 else ("Overweight" if bmi < 30 else "Obese")
    slp_cls  = "good" if inp["sleep_hours"] >= 7 else ("warn" if inp["sleep_hours"] >= 6 else "bad")
    slp_lbl  = "Optimal" if inp["sleep_hours"] >= 7 else ("Below optimal" if inp["sleep_hours"] >= 6 else "Critically low")
    hr_cls   = "good" if inp["resting_hr"] < 65 else ("warn" if inp["resting_hr"] < 80 else "bad")
    hr_lbl   = "Athletic" if inp["resting_hr"] < 65 else ("Normal" if inp["resting_hr"] < 80 else "Elevated")
    bp_cls   = "good" if inp["systolic"] < 120 else ("warn" if inp["systolic"] < 130 else "bad")
    bp_lbl   = "Optimal" if inp["systolic"] < 120 else ("Elevated" if inp["systolic"] < 130 else "High")

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-box {bmi_cls}">
        <div class="metric-box-label">BMI</div>
        <div class="metric-box-val">{bmi}</div>
        <div class="metric-box-sub">{bmi_lbl}</div>
      </div>
      <div class="metric-box {slp_cls}">
        <div class="metric-box-label">Sleep</div>
        <div class="metric-box-val">{inp['sleep_hours']}h</div>
        <div class="metric-box-sub">{slp_lbl}</div>
      </div>
      <div class="metric-box {hr_cls}">
        <div class="metric-box-label">Resting HR</div>
        <div class="metric-box-val">{inp['resting_hr']} bpm</div>
        <div class="metric-box-sub">{hr_lbl}</div>
      </div>
      <div class="metric-box {bp_cls}">
        <div class="metric-box-label">Blood Pressure</div>
        <div class="metric-box-val">{inp['systolic']}</div>
        <div class="metric-box-sub">{bp_lbl}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Risk banner
    risk_lvl = result.get("riskLevel", "medium")
    risk_icon = {"high": "⚠️", "medium": "📊", "low": "✅"}.get(risk_lvl, "📊")
    st.markdown(f"""
    <div class="risk-banner {risk_lvl}">
      <div style="font-size:22px;margin-top:2px;">{risk_icon}</div>
      <div class="risk-banner-text">{result['riskSummary']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    col_back, col_fwd = st.columns([1, 2])
    with col_back:
        if st.button("← Edit data", use_container_width=True):
            st.session_state.step = 1; st.rerun()
    with col_fwd:
        if st.button("Simulate habit change →", type="primary", use_container_width=True):
            st.session_state.step = 3; st.rerun()


# ═══════════════════════════════════════════════
# SCREEN 3 — TIME MACHINE
# ═══════════════════════════════════════════════
elif st.session_state.step == 3:
    inp        = st.session_state.inputs
    bio_age    = st.session_state.bio_age
    metric     = st.session_state.worst_metric
    cfg        = SIM_CONFIG[metric]

    st.markdown("""
    <div class="g-card">
      <div class="g-card-title">The time machine</div>
      <div class="g-card-sub">Adjust one habit below. Watch your projected health future update in real time.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display:inline-block;background:#EEEDFE;color:#4B3FBB;font-size:13px;
    font-weight:600;padding:6px 16px;border-radius:99px;margin-bottom:12px;">
      🎯 Your key lever: {cfg['label']}
    </div>
    """, unsafe_allow_html=True)

    current_val = get_current_metric_val(metric, inp)

    sim_val = st.slider(
        cfg["label"],
        min_value=float(cfg["min"]),
        max_value=float(cfg["max"]),
        value=float(current_val),
        step=float(cfg["step"]),
        key="sim_slider",
    )
    st.session_state.sim_val = sim_val

    sim = sim_formula(metric, sim_val)
    years_gained = sim["years"]
    risk_reduction = sim["risk"]

    # Years gained hero
    st.markdown(f"""
    <div class="years-gained-hero">
      <div class="years-number">+{years_gained:.1f}</div>
      <div class="years-label">years gained back</div>
      <div class="years-sub">If you maintain {cfg['label'].lower()} at {sim_val:.1f}{cfg['unit']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Risk reduction bar
    bar_pct = min(100, int((risk_reduction / 20) * 100))
    st.markdown(f"""
    <div class="prog-bar-wrap">
      <div class="prog-label">Heart risk ↓</div>
      <div class="prog-track"><div class="prog-fill" style="width:{bar_pct}%"></div></div>
      <div class="prog-val">-{risk_reduction}%</div>
    </div>
    <div style="font-size:12px;color:#A0A0B0;text-align:right;margin-top:4px;">10-year cardiovascular risk reduction</div>
    """, unsafe_allow_html=True)

    # Projection chart using st.line_chart
    st.markdown("<div style='margin-top:24px;font-size:13px;font-weight:600;color:#6B6A75;margin-bottom:8px;'>Biological age projection to 2040</div>", unsafe_allow_html=True)

    import pandas as pd
    years = list(range(2026, 2041, 2))
    diff  = bio_age - inp["age"]
    current_traj  = [round(bio_age + i * 0.8 + (diff * 0.15 if diff > 0 else 0), 1) for i in range(len(years))]
    improved_traj = [round(bio_age - min(years_gained, years_gained * (i / (len(years)-1))) + i * 0.5, 1) for i in range(len(years))]

    chart_df = pd.DataFrame({
        "Current trajectory": current_traj,
        "With habit change":  improved_traj,
    }, index=years)
    st.line_chart(chart_df, color=["#AFA9EC", "#1D9E75"])

    st.markdown("---")
    col_back, col_fwd = st.columns([1, 2])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 2; st.rerun()
    with col_fwd:
        if st.button("Get my action plan →", type="primary", use_container_width=True):
            st.session_state.step = 4; st.rerun()


# ═══════════════════════════════════════════════
# SCREEN 4 — COACH + STREAK DASHBOARD
# ═══════════════════════════════════════════════
elif st.session_state.step == 4:
    result  = st.session_state.api_result
    sim_val = st.session_state.sim_val
    metric  = st.session_state.worst_metric
    sim     = sim_formula(metric, sim_val) if sim_val else {"years": 2.5, "risk": 8}
    years_max = result.get("yearsGainedMax", sim["years"])

    # Share card
    st.markdown(f"""
    <div class="share-card">
      <div class="share-number">+{years_max}</div>
      <div class="share-label">years you can gain back 🎉</div>
      <div class="share-sub">Start with one micro-habit below</div>
    </div>
    """, unsafe_allow_html=True)

    # Habit cards
    st.markdown("""
    <div class="g-card">
      <div class="g-card-title">Your action plan</div>
      <div class="g-card-sub">Three highest-impact habits, ranked by life credits — months of healthy life gained.</div>
    </div>
    """, unsafe_allow_html=True)

    habits = result.get("microHabits", [])
    if "added_habits" not in st.session_state:
        st.session_state.added_habits = []

    for i, habit in enumerate(habits):
        added = i in st.session_state.added_habits
        card_cls = "habit-card added" if added else "habit-card"
        credit_cls = "credit-badge green" if added else "credit-badge"

        st.markdown(f"""
        <div class="{card_cls}">
          <div class="habit-action">{'✓ ' if added else ''}{habit['action']}</div>
          <div class="habit-impact">{habit['impact']}</div>
          <div><span class="{credit_cls}">⚡ +{habit['lifeCredits']} life credits</span></div>
        </div>
        """, unsafe_allow_html=True)

        if not added:
            if st.button(f"Add to plan", key=f"add_{i}", use_container_width=False):
                st.session_state.added_habits.append(i)
                st.rerun()

    # Streak dashboard
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="g-card">
      <div class="g-card-title">Your streak dashboard</div>
      <div class="g-card-sub">Habits you've committed to. Each one earns life credits toward your year total.</div>
    </div>
    """, unsafe_allow_html=True)

    added = st.session_state.added_habits
    total_credits = sum(habits[i]["lifeCredits"] for i in added if i < len(habits))
    streak_days   = len(added) * 3

    col_streak, col_info = st.columns([1, 2])
    with col_streak:
        st.markdown(f"""
        <div style="text-align:center;padding:20px 0;">
          <div class="streak-num">{streak_days}</div>
          <div class="streak-label">day streak 🔥</div>
        </div>
        """, unsafe_allow_html=True)
    with col_info:
        if not added:
            st.info("Add a habit above to start your streak. Your body responds after just 3 days of consistency.")
        else:
            st.success(f"**{streak_days}-day streak!** You've earned **{total_credits:.1f} life credits** — that's **{total_credits:.1f} months** of healthy life gained.")
        st.markdown(f"""
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;">
          <span style="font-size:12px;background:#E1F5EE;color:#1D9E75;padding:5px 14px;border-radius:99px;font-weight:500;">
            Life credits: {total_credits:.1f}
          </span>
          <span style="font-size:12px;background:#EEEDFE;color:#4B3FBB;padding:5px 14px;border-radius:99px;font-weight:500;">
            Total gains: {total_credits:.1f} months
          </span>
        </div>
        """, unsafe_allow_html=True)

    # Active habits list
    if added:
        st.markdown("<div style='margin-top:16px;'>", unsafe_allow_html=True)
        for i in added:
            if i < len(habits):
                h = habits[i]
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:14px;
                padding:14px 18px;background:#fff;border:1px solid rgba(75,63,187,0.12);
                border-radius:12px;margin-bottom:10px;">
                  <div style="width:28px;height:28px;border-radius:50%;background:#E1F5EE;
                  border:2px solid #1D9E75;display:flex;align-items:center;justify-content:center;
                  color:#1D9E75;font-size:14px;flex-shrink:0;">✓</div>
                  <div style="flex:1;font-size:14px;font-weight:500;">{h['action']}</div>
                  <span style="font-size:12px;font-weight:600;color:#BA7517;background:#FAEEDA;padding:3px 10px;border-radius:99px;">
                    Day {(i+1)*3} 🔥
                  </span>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Back to simulation", use_container_width=True):
            st.session_state.step = 3; st.rerun()
    with col2:
        if st.button("↺ Try new profile", use_container_width=True):
            for k in ["step","inputs","bio_age","chrono_age","worst_metric","api_result","added_habits","sim_val","_sample"]:
                if k in st.session_state: del st.session_state[k]
            init_state()
            st.rerun()
    with col3:
        share_text = f"I discovered my bio age with GoodAI! I can gain back +{years_max} years with one habit change. #AIforLongevity"
        st.code(share_text, language=None)
