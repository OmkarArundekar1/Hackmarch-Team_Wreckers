"""
generate_sample_data.py — VitalSense synthetic fallback dataset generator
Generates 100 participants × 7 days of realistic circadian activity data.
"""

import os
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths (relative to watch/ root)
# ---------------------------------------------------------------------------
_HERE     = os.path.dirname(os.path.abspath(__file__))
_ROOT     = os.path.abspath(os.path.join(_HERE, ".."))  # watch/
DATA_DIR  = os.path.join(_ROOT, "data")

N_PARTICIPANTS = 100
N_DAYS         = 7
N_MINUTES      = 1440  # minutes per day

SUBJECT_CSV = os.path.join(DATA_DIR, "subject-info.csv")
AC_CSV      = os.path.join(DATA_DIR, "nhanes_1440_AC.csv")


def generate_activity(seed: int = 0, age: int = 40) -> np.ndarray:
    """
    Generate realistic 1440-min activity using circadian sine curve + noise.
    Older participants have more disrupted night-time activity.
    """
    rng = np.random.default_rng(seed)

    t      = np.linspace(0, 2 * np.pi, N_MINUTES)
    base   = 200 + 300 * np.sin(t - np.pi / 2)          # peak at noon
    noise  = rng.normal(0, 50, N_MINUTES)

    # Night suppression (midnight→6 am and 10 pm→midnight)
    night_mask = np.zeros(N_MINUTES)
    night_mask[0:360]    = -180                           # midnight → 6 am
    night_mask[1320:]    = -180                           # 10 pm → midnight

    # Older subjects: less sharp night suppression (simulates age-related disruption)
    age_factor = 1 - (age - 25) / 90.0                   # 1.0 at 25, ~0.5 at 70
    night_mask = night_mask * max(age_factor, 0.3)

    activity = np.clip(base + noise + night_mask, 0, 10_000)
    return activity.astype(np.float32)


def generate_subjects() -> pd.DataFrame:
    """Generate synthetic subject info: SEQN, RIDAGEYR."""
    rng   = np.random.default_rng(42)
    seqns = np.arange(10_000, 10_000 + N_PARTICIPANTS)
    ages  = rng.integers(25, 71, size=N_PARTICIPANTS)     # 25–70 inclusive
    return pd.DataFrame({"SEQN": seqns, "RIDAGEYR": ages})


def generate_ac_data(subjects: pd.DataFrame) -> pd.DataFrame:
    """
    Generate 1440-column activity counts for each (SEQN, PAXDAYM) pair.
    Returns a DataFrame shaped: (N_PARTICIPANTS × N_DAYS) rows × (3 + 1440) cols.
    """
    rows     = []
    min_cols = [f"min_{i}" for i in range(1, N_MINUTES + 1)]

    for _, subj in subjects.iterrows():
        seqn = int(subj["SEQN"])
        age  = int(subj["RIDAGEYR"])
        for day in range(1, N_DAYS + 1):
            seed     = seqn * 10 + day
            activity = generate_activity(seed=seed, age=age)
            row_dict = {"SEQN": seqn, "PAXDAYM": day}
            for col, val in zip(min_cols, activity):
                row_dict[col] = val
            rows.append(row_dict)

    return pd.DataFrame(rows)


def main():
    print("[generate_sample_data] Creating synthetic NHANES-style dataset...")
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. Subject info
    subjects = generate_subjects()
    subjects.to_csv(SUBJECT_CSV, index=False)
    print(f"  [subject-info]  Saved {len(subjects)} participants → {SUBJECT_CSV}")

    # 2. Activity counts
    print(f"  [ac_data]       Generating {len(subjects) * N_DAYS} rows × {N_MINUTES} minute columns...")
    ac_data = generate_ac_data(subjects)
    ac_data.to_csv(AC_CSV, index=False)
    print(f"  [ac_data]       Saved → {AC_CSV}")

    print(f"\nSample data generated: {N_PARTICIPANTS} participants, {N_DAYS} days each")
    return subjects, ac_data


if __name__ == "__main__":
    main()
