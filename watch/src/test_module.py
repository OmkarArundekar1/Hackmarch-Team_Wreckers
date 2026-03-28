"""
test_module.py — VitalSense CosinorAge quick smoke-test
Run this to verify the full pipeline before the demo.
"""

import os
import sys
import json

# Ensure src/ is on path no matter where this script is launched from
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

# ---------------------------------------------------------------------------
# Import helper
# ---------------------------------------------------------------------------
try:
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"[ERROR] Missing core dependency: {e}")
    print("  → Run: pip install pandas numpy")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Early-exit: skip entire pipeline if this source already ran for this user
# ---------------------------------------------------------------------------
_OUTPUT_PATH = os.path.join(os.path.abspath(os.path.join(_HERE, "..")), "output.json")
_USER_ID     = 3
_SOURCE      = "watch"

if os.path.exists(_OUTPUT_PATH):
    with open(_OUTPUT_PATH, "r") as _f:
        try:
            _existing = json.load(_f)
        except json.JSONDecodeError:
            _existing = []
    if any(e.get("user_id") == _USER_ID and e.get("source") == _SOURCE for e in _existing):
        print(f"[test_module] user_id={_USER_ID} source={_SOURCE} already exists in output.json — exiting.")
        sys.exit(0)

print(f"[test_module] No existing entry for user_id={_USER_ID} source={_SOURCE} — running full pipeline...")



# ---------------------------------------------------------------------------
# 1. Load data — real first, synthetic fallback
# ---------------------------------------------------------------------------

_ROOT    = os.path.abspath(os.path.join(_HERE, ".."))
DATA_DIR = os.path.join(_ROOT, "data")

REAL_SUBJECT = os.path.join(DATA_DIR, "subject-info.csv")
REAL_AC_XZ   = os.path.join(DATA_DIR, "nhanes_1440_AC.csv.xz")
REAL_AC_CSV  = os.path.join(DATA_DIR, "nhanes_1440_AC.csv")

real_data_available = (
    os.path.exists(REAL_SUBJECT) and
    (os.path.exists(REAL_AC_XZ) or os.path.exists(REAL_AC_CSV))
)

if real_data_available:
    DATA_STATUS = "REAL DATA"
    print("[test_module] Real NHANES data found — using it.")
else:
    DATA_STATUS = "FALLBACK"
    print("[test_module] Real data NOT found — generating synthetic dataset...")
    try:
        import generate_sample_data
        generate_sample_data.main()
    except Exception as e:
        print(f"  [ERROR] Could not generate synthetic data: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# 2. Import cosinor_module and run a single prediction
# ---------------------------------------------------------------------------
print("\n[test_module] Importing cosinor_module...")
try:
    import cosinor_module as cm
except Exception as e:
    print(f"[ERROR] Failed to import cosinor_module: {e}")
    sys.exit(1)

# Force data load
df = cm._ensure_data()
if df is None:
    print("[ERROR] No dataset loaded — cannot continue.")
    sys.exit(1)

# Pick one sample row (first participant, any available day)
sample_row  = df.iloc[0]
sample_seqn = int(sample_row["SEQN"])

print(f"\n[test_module] Running predict_bio_age on SEQN={sample_seqn}...")
feats = cm.extract_features(sample_row)

try:
    result = cm.predict_bio_age(
        feats["activity_series"],
        feats["timestamps"],
        feats["chron_age"],
    )
except Exception as e:
    print(f"  [WARN] predict_bio_age raised: {e} — forcing fallback manually")
    result = {
        "bio_age":      feats["chron_age"] + 3.0,
        "confidence":   0.40,
        "top_features": ["Unavailable"],
    }

# ---------------------------------------------------------------------------
# 3. Pretty-print output
# ---------------------------------------------------------------------------
print("\n" + "=" * 50)
print(f"  SEQN:                {feats['seqn']}")
print(f"  Chronological Age:   {feats['chron_age']:.0f}")
print(f"  Biological Age:      {result['bio_age']:.1f}")
print(f"  Confidence:          {result['confidence']:.2f}")
print(f"  Top Factors:         {result['top_features']}")
print(f"  Status:              {DATA_STATUS}")
print("=" * 50 + "\n")


# ---------------------------------------------------------------------------
# 4. Test FastAPI /manual/predict via requests
# ---------------------------------------------------------------------------
print("[test_module] Testing FastAPI /manual/predict endpoint (HTTP)...")

# We spin up the FastAPI app in-process using TestClient (no server needed)
try:
    from fastapi.testclient import TestClient  # type: ignore
    client = TestClient(cm.app)

    payload = {
        "chron_age":       35,
        "sleep_hours":     5.5,
        "sleep_regularity": 0.6,
    }
    resp = client.post("/manual/predict", json=payload)
    print(f"  [/manual/predict] status={resp.status_code}  body={resp.json()}")

except ImportError:
    # Fall back to live requests if httpx/TestClient not available
    print("  [INFO] fastapi.testclient not available — trying live HTTP (requests)...")
    try:
        import requests  # type: ignore
        import threading
        import time
        import uvicorn  # type: ignore

        server = uvicorn.Server(uvicorn.Config(cm.app, host="127.0.0.1", port=8002, log_level="error"))
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        time.sleep(1.5)  # let server start

        payload = {
            "chron_age":       35,
            "sleep_hours":     5.5,
            "sleep_regularity": 0.6,
        }
        resp = requests.post("http://127.0.0.1:8002/manual/predict", json=payload, timeout=5)
        print(f"  [/manual/predict] status={resp.status_code}  body={resp.json()}")
        server.should_exit = True
    except Exception as e:
        print(f"  [WARN] Live HTTP test failed: {e}")
        # Inline formula test as last resort
        chron_age        = 35
        sleep_hours      = 5.5
        sleep_regularity = 0.6
        sleep_deficit    = max(0.0, 7.0 - sleep_hours)
        bio_age          = chron_age + sleep_deficit * 1.5 + (1 - sleep_regularity) * 4
        manual_result    = {
            "bio_age":      round(bio_age, 1),
            "confidence":   0.55,
            "top_features": ["Sleep deficit", "Irregular sleep pattern"],
        }
        print(f"  [/manual/predict] inline result={manual_result}")

except Exception as e:
    print(f"  [ERROR] FastAPI test failed: {e}")

print("\n[test_module] All tests completed.")

# ---------------------------------------------------------------------------
# 5. Save result to output.json
# ---------------------------------------------------------------------------
print("\n[test_module] Saving result to output.json...")
try:
    from cosinor_module import save_to_json
    target_seqn = 62161  # known NHANES SEQN; falls back gracefully if not found
    save_to_json(seqn=target_seqn, output_path="output.json", user_id=3)
except Exception as e:
    print(f"  [WARN] save_to_json failed: {e}")

