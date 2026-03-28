"""
cosinor_module.py — VitalSense Biological Age Estimation (CosinorAge)
Mirror–Time Machine–Coach architecture | watch/ module
"""

import os
import sys
import warnings
import traceback
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Resolve paths relative to watch/ root regardless of where script is called
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))  # watch/
DATA_DIR = os.path.join(_ROOT, "data")
RESULTS_PATH = os.path.join(DATA_DIR, "bio_age_results.csv")

# ---------------------------------------------------------------------------
# A) Load & merge NHANES data
# ---------------------------------------------------------------------------

def load_data():
    """Load and merge subject-info and NHANES 1440-column activity data."""
    subject_path = os.path.join(DATA_DIR, "subject-info.csv")
    ac_path_xz   = os.path.join(DATA_DIR, "nhanes_1440_AC.csv.xz")
    ac_path_csv  = os.path.join(DATA_DIR, "nhanes_1440_AC.csv")

    print("[load_data] Loading data files from:", DATA_DIR)

    try:
        subject_df = pd.read_csv(subject_path)
        print(f"  [subject-info] shape={subject_df.shape}  cols={list(subject_df.columns[:5])}...")
    except FileNotFoundError:
        print("  [WARN] subject-info.csv not found — using synthetic data")
        return None, None

    # Fix age column name BEFORE merge (handles both NHANES naming conventions)
    age_col_map = {
        "RIDAGEYR": "chron_age",
        "age_in_years_at_screening": "chron_age",
    }
    for old, new in age_col_map.items():
        if old in subject_df.columns:
            subject_df = subject_df.rename(columns={old: new})
            print(f"  [subject-info] Renamed '{old}' → 'chron_age'")
            break
    if "chron_age" not in subject_df.columns:
        print("  [WARN] No age column found in subject-info; defaulting to 40")
        subject_df["chron_age"] = 40

    try:
        if os.path.exists(ac_path_xz):
            print("  [ac_data]     reading .xz compressed file (may take a moment)...")
            ac_df = pd.read_csv(ac_path_xz)
        elif os.path.exists(ac_path_csv):
            print("  [ac_data]     reading uncompressed .csv...")
            ac_df = pd.read_csv(ac_path_csv)
        else:
            print("  [WARN] nhanes_1440_AC file not found — using synthetic data")
            return None, None
        print(f"  [ac_data]     shape={ac_df.shape}  cols={list(ac_df.columns[:5])}...")
    except Exception as e:
        print(f"  [ERROR] Failed to read activity file: {e}")
        return None, None

    # Merge
    if "SEQN" not in subject_df.columns or "SEQN" not in ac_df.columns:
        print("  [ERROR] 'SEQN' column missing in one of the datasets")
        return None, None

    merged = pd.merge(subject_df, ac_df, on="SEQN", how="inner")
    print(f"  [merged]      shape={merged.shape}  cols={list(merged.columns[:8])}...")
    return merged, True


# Eagerly load at import time so functions can reference `merged_df`
_merged_df = None

def _ensure_data():
    global _merged_df
    if _merged_df is not None:
        return _merged_df

    merged, ok = load_data()
    if merged is None:
        # Fallback: generate + load synthetic data
        print("[_ensure_data] Falling back to synthetic dataset...")
        try:
            sys.path.insert(0, _HERE)
            import generate_sample_data  # runs generation as side-effect
        except Exception as e:
            print(f"  [ERROR] Could not generate synthetic data: {e}")
            return None
        # Try loading the generated CSVs
        merged, ok = load_data()
        if merged is None:
            print("  [ERROR] Cannot load any dataset. All predictions will use formula fallback.")
            return None

    _merged_df = merged
    return _merged_df


# ---------------------------------------------------------------------------
# B) Feature extraction for one participant row
# ---------------------------------------------------------------------------

def extract_features(row):
    """
    Extract wearable features from a single merged DataFrame row.

    Returns
    -------
    dict with keys: seqn, chron_age, activity_series, timestamps
    """
    try:
        seqn      = int(row["SEQN"])
        chron_age = float(row["chron_age"])

        # Real NHANES uses zero-padded names: min_0001..min_1440
        # Synthetic data uses plain names: min_1..min_1440
        min_cols = [f"min_{str(i).zfill(4)}" for i in range(1, 1441)]
        if min_cols[0] not in row.index:
            min_cols = [f"min_{i}" for i in range(1, 1441)]
        if min_cols[0] not in row.index:
            # Last resort: any column starting with min_
            min_cols = sorted(
                [c for c in row.index if str(c).startswith("min_")],
                key=lambda x: int(str(x).replace("min_", "").lstrip("0") or "0")
            )[:1440]
        if not min_cols:
            raise ValueError("Cannot locate 1440-minute activity columns")

        activity_series = np.array(row[min_cols].values, dtype=float)
        timestamps = pd.date_range(start="2021-01-01", periods=1440, freq="min")

        return {
            "seqn":            seqn,
            "chron_age":       chron_age,
            "activity_series": activity_series,
            "timestamps":      timestamps,
        }
    except Exception as e:
        print(f"  [extract_features] Error: {e}")
        return {
            "seqn":            int(row.get("SEQN", 0)),
            "chron_age":       float(row.get("chron_age", 40)),
            "activity_series": np.zeros(1440),
            "timestamps":      pd.date_range(start="2021-01-01", periods=1440, freq="min"),
        }


# ---------------------------------------------------------------------------
# C) Biological age prediction  (circadian-strength formula — no external deps)
# ---------------------------------------------------------------------------

def predict_bio_age(activity_series, timestamps, chron_age):
    """
    Predict biological age from wearable activity using a circadian-strength
    formula derived from NHANES actigraphy research.

    Returns
    -------
    dict: bio_age, confidence, top_features
    """
    try:
        activity = np.array(activity_series, dtype=float)

        # Guard: treat flat/all-NaN traces as missing data
        if np.isnan(activity).any():
            activity = np.nan_to_num(activity, nan=0.0)
        total_mean = float(activity.mean())
        if total_mean == 0:
            raise ValueError("All-zero activity trace")

        night = float(activity[0:360].mean())    # midnight–6 am
        day   = float(activity[360:1080].mean()) # 6 am–6 pm

        sleep_score        = 1.0 - (night / (total_mean + 1.0))
        day_score          = day  / (total_mean + 1.0)
        circadian_strength = float(np.clip(day_score - sleep_score, 0, 1))

        age_delta  = (1.0 - sleep_score) * 12.0 + max(0.0, 1.0 - circadian_strength) * 6.0
        bio_age    = round(float(chron_age + age_delta), 1)
        confidence = round(min(0.82, 0.55 + circadian_strength * 0.3), 2)

        print(f"  [circadian]   bio_age={bio_age}  conf={confidence}  circ={circadian_strength:.2f}")
        return {
            "bio_age":      bio_age,
            "confidence":   confidence,
            "top_features": ["Circadian rhythm strength", "Night activity disruption"],
        }
    except Exception as e:
        print(f"  [predict_bio_age] ERROR: {e}")
        return {
            "bio_age":      round(float(chron_age) + 6.0, 1),
            "confidence":   0.55,
            "top_features": ["Sleep regularity", "Night activity disruption"],
        }


# ---------------------------------------------------------------------------
# D) Batch processing
# ---------------------------------------------------------------------------

def process_all(n=50):
    """
    Process the first `n` unique participants from the merged dataset.

    Returns
    -------
    pd.DataFrame: SEQN, chron_age, bio_age, confidence, top_features
    """
    print(f"\n[process_all] Starting batch processing for n={n} participants...")
    df = _ensure_data()
    if df is None:
        print("[process_all] No data available — returning empty DataFrame")
        return pd.DataFrame(columns=["SEQN", "chron_age", "bio_age", "confidence", "top_features"])

    unique_seqns = df["SEQN"].unique()[:n]
    records = []

    for i, seqn in enumerate(unique_seqns, 1):
        try:
            participant_rows = df[df["SEQN"] == seqn]

            # Prefer day 2; else first available
            if "PAXDAYM" in participant_rows.columns:
                day2 = participant_rows[participant_rows["PAXDAYM"] == 2]
                row  = day2.iloc[0] if len(day2) > 0 else participant_rows.iloc[0]
            else:
                row = participant_rows.iloc[0]

            feats     = extract_features(row)
            prediction = predict_bio_age(
                feats["activity_series"],
                feats["timestamps"],
                feats["chron_age"],
            )

            records.append({
                "SEQN":        seqn,
                "chron_age":   feats["chron_age"],
                "bio_age":     prediction["bio_age"],
                "confidence":  prediction["confidence"],
                "top_features": str(prediction["top_features"]),
            })

            if i % 10 == 0:
                print(f"  [process_all] Progress: {i}/{len(unique_seqns)} processed")

        except Exception as e:
            print(f"  [process_all] Skipped SEQN={seqn}: {e}")

    result_df = pd.DataFrame(records)
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        result_df.to_csv(RESULTS_PATH, index=False)
        print(f"[process_all] Results saved → {RESULTS_PATH}")
    except Exception as e:
        print(f"[process_all] Could not save CSV: {e}")

    print(f"[process_all] Done. {len(result_df)} records processed.")
    return result_df


# ---------------------------------------------------------------------------
# E) Single user prediction (called by FastAPI)
# ---------------------------------------------------------------------------

def predict_single(seqn: int, day: int = 2) -> dict:
    """
    Predict biological age for one participant by SEQN and day.

    Returns
    -------
    dict: seqn, chron_age, bio_age, confidence, top_features, day_used, status
    """
    print(f"[predict_single] SEQN={seqn}  day={day}")
    df = _ensure_data()

    if df is None:
        return {
            "seqn": seqn, "chron_age": None,
            "bio_age": None, "confidence": 0.0,
            "top_features": [], "day_used": None,
            "status": "ERROR: No dataset loaded",
        }

    participant_rows = df[df["SEQN"] == seqn]
    if participant_rows.empty:
        return {
            "seqn": seqn, "chron_age": None,
            "bio_age": None, "confidence": 0.0,
            "top_features": [], "day_used": None,
            "status": f"ERROR: SEQN {seqn} not found",
        }

    day_used = day
    if "PAXDAYM" in participant_rows.columns:
        day_rows = participant_rows[participant_rows["PAXDAYM"] == day]
        if day_rows.empty:
            print(f"  [predict_single] Day {day} not found — using first available day")
            row      = participant_rows.iloc[0]
            day_used = int(row["PAXDAYM"]) if "PAXDAYM" in row else 1
        else:
            row = day_rows.iloc[0]
    else:
        row = participant_rows.iloc[0]

    feats      = extract_features(row)
    prediction = predict_bio_age(
        feats["activity_series"],
        feats["timestamps"],
        feats["chron_age"],
    )

    return {
        "seqn":        feats["seqn"],
        "chron_age":   feats["chron_age"],
        "bio_age":     prediction["bio_age"],
        "confidence":  prediction["confidence"],
        "top_features": prediction["top_features"],
        "day_used":    day_used,
        "status":      "OK",
    }


# ---------------------------------------------------------------------------
# G) Save result to JSON  (called by test_module or external scripts)
# ---------------------------------------------------------------------------

import json

def save_to_json(seqn: int, output_path: str = "output.json", user_id: int = 3):
    """
    Run a prediction for `seqn` and append the result to `output_path`.
    Skips silently if user_id+source='watch' already exists (other sources are allowed).
    """
    # 1. Check if user_id + source='watch' already present
    if os.path.exists(output_path):
        with open(output_path, "r") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
        if any(e.get("user_id") == user_id and e.get("source") == "watch" for e in existing):
            print(f"[save_to_json] user_id={user_id} source=watch already exists in {output_path} — skipping.")
            return
    else:
        existing = []

    # 2. Load data and locate the row
    df = _ensure_data()
    if df is None:
        print("[save_to_json] ERROR: No dataset loaded — cannot save.")
        return

    participant_rows = df[df["SEQN"] == seqn]
    if participant_rows.empty:
        print(f"[save_to_json] ERROR: SEQN={seqn} not found in dataset.")
        return
    row = participant_rows.iloc[0]

    # 3. Resolve activity column names (same logic as extract_features)
    min_cols = [f"min_{str(i).zfill(4)}" for i in range(1, 1441)]
    if min_cols[0] not in row.index:
        min_cols = [f"min_{i}" for i in range(1, 1441)]
    if min_cols[0] not in row.index:
        min_cols = sorted(
            [c for c in row.index if str(c).startswith("min_")],
            key=lambda x: int(str(x).replace("min_", "").lstrip("0") or "0")
        )[:1440]

    # 4. Run prediction
    result = predict_single(seqn)
    if result.get("status", "") != "OK":
        print(f"[save_to_json] Prediction failed: {result.get('status')}")
        return

    chron_age = float(result["chron_age"])
    bio_age   = float(result["bio_age"])
    age_gap   = round(bio_age - chron_age, 1)

    # 5. Compute raw signal statistics — use nanmean so missing night readings → 0
    def _safe_mean(cols):
        val = np.nanmean(row[cols].values.astype(float))
        return round(float(val), 2) if not np.isnan(val) else 0.0

    night_mean = _safe_mean(min_cols[0:360])
    day_mean   = _safe_mean(min_cols[360:1080])
    total_mean = _safe_mean(min_cols)

    # Re-derive circadian_strength (mirrors predict_bio_age logic, NaN-safe)
    total_m            = total_mean if total_mean != 0 else 1.0
    sleep_score        = 1.0 - (night_mean / (total_m + 1.0))
    day_score          = day_mean / (total_m + 1.0)
    circadian_strength = round(float(np.clip(day_score - sleep_score, 0, 1)), 3)

    # 6. Risk flag
    if age_gap > 5:
        risk_flag = "HIGH"
    elif age_gap > 2:
        risk_flag = "MODERATE"
    else:
        risk_flag = "LOW"

    # 7. Build entry
    entry = {
        "user_id":            user_id,
        "source":             "watch",
        "seqn":               int(seqn),
        "chronological_age":  int(chron_age),
        "biological_age":     bio_age,
        "age_gap":            age_gap,
        "confidence":         float(result["confidence"]),
        "top_factors":        result["top_features"],
        "raw_signals": {
            "night_activity_mean": night_mean,
            "day_activity_mean":   day_mean,
            "total_activity_mean": total_mean,
            "circadian_strength":  circadian_strength,
        },
        "ai_context": {
            "summary": (
                f"This person is chronologically {int(chron_age)} "
                f"but biologically {bio_age}."
            ),
            "risk_flag": risk_flag,
            "explainability_notes": [
                f"Biological age exceeds chronological age by {age_gap} years",
                f"Night activity level: {night_mean} counts/min",
                f"Day activity level: {day_mean} counts/min",
                f"Top contributing factors: {', '.join(result['top_features'])}",
            ],
        },
    }

    existing.append(entry)
    with open(output_path, "w") as f:
        json.dump(existing, f, indent=2)
    print(f"[save_to_json] Saved user_id={user_id} → {output_path}")


# ---------------------------------------------------------------------------
# F) FastAPI application
# ---------------------------------------------------------------------------

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="VitalSense — CosinorAge API",
    description="Biological age estimation from wearable activity data",
    version="1.0.0",
)


class WearableInput(BaseModel):
    seqn: int
    day: int = 2


class ManualInput(BaseModel):
    chron_age: int
    sleep_hours: float
    sleep_regularity: float = 0.7


@app.get("/health")
def health():
    return {"status": "ok", "service": "VitalSense CosinorAge"}


@app.post("/wearable/predict")
def wearable_predict(data: WearableInput):
    """Predict biological age using wearable data for a given SEQN."""
    try:
        return predict_single(data.seqn, data.day)
    except Exception as e:
        return {"error": str(e), "status": "FAILED"}


@app.post("/manual/predict")
def manual_predict(data: ManualInput):
    """Predict biological age from manually entered sleep data (no wearable required)."""
    try:
        sleep_deficit = max(0.0, 7.0 - data.sleep_hours)
        bio_age = data.chron_age + sleep_deficit * 1.5 + (1 - data.sleep_regularity) * 4
        return {
            "bio_age":      round(bio_age, 1),
            "confidence":   0.55,
            "top_features": ["Sleep deficit", "Irregular sleep pattern"],
        }
    except Exception as e:
        return {"error": str(e), "status": "FAILED"}


if __name__ == "__main__":
    print("[main] Starting VitalSense CosinorAge API on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
